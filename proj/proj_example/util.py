#!/bin/env python
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nmigen import *
from nmigen.sim import Simulator, Delay

import unittest
import math


class SimpleElaboratable(Elaboratable):
    """Simplified Elaboratable interface
    Widely, but not generally applicable. Suitable for use with
    straight-forward blocks of logic in a single domain.

    Attributes
    ----------

    m: Module
        The resulting module
    platform: 
        The platform for this elaboration

    """

    def elab(self, m):
        """Alternate elaborate interface"""
        return NotImplementedError()

    def elaborate(self, platform):
        self.m = Module()
        self.platform = platform
        self.elab(self.m)
        return self.m


class _DummySyncModule(SimpleElaboratable):
    """A module that does something arbirarty with synchronous logic

    This is used by TestBase to stop nMigen from complaining if our DUT doesn't
    contain any synchronous logic."""

    def elab(self, m):
        state = Signal(1)
        m.d.sync += state.eq(~state)


class TestBase(unittest.TestCase):
    """Base class for testing an nMigen module.

    The module can use sync, comb or both.
    """

    def setUp(self):
        self.m = Module()
        self.dut = self.create_dut()
        self.m.submodules['dut'] = self.dut
        self.m.submodules['dummy'] = _DummySyncModule()
        self.sim = Simulator(self.m)

    def create_dut(self):
        """Returns an instance of the device under test"""
        raise NotImplemented()

    def add_process(self, process):
        """Add main test process to the simulator"""
        self.sim.add_sync_process(process)

    def add_sim_clocks(self):
        """Add clocks as required by sim.
        """
        self.sim.add_clock(1, domain='sync')

    def run_sim(self, process, write_trace=False):
        self.add_process(process)
        self.add_sim_clocks()
        if write_trace:
            with self.sim.write_vcd("zz.vcd", "zz.gtkw"):
                self.sim.run()
        else:
            self.sim.run()


class InstructionBase(SimpleElaboratable):
    """Custom Instruction.

    Attributes
    ----------
    start: Signal input
        When to start executing this instruction. Set only for one cycle.
    in0: Signal(32) input
        The first operand. Only available when `start` is signalled.
    in1: Signal(32) input
        The second operand. Only available when `start` is signalled.
    done: Signal() output
        Single cycle signal to indicate that processing has finished.
    output: Signal(32) output
        The result. Must be valid when `done` is signalled.
    """

    def __init__(self):
        self.in0 = Signal(32)
        self.in1 = Signal(32)
        self.output = Signal(32)
        self.start = Signal()
        self.done = Signal()

    def signal_done(self, m):
        m.d.comb += self.done.eq(1)


class InstructionTestBase(TestBase):
    def verify_against_reference(self, inputs, reference_fn):
        """Verifies that our instruction behaves the same as a reference
        implementation.

        Parameters
        ----------
        inputs: An iterable of either integers or pairs of integers.
        reference_fn: A function that accepts either 1 or 2 integers and returns
        an integer.
        """
        def process():
            for input in inputs:
                if type(input) is tuple:
                    in0, in1 = input
                    yield self.dut.in0.eq(in0)
                    yield self.dut.in1.eq(in1)
                    expected = reference_fn(in0, in1)
                    input_hex = f"0x{in0:08X}, 0x{in1:08X}"
                else:
                    yield self.dut.in0.eq(input)
                    expected = reference_fn(input)
                    input_hex = f"0x{input:08X}"
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                actual = (yield self.dut.output)
                self.assertEqual(
                    actual, expected,
                    f"\n  HEX: instruction({input_hex}) expected: 0x{expected:08X} actual: 0x{actual:08X}" +
                    f"\n  DEC: instruction({input}) expected: {expected} actual: {actual}")
                yield
        self.run_sim(process, True)


