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
from amaranth_cfu import InstructionBase, TestBase, Cfu, CfuTestBase

import unittest


class StoreInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))
        self.reset_acc = Signal(1)
        self.input_offset = Signal(signed(32))

    def elab(self, m):
        with m.If(self.start):
            with m.If(self.in0 == 10):
                m.d.sync += self.max_width.eq(self.in1s)
            with m.Elif(self.in0 == 11):
                m.d.sync += self.max_height.eq(self.in1s)
            with m.Elif(self.in0 == 12):
                m.d.comb += self.reset_acc.eq(1)
            with m.Elif(self.in0 == 13):
                m.d.sync += self.input_offset.eq(self.in1s)
            m.d.comb += [
                self.done.eq(1),
                self.output.eq(1),
            ]
        return m


class StoreInstructionTest(TestBase):
    def create_dut(self):
        return StoreInstruction()

    def test_start(self):
        DATA = [
            # Only set max_width and max_height when start is 1.
            ((1, 10, 5), (1, 1, 0, 0)),
            ((1, 11, 6), (1, 1, 5, 0)),
            # Check that when start is 0, max_width and max_height remains the
            # same.
            ((0, 5, 7), (0, 0, 5, 6)),
            ((0, 1, 1), (0, 0, 5, 6)),
            ((1, 10, 7), (1, 1, 5, 6)),
            ((0, 0, 0), (0, 0, 7, 6)),
            ((1, 11, 9), (1, 1, 7, 6)),
            ((0, 2, 3), (0, 0, 7, 9)),
            ((1, 9, 19), (1, 1, 7, 9)),
            ((0, 4, 3), (0, 0, 7, 9)),
            ((1, 10, -3), (1, 1, 7, 9)),
            ((0, 1, 6), (0, 0, -3, 9)),
            ((1, 11, -4), (1, 1, -3, 9)),
            ((0, 1, 3), (0, 0, -3, -4)),
        ]

        def process():
            for n, (inputs, outputs) in enumerate(DATA):
                start, in0, in1s = inputs
                done, output, width, height = outputs
                yield self.dut.start.eq(start)
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1s)
                yield
                self.assertEqual((yield self.dut.done), done)
                self.assertEqual((yield self.dut.output), output)
                self.assertEqual((yield self.dut.max_width), width)
                self.assertEqual((yield self.dut.max_height), height)
        self.run_sim(process, False)


class ReadInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))
        self.acc = Signal(signed(32))
        self.input_offset = Signal(signed(32))

    def elab(self, m):
        m.d.comb += self.done.eq(1)
        with m.If(self.in0 == 10):
            m.d.comb += [
                self.output.eq(self.max_width),
            ]
        with m.Elif(self.in0 == 11):
            m.d.comb += [
                self.output.eq(self.max_height),
            ]
        with m.Elif(self.in0 == 12):
            m.d.comb += [
                self.output.eq(self.acc),
            ]
        with m.Elif(self.in0 == 13):
            m.d.comb += [
                self.output.eq(self.input_offset),
            ]
        return m


class ReadInstructionTest(TestBase):
    def create_dut(self):
        return ReadInstruction()

    def test_start(self):
        def process():
            width = 1234
            height = 5678
            yield self.dut.max_width.eq(width)
            yield self.dut.max_height.eq(height)
            yield self.dut.in0.eq(10)
            yield
            self.assertEqual((yield self.dut.done), 1)
            self.assertEqual((yield self.dut.output), width)
            yield self.dut.in0.eq(11)
            yield
            self.assertEqual((yield self.dut.done), 1)
            self.assertEqual((yield self.dut.output), height)
        self.run_sim(process, False)


class DoubleCompareInstruction(InstructionBase):
    """The 4 comparisons will be performed in parallel
    """

    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))

    def elab(self, m):
        m.d.comb += [
            self.output.eq((self.in0s >= 0) & (self.in0s < self.max_width) & (
                self.in1s >= 0) & (self.in1s < self.max_height)),
            self.done.eq(1)
        ]


class DoubleCompareInstructionTest(TestBase):
    def create_dut(self):
        return DoubleCompareInstruction()

    def test_double_compare(self):
        DATA = [
            ((0, 0, 2, 2), 1),
            ((4, 5, 4, 5), 0),
            ((19, 20, 10, 10), 0),
            ((11, 13, 11, 12), 0),
            ((18, 20, 19, 21), 1),
            ((-3, 1, 5, 6), 0),
            ((-2, -2, 5, 6), 0),
        ]

        def process():
            for n, (inputs, expected_output) in enumerate(DATA):
                in0, in1, width, height = inputs
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield self.dut.max_width.eq(width)
                yield self.dut.max_height.eq(height)
                yield
                self.assertEqual((yield self.dut.output), expected_output)
        self.run_sim(process, False)


class MultiplyAccumulateInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.reset_acc = Signal(1)  # input
        self.acc = Signal(signed(32))  # output
        self.input_offset = Signal(signed(32))  # input

    def elab(self, m):
        filter_val = Signal(32)
        input_val = Signal(32)
        m.d.comb += [
            filter_val.eq(self.in0s),
            input_val.eq(self.in1s),
        ]
        with m.If(self.reset_acc):
            m.d.sync += self.acc.eq(0)
        with m.If(self.start):
            m.d.sync += [
                self.acc.eq(self.acc + (filter_val *
                                        (input_val + self.input_offset))),
                self.done.eq(1),
            ]


class MultiplyAccumulateInstructionTest(TestBase):
    def create_dut(self):
        return MultiplyAccumulateInstruction()

    def test_multiply_accumulate(self):
        DATA = [
            # start, reset_acc, filter_val, input_val, input_offset
            # When start or reset_acc is set, calculations or reset happens
            # next cycle
            ((0, 1, 2, 3, 4), 0),
            ((0, 0, 2, 3, 4), 0),
            ((1, 0, 2, 3, 4), 0),
            ((1, 0, 2, 3, 4), 14),
            ((0, 1, 2, 3, 4), 28),
            ((1, 0, 2, 3, 4), 0),
            ((0, 1, 2, 3, 4), 14),
            ((0, 0, 2, 3, 4), 0),
            ((1, 0, 4, 2, 6), 0),
            ((0, 0, 4, 2, 6), 32),
            ((1, 0, 4, 2, 6), 32),
            ((1, 0, 4, 2, 6), 64),
            ((1, 0, 0, 2, 6), 96),
            ((1, 0, -12, 2, 6), 96),
            ((1, 0, -4, 2, 6), 0),
            ((1, 0, -16, 2, 6), -32),
        ]

        def process():
            for n, (inputs, expected_output) in enumerate(DATA):
                start, reset_acc, filter_val, input_val, input_offset = inputs
                yield self.dut.start.eq(start)
                yield self.dut.reset_acc.eq(reset_acc)
                yield self.dut.in0.eq(filter_val)
                yield self.dut.in1.eq(input_val)
                yield self.dut.input_offset.eq(input_offset)
                yield
                self.assertEqual((yield self.dut.acc), expected_output)
        self.run_sim(process, False)


class MultiplyAccumulateFourInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.reset_acc = Signal(1)  # input
        self.acc = Signal(signed(32))  # output
        self.input_offset = Signal(signed(32))  # input

    def elab(self, m):
        filter_val = Signal(32)
        input_val = Signal(32)

        m.d.comb += [
            filter_val.eq(self.in0),
            input_val.eq(self.in1),
        ]

        temp = [Signal(signed(32)), Signal(signed(32)),
                Signal(signed(32)), Signal(signed(32))]
        for i in range(len(temp)):
            m.d.comb += temp[i].eq((filter_val.word_select(i, 8).as_signed() * (
                input_val.word_select(i, 8).as_signed() + self.input_offset)))
        with m.If(self.reset_acc):
            m.d.sync += self.acc.eq(0)
        with m.If(self.start):
            m.d.sync += [
                self.acc.eq(
                    self.acc + (temp[0] + temp[1] + temp[2] + temp[3])),
                self.done.eq(1),
            ]


class MultiplyAccumulateFourInstructionTest(TestBase):
    def create_dut(self):
        return MultiplyAccumulateFourInstruction()

    def test_multiply_accumulate_four(self):
        DATA = [
            # start, reset_acc, filter_val, input_val, input_offset
            # When start or reset_acc is set, calculations or reset happens
            # next cycle
            ((0, 1, 2, 3, 4), 0),
            ((0, 0, 2, 3, 4), 0),
            ((1, 0, 2, 3, 4), 0),
            ((1, 0, 2, 3, 4), 14),
            ((0, 1, 2, 3, 4), 28),
            ((1, 0, 2, 3, 4), 0),
            ((0, 1, 2, 3, 4), 14),
            ((0, 0, 2, 3, 4), 0),
            ((1, 0, 4, 2, 6), 0),
            ((0, 0, 4, 2, 6), 32),
            ((1, 0, 4, 2, 6), 32),
            ((1, 0, 4, 2, 6), 64),
            ((1, 0, 0, 2, 6), 96),
            # filter_val is set to a -ve value. filter_val = -12
            ((1, 0, 0x000000F4, 0x00000002, 6), 96),
            # filter_val = -4
            ((1, 0, 0x000000FC, 0x00000002, 6), 0),
            # input_val = -2
            ((1, 0, 0x00000002, 0x000000FE, 6), -32),
            # filter_val = -3, input_val = -1
            ((1, 0, 0x000000FD, 0x000000FF, 6), -24),
            # load in 4 bytes
            ((1, 0, 0x02020202, 0x01010101, 6), -39),
            # load in 4 bytes with -ve filter_val
            ((1, 0, 0xFCFCFCFC, 0x01010101, 6), 17),
            # -95 + 5 * ( -10 + 6) = -115
            ((1, 0, 0x00000005, 0x000000F6, 6), -95),
            # -115 + (-7) * (-11 + 6) = -80
            ((1, 0, 0x000000F9, 0x000000F5, 6), -115),
            # load in lower 2 bytes
            ((1, 0, 0x0000F9F9, 0x000000F5, 6), -80),
            # load in 2 bytes with different values
            ((1, 0, 0x050000F9, 0xF60000F5, 6), -87),
            # load in all bytes with different values
            ((1, 0, 0x05F801F9, 0xF60309F3, 6), -72),
            ((1, 0, 0, 0, 6), -100),
        ]

        def process():
            for n, (inputs, expected_output) in enumerate(DATA):
                start, reset_acc, filter_val, input_val, input_offset = inputs
                yield self.dut.start.eq(start)
                yield self.dut.reset_acc.eq(reset_acc)
                yield self.dut.in0.eq(filter_val)
                yield self.dut.in1.eq(input_val)
                yield self.dut.input_offset.eq(input_offset)
                yield
                self.assertEqual((yield self.dut.acc), expected_output)
        self.run_sim(process, False)


