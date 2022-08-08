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

"""Tests for sysarray.py"""

import random

from amaranth import Cat, Const, Module, signed
from amaranth.sim import Passive, Delay

from .sysarray import SystolicArray
from ..util import TestBase


def randlist(n, r):
    """Produces a list of n numbers in range r"""
    return [random.randrange(-r, r) for _ in range(n)]


def vector_multiply(a, b):
    return sum(i * j for (i, j) in zip(a, b))


def pack(values, shape):
    return Cat(Const(v, shape) for v in values)


class SystolicArrayTest(TestBase):
    """Tests the SystolicArray class."""

    def create_dut(self):
        return SystolicArray()

    def test_it_multiplies(self):
        """Test parallel multiplications."""
        # a has 4 lists of 20 values
        # b has 2 lists of 20 values
        # Multiply each list of A by each list of B through the array
        # And check the result agrees with a python calculation
        random.seed(123)
        a = [
            randlist(20, 256),
            randlist(20, 256),
            randlist(20, 256),
            randlist(20, 256)]
        b = [
            randlist(20, 128),
            randlist(20, 128)]
        expected_outputs = [vector_multiply(a_list, b_list)
                            for b_list in b for a_list in a]
        dut = self.dut

        # Get 4 values from a list and put it into an input of the
        # systolic array
        def set_input(input_index, value_index, values, inputs, shape):
            idx_from = value_index * 4
            idx_to = idx_from + 4
            if idx_from >= 0 and idx_to <= len(values[input_index]):
                data = values[input_index][idx_from:idx_to]
                yield inputs[input_index].eq(pack(data, shape))

        def set_input_a(input_index, value_index):
            yield from set_input(
                input_index, value_index, a, dut.input_a, signed(9))

        def set_input_b(input_index, value_index):
            yield from set_input(
                input_index, value_index, b, dut.input_b, signed(8))

        def process():
            new_value_found = [False for _ in range(8)]
            for i in range(15):
                # Set inputs
                yield dut.first.eq(i == 0)
                yield dut.last.eq(i == 4)
                for a_idx in range(4):
                    yield from set_input_a(a_idx, i - a_idx)
                for b_idx in range(2):
                    yield from set_input_b(b_idx, i - b_idx)
                # Tick
                yield
                # Check accumulator values as they are ready
                for acc_idx in range(8):
                    if (yield dut.accumulator_new[acc_idx]):
                        self.assertFalse(new_value_found[acc_idx],
                                         "should not get new value twice")
                        new_value_found[acc_idx] = True
                        self.assertEqual((yield dut.accumulator[acc_idx]),
                                         expected_outputs[acc_idx])
            # Check all 8 accumulators read
            self.assertTrue(all(new_value_found))

        self.run_sim(process, False)
