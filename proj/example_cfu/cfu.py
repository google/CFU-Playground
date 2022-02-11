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

from amaranth import *
from amaranth_cfu import InstructionBase, InstructionTestBase, simple_cfu, CfuTestBase

import unittest


class FibInstruction(InstructionBase):
    """Sample fibonacci instrucion

    This implementation uses a state machine."""

    def elab(self, m):
        s1 = Signal(32)
        s2 = Signal(32)
        count = Signal(32)
        with m.FSM():
            with m.State("WAIT"):
                m.d.sync += [
                    s1.eq(0),
                    s2.eq(1)
                ]
                with m.If(self.start):
                    with m.If(self.in0 > 46):
                        # fib > 46 is too large
                        m.d.comb += self.done.eq(1)
                    with m.Else():
                        m.next = "RUN"
                        m.d.sync += count.eq(self.in0)
            with m.State("RUN"):
                m.d.sync += [
                    count.eq(count - 1),
                    s1.eq(s2),
                    s2.eq(s1 + s2),
                ]
                with m.If(count == 0):
                    m.d.comb += self.done.eq(1)
                    m.next = "WAIT"
        m.d.comb += self.output.eq(s1)


class FibInstruction2(InstructionBase):
    """An alternative sample fibonacci instrucion

    This implementation avoids using an explicit state machine and just uses a
    counter, with 0 being the idle state."""

    def elab(self, m):
        s1 = Signal(32)
        s2 = Signal(32)
        count = Signal(32)
        with m.If(self.start):
            m.d.sync += [
                s1.eq(0),
                s2.eq(1),
                count.eq(self.in0 + 1)
            ]
        with m.If(count == 1):
            m.d.comb += self.done.eq(1)
            m.d.sync += count.eq(0)
        with m.Elif(count == 0):
            pass
        with m.Else():
            m.d.sync += [
                count.eq(count - 1),
                s1.eq(s2),
                s2.eq(s1 + s2),
            ]
        m.d.comb += self.output.eq(s1)


class SumBytesInstruction(InstructionBase):
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


class SumBytesInstructionTest(InstructionTestBase):
    def create_dut(self):
        return SumBytesInstruction()

    def test_sum_bytes(self):
        def sum_bytes(a, b):
            total = 0
            for x in range(4):
                total += (a >> (8 * x)) & 0xff
                total += (b >> (8 * x)) & 0xff
            return total
        self.verify_against_reference(
            [(0x01010101, 0x02020202), (0x12345678, 0xabcdef01)], sum_bytes)


class ReverseBytesInstruction(InstructionBase):
    """Reverses bytes in in0
    """

    def elab(self, m):
        for n in range(4):
            m.d.comb += self.output.word_select(3 - n, 8).eq(
                self.in0.word_select(n, 8))
        m.d.comb += self.done.eq(1)


class ReverseBytesInstructionTest(InstructionTestBase):
    def create_dut(self):
        return ReverseBytesInstruction()

    def test_reverse_bytes(self):
        def reverse_bytes(a):
            out = 0
            for x in range(4):
                out = (out << 8) | (a & 0xff)
                a = a >> 8
            return out
        self.verify_against_reference(
            [0, 100, 0x12345678, 0xabcdef01], reverse_bytes)


class ReverseBitsInstruction(InstructionBase):
    """Reverses bits in in0
    """

    def elab(self, m):
        for n in range(32):
            m.d.comb += self.output[31 - n].eq(self.in0[n])
        m.d.comb += self.done.eq(1)


class ReverseBitsInstructionTest(InstructionTestBase):
    def create_dut(self):
        return ReverseBitsInstruction()

    def test_reverse_bits(self):
        def reverse_bits(a):
            out = 0
            for x in range(32):
                out = (out << 1) | ((a >> x) & 1)
            return out
        self.verify_against_reference(
            [0, 100, 0x12345678, 0xabcdef01], reverse_bits)


def python_fib(n):
    s1 = 0
    s2 = 1
    for _ in range(n):
        next = s1 + s2
        s1 = s2
        s2 = next
    return s1


class FibInstructionTest(InstructionTestBase):
    def create_dut(self):
        return FibInstruction()

    def test_fib(self):
        self.verify_against_reference(range(8), python_fib)


class FibInstruction2Test(InstructionTestBase):
    def create_dut(self):
        return FibInstruction2()

    def test_fib(self):
        self.verify_against_reference(range(8), python_fib)


def make_cfu():
    return simple_cfu({
        0: SumBytesInstruction(),
        1: ReverseBytesInstruction(),
        2: ReverseBitsInstruction(),
        3: FibInstruction(),
    })


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        DATA = [
            ((0, 0x01020304, 0x0a0b0c0d), 56),
            ((1, 0x01020304, 0), 0x04030201),
            ((2, 0x01020304, 0), 0x20c04080),
            ((3, 0x05, 0), 5),
            ((3, 0x06, 0), 8),
            ((3, 46, 0), 1836311903),  # Max input
            ((3, 47, 0), 0),           # Input too large
        ]
        return self.run_ops(DATA)


if __name__ == '__main__':
    unittest.main()
