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

__package__ = 'nmigen_cfu'

from nmigen import Array, Signal, signed
from .util import SimpleElaboratable, TestBase


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
    funct7: Signal(7) input
        The funct(7) value from the instruction.
    done: Signal() output
        Single cycle signal to indicate that processing has finished.
    output: Signal(32) output
        The result. Must be valid when `done` is signalled.
    in0s: Signal(signed(32)) output
        in0 as a signed value. Use in0s rather than in0 if the input is signed.
    in1s: Signal(32) output
        in1 as a signed value. Use in1s rather than in1 if the input is signed.
    """

    def __init__(self):
        self.in0 = Signal(32)
        self.in1 = Signal(32)
        self.funct7 = Signal(7)
        self.output = Signal(32)
        self.start = Signal()
        self.done = Signal()
        self.in0s = Signal(signed(32))
        self.in1s = Signal(signed(32))

    def signal_done(self, m):
        m.d.comb += self.done.eq(1)

    def elaborate(self, platform):
        m = super().elaborate(platform)
        m.d.comb += [
            self.in0s.eq(self.in0),
            self.in1s.eq(self.in1),
        ]
        return m


class InstructionTestBase(TestBase):
    """Base test class, suitable for testing simple instructions."""

    def verify(self, data):
        """Verifies instruction given explicit lists of inputs and outputs

        Parameters
        ----------
        data: list of tuples (in0, in1, out).
        """
        def process():
            for n, (in0, in1, expected) in enumerate(data):
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                actual = (yield self.dut.output)
                self.assertEqual(
                    actual, expected,
                    f"\n  case {n}:  " +
                    f" in0={in0:08x}, in1={in1:08x}, expected={expected:08x}, actual={actual:08x}")
                yield
        self.run_sim(process, True)

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
                if isinstance(input, tuple):
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


class _FallbackInstruction(InstructionBase):
    """Executed by CFU when no instruction explicitly defined for a given function id.

    This does nothing useful, but it does ensure that the CFU does not hang on an unknown functionid.
    """

    def elab(self, m):
        m.d.comb += self.output.eq(self.in0)
        m.d.comb += self.done.eq(1)


class Cfu(SimpleElaboratable):
    """Custom function unit interface.

    Implements RR instruction format instrunctions
    We use funct3 bits of function ID to distinguish 8 separate "instructions".
    funct7 is passed to the instruction.

    Parameters
    ----------
    instructions: A map from opcode (start from 0) to instructions (instances of
                  subclasses of InstructionBase).

    Attributes
    ----------
    Attribute public names and types form the Verilog module interface:

        input               io_bus_cmd_valid,
        output              io_bus_cmd_ready,
        input      [19:0]   io_bus_cmd_payload_function_id,
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
        for i in range(8):
            if i not in self.instructions:
                self.instructions[i] = _FallbackInstruction()
        self.cmd_valid = Signal(name='io_bus_cmd_valid')
        self.cmd_ready = Signal(name='io_bus_cmd_ready')
        self.cmd_function_id = Signal(
            20, name='io_bus_cmd_payload_function_id')
        self.cmd_in0 = Signal(32, name='io_bus_cmd_payload_inputs_0')
        self.cmd_in1 = Signal(32, name='io_bus_cmd_payload_inputs_1')
        self.rsp_valid = Signal(name='io_bus_rsp_valid')
        self.rsp_ready = Signal(name='io_bus_rsp_ready')
        self.rsp_ok = Signal(name='io_bus_rsp_payload_response_ok')
        self.rsp_out = Signal(32, name='io_bus_rsp_payload_outputs_0')
        self.ports = [
            self.cmd_valid,
            self.cmd_ready,
            self.cmd_function_id,
            self.cmd_in0,
            self.cmd_in1,
            self.rsp_valid,
            self.rsp_ready,
            self.rsp_ok,
            self.rsp_out,
        ]

    def elab(self, m):
        # break out the functionid
        funct3 = Signal(3)
        funct7 = Signal(7)
        m.d.comb += [
            funct3.eq(self.cmd_function_id[:3]),
            funct7.eq(self.cmd_function_id[-7:]),
        ]
        stored_function_id = Signal(3)
        current_function_id = Signal(3)
        current_function_done = Signal()
        stored_output = Signal(32)

        # Response is always OK.
        m.d.comb += self.rsp_ok.eq(1)

        instruction_outputs = Array(Signal(32) for _ in range(8))
        instruction_dones = Array(Signal() for _ in range(8))
        instruction_starts = Array(Signal() for _ in range(8))
        for (i, instruction) in self.instructions.items():
            m.d.comb += instruction_outputs[i].eq(instruction.output)
            m.d.comb += instruction_dones[i].eq(instruction.done)
            m.d.comb += instruction.start.eq(instruction_starts[i])

        def check_instruction_done():
            with m.If(current_function_done):
                m.d.comb += self.rsp_valid.eq(1)
                m.d.comb += self.rsp_out.eq(
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
                m.d.comb += current_function_id.eq(funct3)
                m.d.comb += current_function_done.eq(
                    instruction_dones[current_function_id])
                m.d.comb += self.cmd_ready.eq(1)
                with m.If(self.cmd_valid):
                    m.d.sync += stored_function_id.eq(
                        self.cmd_function_id[:3])
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
                m.d.comb += self.rsp_out.eq(stored_output)
                with m.If(self.rsp_ready):
                    m.next = "WAIT_CMD"

        for (i, instruction) in self.instructions.items():
            m.d.comb += [
                instruction.in0.eq(self.cmd_in0),
                instruction.in1.eq(self.cmd_in1),
                instruction.funct7.eq(funct7),
            ]
            m.submodules[f"fn{i}"] = instruction


class CfuTestBase(TestBase):
    """Tests CFU ops independent of timing and handshaking."""

    def run_ops(self, data):
        """Runs the given ops through the CFU, checking results.

        Arguments:
            data: [((function_id, in0, in1), expected_output)...]
                  if expected_output is None, it is ignored.
        """
        def process():
            for n, (inputs, expected) in enumerate(data):
                function_id, in0, in1 = inputs
                # Set inputs and cmd_valid
                yield self.dut.cmd_function_id.eq(function_id)
                yield self.dut.cmd_in0.eq(in0)
                yield self.dut.cmd_in1.eq(in1)
                yield self.dut.cmd_valid.eq(1)
                yield self.dut.rsp_ready.eq(1)
                yield
                # Wait until command accepted and response available
                while not (yield self.dut.cmd_ready):
                    yield
                yield self.dut.cmd_valid.eq(0)
                while not (yield self.dut.rsp_valid):
                    yield
                yield self.dut.rsp_ready.eq(0)

                # Ensure no errors, and output as expected
                ok = (yield self.dut.rsp_ok)
                self.assertTrue(ok, f"op{n} response ok")
                if expected is not None:
                    actual = (yield self.dut.rsp_out)
                    self.assertEqual(actual, expected & 0xffff_ffff,
                                     f"op {n} output {hex(actual)} != {hex(expected & 0xffff_ffff)}")
                yield

        self.run_sim(process, True)
