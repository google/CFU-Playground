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

from amaranth import Mux, Signal, signed
from amaranth_cfu import InstructionBase, SimpleElaboratable, TestBase, Cfu, CfuTestBase
import unittest


class WriteInstruction(InstructionBase):
    """Writes values to CFU registers.

    Not all of these are simple writes to a register - some may have other effects.
    in0 is the register to write.
    in1 is the value to write into it.

    Interface:
        input_offset: Signal(signed(32))
            Output. Offset to apply for Macc instruction
        reset_acc: Signal()
            Output. Signal to cause accumulator to be reset
        output_offset: Signal(signed(32))
            Output. Final offset to apply to
        out_depth_set: Signal()
            Output. Indicates output channel depth value is valid
        out_depth: Signal(32)
            Output. Output channel depth
        out_mult_set: Signal()
            Output. Indicates output channel mult value is valid
        out_mult: Signal(signed(32))
            Output. Output channel multiplier
        out_bias_shift_set: Signal()
            Output. Indicates output channel bias_shfit value is valid
        out_bias_shfit: Signal(32)
            Output. Output channel bias and shift. Bias is in bits [0:17],
            shift is in bits [24:32]

    TODO: should be more modular with the ability to add small pieces of
          independently testable functionality.
    """

    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(32))
        self.reset_acc = Signal()

        self.output_offset = Signal(signed(32))

        self.out_depth_set = Signal()
        self.out_depth = Signal(32)
        self.out_mult_set = Signal()
        self.out_mult = Signal(signed(32))
        self.out_bias_shift_set = Signal()
        self.out_bias_shift = Signal(32)

    def elab(self, m):
        with m.If(self.start):
            # Just examine lower 8 bits
            with m.Switch(self.in0[:8]):
                with m.Case(0):
                    m.d.sync += self.input_offset.eq(self.in1)
                with m.Case(1):
                    m.d.comb += self.reset_acc.eq(1)
                with m.Case(0x10):
                    m.d.sync += self.output_offset.eq(self.in1)
                with m.Case(0x20):
                    m.d.comb += self.out_depth_set.eq(1)
                    m.d.comb += self.out_depth.eq(self.in1)
                with m.Case(0x21):
                    m.d.comb += self.out_mult_set.eq(1)
                    m.d.comb += self.out_mult.eq(self.in1)
                with m.Case(0x22):
                    m.d.comb += self.out_bias_shift_set.eq(1)
                    m.d.comb += self.out_bias_shift.eq(self.in1)
            m.d.comb += self.done.eq(1)


class WriteInstructionTest(TestBase):
    """Cursory test of WriteInstruction.

    Important details can only be tested in concert with other modules.
    """

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
        self.run_sim(process, False)


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
        self.run_sim(process, False)


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
        filter_vals = [
            Signal(
                signed(8),
                name=f"filter_val_{i}") for i in range(4)]
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
            return ((a & 0xff) << 24) + ((b & 0xff) << 16) + \
                ((c & 0xff) << 8) + (d & 0xff)

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
        self.run_sim(process, False)


INT32_MIN = 0x8000_0000
INT32_MAX = 0x7fff_ffff


class RoundingDividebyPOT(SimpleElaboratable):
    """Implements gemmlowp::RoundingDivideByPOT

    This divides by a power of two, rounding to the nearest whole number.
    """

    def __init__(self):
        self.x = Signal(signed(32))
        self.exponent = Signal(5)
        self.result = Signal(signed(32))

    def elab(self, m):
        # TODO: reimplement as a function that returns an expression
        mask = (1 << self.exponent) - 1
        remainder = self.x & mask
        threshold = (mask >> 1) + self.x[31]
        rounding = Mux(remainder > threshold, 1, 0)
        m.d.comb += self.result.eq((self.x >> self.exponent) + rounding)


class RoundingDividebyPOTInstruction(InstructionBase):
    def elab(self, m):
        rdbypot = RoundingDividebyPOT()
        m.submodules['RDByPOT'] = rdbypot
        m.d.comb += [
            rdbypot.x.eq(self.in0s),
            rdbypot.exponent.eq(self.in1),
            self.output.eq(rdbypot.result),
            self.done.eq(1),
        ]


