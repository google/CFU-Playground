#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
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

#
# This file contains tests and examples
#
__package__ = 'amaranth_cfu'

import math
from amaranth import Signal
from amaranth.sim import Delay

from .cfu import simple_cfu, InstructionBase, InstructionTestBase
from .util import TestBase


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
            m.d.comb += self.output.word_select(3 - n, 8).eq(
                self.in0.word_select(n, 8))
        m.d.comb += self.done.eq(1)


class _ReverseBitsInstruction(InstructionBase):
    """Reverses bits in in0
    """

    def elab(self, m):
        for n in range(32):
            m.d.comb += self.output[31 - n].eq(self.in0[n])
        m.d.comb += self.done.eq(1)


class _SyncAddInstruction(InstructionBase):
    """Does an Add, but synchronously
    """

    def elab(self, m):
        with m.If(self.start):
            m.d.sync += self.output.eq(self.in0 + self.in1)
            m.d.sync += self.done.eq(1)
        with m.Else():
            m.d.sync += self.done.eq(0)


class _CfuTest(TestBase):
    def create_dut(self):
        return simple_cfu({
            0: _SumBytesInstruction(),
            1: _ReverseBytesInstruction(),
            2: _ReverseBitsInstruction(),
            3: _FactorialInstruction(),
            4: _SyncAddInstruction(),
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
                yield self.dut.cmd_function_id.eq(func)
                yield self.dut.cmd_in0.eq(i0)
                yield self.dut.cmd_in1.eq(i1)
                yield self.dut.cmd_valid.eq(1)
                yield self.dut.rsp_ready.eq(0)
                yield
                yield self.dut.cmd_valid.eq(0)
                yield self.dut.rsp_ready.eq(1)
                yield Delay(0.1)
                assert (yield from self.wait_response_valid()), (
                    "op{func}({i0:08X}, {i1:08X}) failed to complete")
                actual_output = (yield self.dut.rsp_out)
                assert actual_output == expected_output, (
                    f"\nHEX: op{func}(0x{i0:08X}, 0x{i1:08X}) expected: {expected_output:08X} got: {actual_output:08X}" +
                    f"\nDEC: op{func}(0x{i0}, 0x{i1}) expected: {expected_output} got: {actual_output}")
                yield
        self.run_sim(process)

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
            # Multi-cycle instruction, but always ready next cycle
            ((4, 3, 5, 1, 1), (X, 0, 1)),
            ((0, 0, 0, 0, 1), (8, 1, 0)),
            # CPU not ready
            ((4, 3, 4, 1, 0), (X, 0, 1)),
            ((0, 0, 0, 0, 0), (X, 1, 0)),
            ((0, 0, 0, 0, 0), (X, 1, 0)),
            ((0, 0, 0, 0, 1), (7, 1, 0)),
            # Fallback instruction - same cycle, CPU ready
            ((7, 0, 0, 1, 1), (X, 1, 1)),
        ]

        def process():
            for n, (inputs, expected_outputs) in enumerate(DATA):
                func, i0, i1, cmd_valid, rsp_ready = inputs
                exp_result, exp_rsp_valid, exp_cmd_ready = expected_outputs
                yield self.dut.cmd_function_id.eq(func)
                yield self.dut.cmd_in0.eq(i0)
                yield self.dut.cmd_in1.eq(i1)
                yield self.dut.cmd_valid.eq(cmd_valid)
                yield self.dut.rsp_ready.eq(rsp_ready)
                yield Delay(0.1)
                if exp_result is not None:
                    self.assertEqual((yield self.dut.rsp_out), exp_result)
                if exp_rsp_valid is not None:
                    self.assertEqual((yield self.dut.rsp_valid), exp_rsp_valid)
                if exp_cmd_ready is not None:
                    self.assertEqual((yield self.dut.cmd_ready), exp_cmd_ready)
                yield
        self.run_sim(process, False)
