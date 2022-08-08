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

from amaranth import Array, Signal, signed
from amaranth.hdl.dsl import Module
from .util import SimpleElaboratable, TestBase
from amaranth.hdl import ResetSignal


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

    def verify(self, data, trace=False):
        """Verifies instruction given explicit lists of inputs and outputs

        Parameters
        ----------
        data: list of 3-tuples (in0, in1, out) or 4-tuples (funct7, in0, in1, out)
        """
        def process():
            for n, values in enumerate(data):
                funct7, in0, in1, expected = values if len(
                    values) == 4 else (0,) + values
                yield self.dut.funct7.eq(funct7)
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                actual = (yield self.dut.output)
                if expected is not None:
                    self.assertEqual(
                        actual, expected,
                        f"\n  case {n}:   " +
                        f"in0={in0:08x}, in1={in1:08x}, " +
                        f"expected={expected:08x}, actual={actual:08x}")
                yield
        self.run_sim(process, trace)

    def verify_against_reference(self, inputs, reference_fn, trace=False):
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
        self.run_sim(process, trace)


class _FallbackInstruction(InstructionBase):
    """Executed by CFU when no instruction explicitly defined for a given function id.

    This does nothing useful, but it does ensure that the CFU does not hang on an unknown functionid.
    """

    def elab(self, m):
        m.d.comb += self.output.eq(self.in0)
        m.d.comb += self.done.eq(1)


class CfuBase(SimpleElaboratable):
    """Custom function unit interface.

    Implements RR instruction format instrunctions
    We use funct3 bits of function ID to distinguish 8 separate "instructions".
    funct7 is passed to the instruction.

    This class contains interface only, without any implementation.

    Attributes
    ----------
    Attribute public names and types form the Verilog module interface:

        input               cmd_valid,
        output              cmd_ready,
        input      [9:0]    cmd_payload_function_id,
        input      [31:0]   cmd_payload_inputs_0,
        input      [31:0]   cmd_payload_inputs_1,
        output              rsp_valid,
        input               rsp_ready,
        output     [31:0]   rsp_payload_outputs_0,
        input               clk
        input               reset
        output    [13:0]    port0_addr,
        output    [13:0]    port1_addr,
        output    [13:0]    port2_addr,
        output    [13:0]    port3_addr,
        input     [31:0]    port0_din,
        input     [31:0]    port1_din,
        input     [31:0]    port2_din,
        input     [31:0]    port3_din,
    """

    def __init__(self):
        self.cmd_valid = Signal(name='cmd_valid')
        self.cmd_ready = Signal(name='cmd_ready')
        self.cmd_function_id = Signal(
            10, name='cmd_payload_function_id')
        self.cmd_in0 = Signal(32, name='cmd_payload_inputs_0')
        self.cmd_in1 = Signal(32, name='cmd_payload_inputs_1')
        self.rsp_valid = Signal(name='rsp_valid')
        self.rsp_ready = Signal(name='rsp_ready')
        self.rsp_out = Signal(32, name='rsp_payload_outputs_0')
        self.reset = Signal(name='reset')
        self.lram_addr = [Signal(32, name=f'port{i}_addr') for i in range(4)]
        self.lram_data = [Signal(32, name=f'port{i}_din') for i in range(4)]
        self.ports = [
            self.cmd_valid,
            self.cmd_ready,
            self.cmd_function_id,
            self.cmd_in0,
            self.cmd_in1,
            self.rsp_valid,
            self.rsp_ready,
            self.rsp_out,
            self.reset,
        ] + self.lram_addr + self.lram_data


class Cfu(CfuBase):
    """Standard Custom function unit implementation.

    See CfuBase for attributes.
    """

    def elab_instructions(self, m):
        """Make instructions this CFU will execute.

        Returns:
          A dictionary with keys in range(8) containing the CFU's instructions.
        """
        return dict()

    def __build_instructions(self, m):
        """Builds the list of eight instructions"""
        instruction_dict = self.elab_instructions(m)

        assert all(k in range(8) for k in instruction_dict.keys()), \
            "Instruction IDs must be integers from 0 to 7"

        # Add fallback instructions where needed
        for i in range(8):
            if i not in instruction_dict:
                m.submodules[f"fallback{i}"] = fb = _FallbackInstruction()
                instruction_dict[i] = fb

        return list(instruction_dict[i] for i in range(8))

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

        instructions = self.__build_instructions(m)
        instruction_outputs = Array(Signal(32) for _ in range(8))
        instruction_dones = Array(Signal() for _ in range(8))
        instruction_starts = Array(Signal() for _ in range(8))
        for (i, instruction) in enumerate(instructions):
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

        for instruction in instructions:
            m.d.comb += [
                instruction.in0.eq(self.cmd_in0),
                instruction.in1.eq(self.cmd_in1),
                instruction.funct7.eq(funct7),
            ]

        # tie "reset" and "rst" together (issue #110)
        rst = ResetSignal('sync')
        m.d.comb += rst.eq(self.reset)


class CfuTestBase(TestBase):
    """Tests CFU ops independent of timing and handshaking."""

    def _unpack(self, inputs):
        return inputs if len(inputs) == 4 else (
            inputs[0], 0, inputs[1], inputs[2])

    def run_ops(self, data, write_trace=False):
        """Runs the given ops through the CFU, checking results.

        Arguments:
            data: [(input, expected_output)...]
                  if expected_output is None, it is ignored.
                  input is either a 3-tuple (function_id, in0, in1) or
                  a 4-tuple (function_id, funct7, in0, in1)
        """
        def process():
            for n, (inputs, expected) in enumerate(data):
                function_id, funct7, in0, in1 = self._unpack(inputs)
                # Set inputs and cmd_valid
                yield self.dut.cmd_function_id.eq((funct7 << 3) | function_id)
                yield self.dut.cmd_in0.eq(in0 & 0xffff_ffff)
                yield self.dut.cmd_in1.eq(in1 & 0xffff_ffff)
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
                if expected is not None:
                    actual = (yield self.dut.rsp_out)
                    self.assertEqual(actual, expected & 0xffff_ffff,
                                     f"output {hex(actual)} != {hex(expected & 0xffff_ffff)} ::: " +
                                     f"function_id={function_id}, funct7={funct7}, " +
                                     f" in0={in0} {hex(in0)}, in1={in1} {hex(in1)} (n={n})")
                yield

        self.run_sim(process, write_trace)
