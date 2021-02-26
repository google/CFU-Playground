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

from nmigen import Signal, signed
from nmigen_cfu import InstructionBase, TestBase, Cfu, CfuTestBase
import unittest


class WriteInstruction(InstructionBase):
    """Writes values to CFU registers.

    Not all of these are simple writes to a register - some may have other effects.
    in0 is the register to write.
    in1 is the value to write into it.
    """
    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(32))
        self.reset_acc = Signal()

    def elab(self, m):
        with m.If(self.start):
            # Just examine lower four bits
            with m.Switch(self.in0[:4]):
                with m.Case(0):
                    m.d.sync += self.input_offset.eq(self.in1)
                with m.Case(1):
                    m.d.comb += self.reset_acc.eq(1)
            m.d.comb += self.done.eq(1)


class WriteInstructionTest(TestBase):
    def create_dut(self):
        return WriteInstruction()

    def test(self):
        DATA = [
            ((0, 0), (0, 0)),
            ((0, 5), (0, 0)),
            ((1, 123), (5, 1)),
            ((0, 0), (5, 0)),
            ((0, 0), (0, 0)),
        ]

        def process():
            for (in0, in1), (input_offset, reset_acc) in DATA:
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual((yield self.dut.input_offset), input_offset)
                self.assertEqual((yield self.dut.reset_acc), reset_acc)
                yield
        self.run_sim(process, True)


class ReadInstruction(InstructionBase):
    """Reads values to CFU registers.

    Not all of these reads are side effect free.

    in0 is the register to read.
    out0 contains the read value.
    """
    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(32))
        self.accumulator = Signal(signed(32))

    def elab(self, m):
        with m.If(self.start):
            # Just examine lower four bits of the regiser number
            with m.Switch(self.in0[:4]):
                with m.Case(0):
                    m.d.comb += self.output.eq(self.input_offset)
                with m.Case(1):
                    m.d.comb += self.output.eq(self.accumulator)
            m.d.comb += self.done.eq(1)


class ReadInstructionTest(TestBase):
    def create_dut(self):
        return ReadInstruction()

    def test(self):
        DATA = [
            (0, 666),
            (1, -888 & 0xffffffff),
        ]

        def process():
            yield self.dut.input_offset.eq(666)
            yield self.dut.accumulator.eq(-888)
            yield
            for reg_num, expected in DATA:
                yield self.dut.in0.eq(reg_num)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual((yield self.dut.output), expected)
                yield
        self.run_sim(process, True)


class MaccInstruction(InstructionBase):
    """Multiply accumulate x4

    in0 contains 4 signed input values
    in1 contains 4 signed filter values
    """
    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(32))
        self.accumulator = Signal(signed(32))
        self.reset_acc = Signal()

    def elab(self, m):
        in_vals = [Signal(signed(8), name=f"in_val_{i}") for i in range(4)]
        filter_vals = [Signal(signed(8), name=f"filter_val_{i}") for i in range(4)]
        mults = [Signal(signed(19), name=f"mult_{i}") for i in range(4)]
        for i in range(4):
            m.d.comb += [
                in_vals[i].eq(self.in0.word_select(i, 8).as_signed()),
                filter_vals[i].eq(self.in1.word_select(i, 8).as_signed()),
                mults[i].eq(
                    (in_vals[i] + self.input_offset) * filter_vals[i]),
            ]
        m.d.sync += self.done.eq(0)
        with m.If(self.start):
            m.d.sync += self.accumulator.eq(self.accumulator + sum(mults))
            # m.d.sync += self.accumulator.eq(self.accumulator + 72)
            m.d.sync += self.done.eq(1)
        with m.Elif(self.reset_acc):
            m.d.sync += self.accumulator.eq(0)


class MaccInstructionTest(TestBase):
    def create_dut(self):
        return MaccInstruction()

    def test(self):
        def x(a, b, c, d):
            return ((a & 0xff) << 24) + ((b & 0xff) << 16) + ((c & 0xff) << 8) + (d & 0xff)

        DATA = [
            # Reset everything
            (1, x(0, 0, 0, 0), x(0, 0, 0, 0), 0),
            # = 1 * 128
            (1, x(0, 0, 0, 0), x(1, 0, 0, 0), 128),
            # + 1 * 1
            (0, x(-127, 0, 0, 0), x(1, 0, 0, 0), 129),
            # + 4 * 1 * 1
            (0, x(-127, -127, -127, -127), x(1, 1, 1, 1), 133),
            # = 37 * 23
            (1, x(0, 0, 37 - 128, 0), x(0, 0, 23, 0), 37 * 23),
            # = 4 * 255 * 127
            (1, x(127, 127, 127, 127), x(127, 127, 127, 127), 4 * 255 * 127),
            # = 4 * 255 * -128
            (1, x(127, 127, 127, 127), x(-128, -128, -128, -128), 4 * 255 * -128),
            # + 4 * 255 * -128
            (0, x(127, 127, 127, 127), x(-128, -128, -128, -128), 8 * 255 * -128),
        ]

        def process():
            yield self.dut.input_offset.eq(128)
            yield
            for reset_acc, inputs, filters, acc in DATA:
                if reset_acc:
                    yield self.dut.reset_acc.eq(1)
                    yield
                    yield self.dut.reset_acc.eq(0)
                    yield
                    yield
                yield self.dut.in0.eq(inputs)
                yield self.dut.in1.eq(filters)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual((yield self.dut.accumulator), acc)
                yield
        self.run_sim(process, True)


class AvgPdti8Cfu(Cfu):
    def __init__(self):
        self.write = WriteInstruction()
        self.read = ReadInstruction()
        self.macc = MaccInstruction()
        super().__init__({
            0: self.write,
            1: self.read,
            2: self.macc,
        })

    def elab(self, m):
        super().elab(m)
        m.d.comb += [
            self.read.input_offset.eq(self.write.input_offset),
            self.read.accumulator.eq(self.macc.accumulator),
            self.macc.reset_acc.eq(self.write.reset_acc),
            self.macc.input_offset.eq(self.write.input_offset),
        ]


def make_cfu():
    return AvgPdti8Cfu()


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        DATA = [
            # Write and Read input offset
            ((0, 0, 123), None),
            ((1, 0, 0), 123),
        ]
        return self.run_ops(DATA)


if __name__ == '__main__':
    unittest.main()
