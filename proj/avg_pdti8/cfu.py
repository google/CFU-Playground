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
        self.input_offset = Signal(32)
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
        self.input_offset = Signal(32)
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


class AvgPdti8Cfu(Cfu):
    def __init__(self):
        self.write = WriteInstruction()
        self.read = ReadInstruction()
        super().__init__({
            0: self.write,
            1: self.read,
        })

    def elab(self, m):
        super().elab(m)
        m.d.comb += [
            self.read.input_offset.eq(self.write.input_offset),
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