class SRDHM(SimpleElaboratable):
    """Implements gemmlowp::SaturatingRoundingDoublingHighMul

    It multiplies two 32 bit numbers, then returns bits 62 to 31 of the
    64 bit result. This is 2x the high word (allowing for saturating and
    rounding).

    Note that there is a bug to investigated here. This implementation
    matches the behavior of the compiled source, however, "nudge" may be
    one of two values.

    TODO: reimplement as a pipeline
    """

    def __init__(self):
        self.a = Signal(signed(32))
        self.b = Signal(signed(32))
        self.start = Signal()
        self.result = Signal(signed(32))
        self.done = Signal()

    def elab(self, m):
        m.d.sync += self.done.eq(0)

        ab = Signal(signed(64))
        nudge = 1 << 30  # for some reason negative nudge is not used
        with m.FSM():
            with m.State("stage0"):
                with m.If(self.start):
                    with m.If((self.a == INT32_MIN) & (self.b == INT32_MIN)):
                        m.d.sync += [
                            self.result.eq(INT32_MAX),
                            self.done.eq(1)
                        ]
                    with m.Else():
                        m.d.sync += ab.eq(self.a * self.b)
                        m.next = "stage1"
            with m.State("stage1"):
                m.d.sync += [
                    self.result.eq((ab + nudge)[31:]),
                    self.done.eq(1)
                ]
                m.next = "stage0"


class SaturatingRoundingDoubleHighMulInstruction(InstructionBase):
    def elab(self, m):
        srdhm = SRDHM()
        m.submodules['srdhm'] = srdhm
        m.d.comb += [
            srdhm.a.eq(self.in0s),
            srdhm.b .eq(self.in1s),
            srdhm.start.eq(self.start),
            self.output.eq(srdhm.result),
            self.done.eq(srdhm.done),
        ]


class AvgPdti8Cfu(Cfu):
    def elab_instructions(self, m):
        m.submodules['write'] = write = WriteInstruction()
        m.submodules['read'] = read = ReadInstruction()
        m.submodules['macc'] = macc = MaccInstruction()
        m.submodules['rdpot'] = rdpot = RoundingDividebyPOTInstruction()
        m.submodules['srdhm'] = srdhm = SaturatingRoundingDoubleHighMulInstruction()
        m.d.comb += [
            read.input_offset.eq(write.input_offset),
            read.accumulator.eq(macc.accumulator),
            macc.reset_acc.eq(write.reset_acc),
            macc.input_offset.eq(write.input_offset),
        ]
        return {
            0: write,
            1: read,
            2: macc,
            6: rdpot,
            7: srdhm,
        }


def make_cfu():
    """Called by cfu_gen.py to obtain a CFU."""
    return AvgPdti8Cfu()


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        DATA = [
            # Write and Read input offset
            ((0, 0, -2), None),
            ((1, 0, 0), -2),
            # Read accumulator ==> 0
            ((1, 1, 0), 0),
            # 2 x MACC = 128 + 5*8
            ((0, 0, 128), None),
            ((2, 0x0000_0000, 0x0000_0001), None),
            ((1, 1, 0), 128),
            ((2, 0x8500_0000, 0x0800_0000), None),
            # Read accumulator
            ((1, 1, 0), 128 + 40),
            # Reset accumulator, then accumulate and read again
            ((0, 1, 0), None),
            ((2, (6 - 128) & 0xff, 10), None),
            ((1, 1, 0), 60),

            # Saturating mult - simple tests. Detailed tests are in C code.
            ((7, 0, 0), 0),
            ((7, 0x10000, 0x10000), 0x2),

            # Rounding Divide by POT instrurction - simple tests. Detailed
            # tests are in C code
            ((6, 0x12345678, 0), 0x12345678),
            ((6, 0x12345678, 4), 0x1234568),
            ((6, 0x111f, 4), 0x112),
            ((6, 0x1117, 4), 0x111),
        ]
        self.run_ops(DATA)


if __name__ == '__main__':
    unittest.main()