class Cfu(SimpleElaboratable):
    """Custom function unit interface.

    Parameters
    ----------
    instructions: A map from opcode (start from 0) to instructions (instances of
                  subclasses of InstructionBase).

    Attributes
    ----------
        input               io_bus_cmd_valid,
        output              io_bus_cmd_ready,
        input      [2:0]    io_bus_cmd_payload_function_id,
        input      [31:0]   io_bus_cmd_payload_inputs_0,
        input      [31:0]   io_bus_cmd_payload_inputs_1,
        output              io_bus_rsp_valid,
        input               io_bus_rsp_ready,
        output              io_bus_rsp_payload_response_ok,
        output     [31:0]   io_bus_rsp_payload_outputs_0,
        input clk
    """

    def __init__(self, instructions):
        self.instructions = instructions
        self.cmd_valid = Signal(name='io_bus_cmd_valid')
        self.cmd_ready = Signal(name='io_bus_cmd_ready')
        self.cmd_payload_function_id = Signal(3,
                                              name='io_bus_cmd_payload_function_id')
        self.cmd_payload_inputs_0 = Signal(32,
                                           name='io_bus_cmd_payload_inputs_0')
        self.cmd_payload_inputs_1 = Signal(32,
                                           name='io_bus_cmd_payload_inputs_1')
        self.rsp_valid = Signal(
            name='io_bus_rsp_valid')
        self.rsp_ready = Signal(
            name='io_bus_rsp_ready')
        self.rsp_payload_response_ok = Signal(
            name='io_bus_rsp_payload_response_ok')
        self.rsp_payload_outputs_0 = Signal(32,
                                            name='io_bus_rsp_payload_outputs_0')
        self.clock = Signal(name='clk')
        self.ports = [
            self.cmd_valid,
            self.cmd_ready,
            self.cmd_payload_function_id,
            self.cmd_payload_inputs_0,
            self.cmd_payload_inputs_1,
            self.rsp_valid,
            self.rsp_ready,
            self.rsp_payload_response_ok,
            self.rsp_payload_outputs_0,
            self.clock,
        ]

    def elab(self, m):
        stored_function_id = Signal(3)
        current_function_id = Signal(3)
        is_cmd_transfer = self.cmd_valid & self.cmd_ready
        current_function_done = Signal()
        stored_output = Signal(32)

        instruction_outputs = Array(Signal(32) for _ in range(8))
        instruction_dones = Array(Signal() for _ in range(8))
        instruction_starts = Array(Signal() for _ in range(8))
        for (function_id, instruction) in self.instructions.items():
            m.d.comb += instruction_outputs[function_id].eq(instruction.output)
            m.d.comb += instruction_dones[function_id].eq(instruction.done)
            m.d.comb += instruction.start.eq(instruction_starts[function_id])

        def check_instruction_done():
            with m.If(current_function_done):
                m.d.comb += self.rsp_valid.eq(1)
                m.d.comb += self.rsp_payload_outputs_0.eq(
                    instruction_outputs[current_function_id])
                with m.If(self.rsp_ready):
                    m.next = "WAIT_CMD"
                with m.Else():
                    m.d.sync += stored_output.eq(
                        instruction_outputs[current_function_id])
                    m.next = "WAIT_TRANSFER"
            with m.Else():
                m.next = "WAIT_INSTRUCTION"

        with m.FSM():
            with m.State("WAIT_CMD"):
                # We're waiting for a command from the CPU.
                m.d.comb += current_function_id.eq(
                    self.cmd_payload_function_id)
                m.d.comb += current_function_done.eq(
                    instruction_dones[current_function_id])
                m.d.comb += self.cmd_ready.eq(1)
                with m.If(self.cmd_valid):
                    m.d.sync += stored_function_id.eq(
                        self.cmd_payload_function_id)
                    m.d.comb += instruction_starts[current_function_id].eq(1)
                    check_instruction_done()
            with m.State("WAIT_INSTRUCTION"):
                # An instruction is executing on the CFU. We're waiting until it
                # completes.
                m.d.comb += current_function_id.eq(stored_function_id)
                m.d.comb += current_function_done.eq(
                    instruction_dones[current_function_id])
                check_instruction_done()
            with m.State("WAIT_TRANSFER"):
                # Instruction has completed, but the CPU isn't ready to receive
                # the result.
                m.d.comb += self.rsp_valid.eq(1)
                m.d.comb += self.rsp_payload_outputs_0.eq(stored_output)
                with m.If(self.rsp_ready):
                    m.next = "WAIT_CMD"

        for (function_id, instruction) in self.instructions.items():
            m.d.comb += [
                instruction.in0.eq(self.cmd_payload_inputs_0),
                instruction.in1.eq(self.cmd_payload_inputs_1),
            ]
            m.submodules[f"fn{function_id}"] = instruction


