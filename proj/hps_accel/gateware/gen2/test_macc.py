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

from nmigen import unsigned, signed
from nmigen.sim import Delay

from nmigen_cfu import TestBase

from .macc import MaccBlock


class MaccBlockTest(TestBase):
    """Tests MaccBlock"""

    def create_dut(self):
        return MaccBlock(4, unsigned(8), signed(8), signed(24))

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

    def check_random_calculation(self, size, seed):
        """Checks a randomly generated calculation.

        Args:
          size - number of arguments must be divisble by 4
          seed - used to seed the generator.
        """
        random.seed(seed)
        a_list = [random.randrange(0, 256) for _ in range(size)]
        b_list = [random.randrange(-128, 128) for _ in range(size)]
        expected_result = sum(a * b for a, b in zip(a_list, b_list))

        def to_word(x, y, z, t):
            return ((x & 0xff) |
                    ((y & 0xff) << 8) |
                    ((z & 0xff) << 16) |
                    ((t & 0xff) << 24))

        def process():
            # Send in all inputs
            num_inputs = size // 4
            for i in range(num_inputs):
                a = to_word(*a_list[i * 4: (i + 1) * 4])
                b = to_word(*b_list[i * 4: (i + 1) * 4])
                yield self.dut.input_a.eq(a)
                yield self.dut.input_b.eq(b)
                yield self.dut.input_first.eq(i == 0)
                yield self.dut.input_last.eq(i == (num_inputs - 1))
                yield
            # wait for output to be available
            yield
            yield
            yield
            self.assertEqual((yield self.dut.output_accumulator), expected_result)

        return process()

    def test_larger_calculations(self):
        def process():
            yield from self.check_random_calculation(32, 1)
            yield from self.check_random_calculation(500, 2)
            yield from self.check_random_calculation(64, 3)
            yield from self.check_random_calculation(48, 3)

        self.run_sim(process, False)