class ProjAccel1Cfu(Cfu):
    def elab_instructions(self, m):
        m.submodules["dc"] = dc = DoubleCompareInstruction()
        m.submodules["store"] = store = StoreInstruction()
        m.submodules["read"] = read = ReadInstruction()
        m.submodules["macc"] = macc = MultiplyAccumulateInstruction()
        m.d.comb += [
            dc.max_height.eq(store.max_height),
            dc.max_width.eq(store.max_width),
            read.max_height.eq(store.max_height),
            read.max_width.eq(store.max_width),
            macc.input_offset.eq(store.input_offset),
            macc.reset_acc.eq(store.reset_acc),
            read.acc.eq(macc.acc),
            read.input_offset.eq(store.input_offset),
        ]
        return {
            0: dc,
            1: store,
            2: read,
            3: macc
        }


class ProjAccel1CfuTest(CfuTestBase):
    def create_dut(self):
        return ProjAccel1Cfu()

    def test_proj_accel1_cfu(self):
        DATA = [
            # Store the max_width and max_height values.
            ((1, 10, 6), None),
            ((1, 11, 7), None),
            # Read the max_width and max_height values.
            ((2, 10, 0), 6),
            ((2, 11, 0), 7),
            ((2, 1, 0), 0),
            ((2, 2, 0), 0),
            # Start the compare of in_x and in_y.
            ((0, 1, 1), 1),
            ((0, 5, 6), 1),
            ((0, 0, 0), 1),
            ((0, 5, 7), 0),
            ((0, 6, 7), 0),
            ((0, 10, 10), 0),
            # Test that negative values of in_x or in_y are not in range.
            ((0, -7, 7), 0),
            ((0, -10, -10), 0),
            # Store the max_width and max_height values.
            ((1, 10, 20), None),
            ((1, 11, 18), None),
            # Read the max_width and max_height values.
            ((2, 10, 0), 20),
            ((2, 11, 0), 18),
            # Start the compare of in_x and in_y.
            ((0, 10, 12), 1),
            ((0, 3, 10), 1),
            ((0, 19, 17), 1),
            ((0, 20, 20), 0),
            ((0, 24, 25), 0),
            # Store the input_offset value.
            ((1, 13, 4), None),
            # Read the input_offset value.
            ((2, 13, 0), 4),
            # Reset accumulate to 1.
            ((1, 12, 1), None),
            # Perform the macc calculation. 0 + 2 * (30 + 4) = 68
            ((3, 2, 30), 0),
            # Read the accumulate result.
            ((2, 12, 0), 68),
            # 68 + 4 * (3 + 4) = 96
            ((3, 4, 3), 0),
            ((2, 12, 0), 96),
            # 96 + (-7) * (3 + 4) = 47
            ((3, -7, 3), 0),
            ((2, 12, 0), 47),
            # Store the input_offset value.
            ((1, 13, 12), None),
            # Read the input_offset value.
            ((2, 13, 0), 12),
            # Reset accumulate to 1.
            ((1, 12, 1), None),
            # Perform the macc calculation. 0 + (-6) * (5 + 12) = 18
            ((3, -6, 5), 0),
            # Read the accumulate result. # 2**32-102 due to rsp_payload_outputs_0 being unsigned.
            # This is to test for -ve acc values
            ((2, 12, 0), 2**32 - 102),
            # 2**32 - 102 + (-1000) * (14 + 12)
            ((3, -1000, 14), 0),
            ((2, 12, 0), 4294941194),
        ]
        return self.run_ops(DATA)


def make_cfu():
    return ProjAccel1Cfu()


if __name__ == '__main__':
    unittest.main()