#############################################################################
# Tests
#############################################################################


class _FactorialInstruction(InstructionBase):
    """Factorial instruction.

    Used by tests when we need an instruction that doesn't complete straight
    away.
    """

    def elab(self, m):
        counter = Signal(32)

        with m.FSM():
            with m.State("INIT"):
                with m.If(self.start):
                    with m.If(self.in0 == 0):
                        m.d.sync += self.output.eq(1)
                        m.next = "FASTANSWER"
                    with m.Elif(self.in0 > 12):
                        m.d.sync += self.output.eq(0xffffffff)
                        m.next = "FASTANSWER"
                    with m.Else():
                        m.d.sync += self.output.eq(1)
                        m.d.sync += counter.eq(self.in0)
                        m.next = "CALCULATING"
            with m.State("CALCULATING"):
                m.d.sync += self.output.eq(self.output * counter)
                m.d.sync += counter.eq(counter - 1)
                with m.If(counter == 1):
                    self.signal_done(m)
                    m.next = "INIT"
            with m.State("FASTANSWER"):
                self.signal_done(m)
                m.next = "INIT"


class _FactorialInstructionTest(InstructionTestBase):
    def create_dut(self):
        return _FactorialInstruction()

    def test_factorial(self):
        self.verify_against_reference(range(5), math.factorial)


class _SumBytesInstruction(InstructionBase):
    """Adds all bytes of in0 and in1
    """

    def elab(self, m):
        m.d.comb += self.output.eq(
            self.in0.word_select(0, 8) +
            self.in0.word_select(1, 8) +
            self.in0.word_select(2, 8) +
            self.in0.word_select(3, 8) +
            self.in1.word_select(0, 8) +
            self.in1.word_select(1, 8) +
            self.in1.word_select(2, 8) +
            self.in1.word_select(3, 8)
        )
        m.d.comb += self.done.eq(1)


class _SumBytesInstructionTest(InstructionTestBase):
    def create_dut(self):
        return _SumBytesInstruction()

    def test_sum_bytes(self):
        def sum_bytes(a, b):
            total = 0
            for x in range(4):
                total += (a >> (8 * x)) & 0xff
                total += (b >> (8 * x)) & 0xff
            return total
        self.verify_against_reference([(0x01010101, 0x02020202)], sum_bytes)


class _ReverseBytesInstruction(InstructionBase):
    """Reverses bytes in in0
    """

    def elab(self, m):
        for n in range(4):
            m.d.comb += self.output.word_select(3-n, 8).eq(
                self.in0.word_select(n, 8))
        m.d.comb += self.done.eq(1)


class _ReverseBitsInstruction(InstructionBase):
    """Reverses bits in in0
    """

    def elab(self, m):
        for n in range(32):
            m.d.comb += self.output[31-n].eq(self.in0[n])
        m.d.comb += self.done.eq(1)


