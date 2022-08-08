#!/bin/env python
# Copyright 2021 Google LLC
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

"""Tests for macc.py"""

from collections import namedtuple
import random

from amaranth import unsigned, signed
from amaranth.sim import Delay

from .macc import StandardMaccBlock
from ..util import TestBase


class MaccBlockTest(TestBase):
    """Tests MaccBlock"""

    def create_dut(self):
        # Can only use standard implementation in Amaranth simulator
        return StandardMaccBlock(4, unsigned(8), signed(8), signed(24))

    def test_basic_functions(self):
        D = namedtuple('D', ['a', 'b', 'first', 'last', 'expected'])
        DATA = [
            # Filler - before sim start
            D(0, 0, 0, 0, 0),
            D(0, 0, 0, 0, 0),
            D(0, 0, 0, 0, 0),

            # Data starts here
            D(0, 0, 0, 0, 0),

            # Multiply two sets of numbers (1 byte only)
            D(1, -2, 1, 0, 0),  # -2
            D(5, 3, 0, 1, 13),  # +15
            D(6, 26, 0, 0, 13),  # parameters should not affect output
            D(2, 17, 0, 0, 13),
            D(4, 21, 0, 0, 13),

            # Four sets of four numbers - result calculated by hand
            D(0x01020304, 0x05060708, 1, 0, 13),
            D(0x0a0b0c0d, 0xfffefdfc, 0, 0, 13),  # filter values negative
            D(0x18191a1b, 0x1113171d, 0, 0, 13),
            D(0x22232425, 0x1b1d2127, 0, 1, 6778),
            # ((6, 26, 0, 0), 13),  # parameters should not affect output
            # ((2, 17, 0, 0), 13),
            # ((4, 21, 0, 0), 6778),

            # Filler - wait for results to percolate through system
            D(0, 0, 0, 0, 0),
            D(0, 0, 0, 0, 0),
            D(0, 0, 0, 0, 0),
        ]

        def process():
            for (data, data_prev, data_prev3) in zip(DATA[3:], DATA[2:], DATA):
                # Set inputs
                yield self.dut.input_a.eq(data.a)
                yield self.dut.input_b.eq(data.b)
                yield self.dut.input_first.eq(data.first)
                yield self.dut.input_last.eq(data.last)
                yield Delay(0.1)
                # check inputs correctly passed onward
                self.assertEqual((yield self.dut.output_a), data_prev.a & 0xffff_ffff)
                self.assertEqual((yield self.dut.output_b), data_prev.b & 0xffff_ffff)
                self.assertEqual((yield self.dut.output_first), data_prev.first)
                self.assertEqual((yield self.dut.output_last), data_prev.last)
                # Check output is as expected
                self.assertEqual((yield self.dut.output_accumulator), data_prev3.expected)
                self.assertEqual((yield self.dut.output_accumulator_new), data_prev3.last)
                yield
        self.run_sim(process, False)

    def check_calculation(self, a_list, b_list):
        """Checks a given calculation:

        Args:
          a_list: first operands. Size is a multiple of 4.
          b_list: second operands. List of integers the same size as a_list.
        """
        expected_result = sum(a * b for a, b in zip(a_list, b_list))

        def to_word(x, y, z, t):
            return ((x & 0xff) |
                    ((y & 0xff) << 8) |
                    ((z & 0xff) << 16) |
                    ((t & 0xff) << 24))

        def process():
            # Send in all inputs
            num_inputs = len(a_list) // 4
            for i in range(num_inputs):
                a = to_word(*a_list[i * 4: (i + 1) * 4])
                b = to_word(*b_list[i * 4: (i + 1) * 4])
                yield self.dut.input_a.eq(a)
                yield self.dut.input_b.eq(b)
                yield self.dut.input_first.eq(i == 0)
                yield self.dut.input_last.eq(i == (num_inputs - 1))
                yield
            # wait for output to be available
            yield self.dut.input_last.eq(0)
            yield
            yield
            self.assertFalse((yield self.dut.output_accumulator_new))
            yield
            self.assertTrue((yield self.dut.output_accumulator_new))
            self.assertEqual((yield self.dut.output_accumulator), expected_result)
            yield
            self.assertFalse((yield self.dut.output_accumulator_new))

        return process()

    def check_random_calculation(self, size, seed):
        """Checks a randomly generated calculation.

        Args:
          size - number of arguments must be divisble by 4
          seed - used to seed the generator.
        """
        random.seed(seed)
        a_list = [random.randrange(0, 256) for _ in range(size)]
        b_list = [random.randrange(-128, 128) for _ in range(size)]
        return self.check_calculation(a_list, b_list)

    def test_larger_calculations(self):
        def process():
            yield from self.check_random_calculation(32, 1)
            yield from self.check_random_calculation(500, 2)
            yield from self.check_random_calculation(64, 3)
            yield from self.check_random_calculation(48, 3)

        self.run_sim(process, False)

    def test_layer_04_index_15200(self):
        # Real values from a problematic calculation in gen2.
        a_list = [
            0, 0, 0, 21, 0, 0, 61, 0, 0, 0, 2, 0, 0, 0, 0, 17, 0, 0, 0, 44, 0,
            0, 81, 0, 0, 0, 49, 0, 81, 0, 0, 39, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0,
            9, 0, 6, 10, 0, 29, 0, 0, 0, 25, 0, 0, 7, 0, 0, 0, 0, 0, 0, 3, 0, 9,
            0, 0, 0, 16, 0, 0, 56, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 14, 0, 38, 0,
            0, 77, 0, 0, 0, 32, 0, 3, 0, 0, 21, 0, 0, 0, 22, 0, 9, 42, 0, 0, 0,
            31, 0, 83, 0, 0, 48, 0, 0, 0, 16, 0, 0, 2, 0, 0, 0, 14, 0, 0, 0, 0,
            17, 0, 0, 0, 17, 0, 0, 54, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 20,
            0, 0, 58, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 42, 0, 0, 84, 0, 0,
            0, 59, 0, 69, 0, 0, 35, 0, 0, 0, 3, 0, 15, 13, 0, 0, 12, 3, 0, 35,
            33, 0, 30, 0, 0, 0, 17, 0, 0, 51, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0,
            0, 17, 0, 0, 53, 0, 0, 0, 0, 0, 0, 0, 0, 17, 0, 14, 0, 32, 0, 0, 66,
            0, 0, 0, 19, 0, 0, 0, 0, 18, 0, 0, 0, 46, 0, 37, 56, 0, 0, 0, 49, 0,
            135, 0, 0, 59
        ]
        b_list = [
            -16, 3, 2, -23, -4, 11, 31, 5, 15, 11, 36, 27, 10, 22, 30, 28, -37,
            3, 6, -22, 18, -2, 25, 9, 7, 47, 17, 10, 54, 0, 70, 28, -12, -13, 6,
            -9, -8, -7, 42, 5, -19, 13, 4, -27, -4, -12, 41, 49, -15, -13, 2, 2,
            -7, 8, 24, 39, -13, -41, 8, 16, -28, -39, -16, 28, 55, 39, 3, -4,
            -52, -60, 41, -115, -27, 125, 3, 1, 6, 43, -20, 1, 49, 33, -3, 10,
            -27, -16, -1, -71, -18, -16, 0, 16, 0, 20, -17, -12, 1, 12, 7, 27,
            -22, 15, 29, -27, -5, 33, -1, 17, 50, 6, 5, 20, -29, -24, -26, 14,
            -52, 23, 13, 3, -38, -43, 13, -6, -1, 11, -53, 13, -42, -87, -2, 12,
            17, -17, -22, -71, -7, 30, -18, -20, -117, 3, -59, 2, -31, -22, -1,
            -10, -20, -45, -13, -93, -49, -65, -21, -52, -78, -48, -10, -19, 18,
            -9, 4, 11, 4, 45, -31, -72, -27, -127, -21, -32, -12, -45, 19, -10,
            -7, -39, -18, 17, 14, 25, -28, 7, -31, -47, 10, 3, -36, -9, -46, -6,
            25, -89, 20, -11, 25, -15, -39, 4, -17, 23, -37, -59, -18, -3, -60,
            -30, -21, -49, 10, -7, 33, -20, -29, -33, 11, -2, -14, -27, -74,
            -10, -14, -40, 70, -9, -6, 14, 10, 1, -18, -84, 4, 33, -26, -31, -20,
            -49, -7, -17, -6, 14, -11, -17, 31, 1, -25, -22, 5, 3, 26, -1, -3,
            -27, 3, -24
        ]

        def process():
            yield from self.check_calculation(a_list, b_list)
        self.run_sim(process, False)