class _CfuTest(TestBase):
    def create_dut(self):
        return Cfu({
            0: _SumBytesInstruction(),
            1: _ReverseBytesInstruction(),
            2: _ReverseBitsInstruction(),
            3: _FactorialInstruction(),
        })

    def wait_response_valid(self):
        cycle_limit = 20
        cycle = 0
        while (yield self.dut.rsp_valid) == 0:
            yield
            cycle += 1
            if cycle > cycle_limit:
                return False
        return True

    def test_cfu(self):
        """A high-level integration test that sends some instructions to the CFU
           then checks the results. Doesn't check things like how many cycles
           instructions take to execute, or what the behavior is if the CPU
           isn't ready. For those kinds of things, see the next test."""
        DATA = [
            # byte add
            ((0, 0, 0), 0),
            ((0, 0x01020304, 0x01020304), 20),
            ((0, 0x01010101, 0xffffffff), 1024),
            # byte swap
            ((1, 0x01020304, 0xffffffff), 0x04030201),
            ((1, 0x0102ff00, 0xffffffff), 0x00ff0201),
            # bit swap
            ((2, 0x01020304, 0xffffffff), 0x20c04080),
            ((2, 0xffffffff, 0xffffffff), 0xffffffff),
            ((2, 0x10203040, 0xffffffff), 0x020c0408),
            # Factorial
            ((3, 1, 0), 1),
            ((3, 2, 0), 2),
            ((3, 3, 0), 6),
            ((3, 4, 0), 24),
        ]

        def process():
            for n, (inputs, expected_output) in enumerate(DATA):
                func, i0, i1 = inputs
                yield self.dut.cmd_payload_function_id.eq(func)
                yield self.dut.cmd_payload_inputs_0.eq(i0)
                yield self.dut.cmd_payload_inputs_1.eq(i1)
                yield self.dut.cmd_valid.eq(1)
                yield self.dut.rsp_ready.eq(0)
                yield
                yield self.dut.cmd_valid.eq(0)
                yield self.dut.rsp_ready.eq(1)
                yield Delay(0.1)
                assert (yield from self.wait_response_valid()), (
                    "op{func}({i0:08X}, {i1:08X}) failed to complete")
                actual_output = (yield self.dut.rsp_payload_outputs_0)
                assert actual_output == expected_output, (
                    f"\nHEX: op{func}(0x{i0:08X}, 0x{i1:08X}) expected: {expected:08X} got: {actual_output:08X}" +
                    f"\nDEC: op{func}(0x{i0}, 0x{i1}) expected: {expected} got: {actual_output}")
                yield
        self.run_sim(process, True)

    def test_cfu_cycles(self):
        """A lower-level test that verifies inputs and outputs on a per-cycle
        basis and checks behaviors in cases like when the CPU isn't ready to
        receive responses."""
        # Input: (function, in0, in1, cmd_valid, rsp_ready)
        # Output: (result, rsp_valid, cmd_ready)
        X = None
        DATA = [
            # Nothing
            ((0, 0, 0, 0, 0), (X, 0, 1)),
            # Same cycle instruction, CPU not ready
            ((0, 1, 2, 1, 0), (3, 1, 1)),
            ((0, 0, 0, 0, 1), (3, 1, 0)),
            ((0, 0, 0, 0, 0), (X, 0, 1)),
            # Multi-cycle instruction, CPU ready
            ((3, 3, 0, 1, 1), (X, 0, 1)),
            ((0, 0, 0, 0, 1), (X, 0, 0)),
            ((0, 0, 0, 0, 1), (X, 0, 0)),
            ((0, 0, 0, 0, 1), (6, 1, 0)),
            # Same cycle instruction, CPU ready
            ((0, 5, 3, 1, 1), (8, 1, 1)),
            # Multi-cycle instruction, CPU not ready
            ((3, 2, 0, 1, 0), (X, 0, 1)),
            ((0, 0, 0, 0, 0), (X, 0, 0)),
            ((0, 0, 0, 0, 0), (2, 1, 0)),
            ((0, 0, 0, 0, 1), (2, 1, 0)),
        ]

        def process():
            for n, (inputs, expected_outputs) in enumerate(DATA):
                func, i0, i1, cmd_valid, rsp_ready = inputs
                exp_result, exp_rsp_valid, exp_cmd_ready = expected_outputs
                yield self.dut.cmd_payload_function_id.eq(func)
                yield self.dut.cmd_payload_inputs_0.eq(i0)
                yield self.dut.cmd_payload_inputs_1.eq(i1)
                yield self.dut.cmd_valid.eq(cmd_valid)
                yield self.dut.rsp_ready.eq(rsp_ready)
                yield Delay(0.1)
                if exp_result is not None:
                    self.assertEqual((yield self.dut.rsp_payload_outputs_0), exp_result)
                if exp_rsp_valid is not None:
                    self.assertEqual((yield self.dut.rsp_valid), exp_rsp_valid)
                if exp_cmd_ready is not None:
                    self.assertEqual((yield self.dut.cmd_ready), exp_cmd_ready)
                yield
        self.run_sim(process, True)


if __name__ == '__main__':
    unittest.main()
