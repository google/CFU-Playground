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

from nmigen_cfu import CfuTestBase
from util import pack_vals

from .mnv2_cfu import make_cfu


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        DATA = [
            # Rounding divide 7 by 2**1 == 4
            ((6, 0, 7, 1), 4),

            # Store output shift
            ((0, 22, 5, 0), 0),

            # Store filter value * 4
            ((0, 24, 666, 0), 0),
            ((0, 24, 777, 0), 0),
            ((0, 24, 888, 0), 0),
            ((0, 24, 999, 0), 0),

            # Get filter value * 5
            ((0, 110, 0, 0), 666),
            ((0, 110, 0, 0), 777),
            ((0, 110, 0, 0), 888),
            ((0, 110, 0, 0), 999),
            ((0, 110, 0, 0), 666),  # wrap around

            # Restart, store five more filters, retrieve again
            ((0, 20, 5, 0), 0),
            ((0, 24, 111, 0), 0),
            ((0, 24, 222, 0), 0),
            ((0, 24, 333, 0), 0),
            ((0, 24, 444, 0), 0),
            ((0, 24, 555, 0), 0),
            ((0, 110, 0, 0), 111),
            ((0, 110, 0, 0), 222),
            ((0, 110, 0, 0), 333),
            ((0, 110, 0, 0), 444),
            ((0, 110, 0, 0), 555),

            # Set input offset to 5, then do a macc
            ((0, 12, 5, 0), 0),
            ((0, 30, 0x01020304, 0x02040608), 6 * 2 + 7 * 4 + 8 * 6 + 9 * 8),

            # Test setting and getting accumulator. Leave at zero
            ((0, 16, 59, 0), 0),
            ((0, 16, 0, 0), 59),

            # Store 4 filter value words
            ((0, 20, 4, 0), 5),
            ((0, 24, pack_vals(1, 2, 3, 4), 0), 0),
            ((0, 24, pack_vals(3, 3, 3, 3), 0), 0),
            ((0, 24, pack_vals(-128, -128, -128, -128), 0), 0),
            ((0, 24, pack_vals(-99, 92, -37, 2), 0), 0),

            # Store 4 input value words
            ((0, 10, 4, 0), 0),
            ((0, 25, pack_vals(2, 3, 4, 5, offset=128), 0), 0),
            ((0, 25, pack_vals(2, 12, 220, 51, offset=128), 0), 0),
            ((0, 25, pack_vals(255, 255, 255, 255, offset=128), 0), 0),
            ((0, 25, pack_vals(19, 17, 103, 11, offset=128), 0), 0),

            # Set input offset to 128, then do some maccs
            ((0, 12, 128, 0), 5),
            ((0, 31, 0, 0), 1 * 2 + 2 * 3 + 3 * 4 + 4 * 5),
            ((0, 31, 0, 0), 3 * 2 + 3 * 12 + 3 * 220 + 3 * 51),
            ((0, 31, 0, 0), -128 * 255 * 4),
            ((0, 31, 0, 0), -99 * 19 + 92 * 17 + -37 * 103 + 2 * 11),

            # Get accumulator
            ((0, 16, 0, 0), (1 * 2 + 2 * 3 + 3 * 4 + 4 * 5) + (3 * 2 + 3 * 12 + 3 * 220 + 3 * 51)
             + (-128 * 255 * 4) + (-99 * 19 + 92 * 17 + -37 * 103 + 2 * 11)),
        ]
        return self.run_ops(DATA, False)

    def test_input_store(self):
        DATA = []

        def set_val(val):
            return ((0, 25, val, 0), 0)

        def get_val(val):
            return ((0, 111, 0, 0), val)

        def set_input_depth(val):
            return ((0, 10, val, 0), 0)

        def finish_read():
            return ((0, 112, 0, 0), 0)

        DATA = (
            [set_input_depth(10)] +
            [set_val(v) for v in range(100, 110)] +
            [get_val(v) for v in range(100, 110)] +
            [set_val(v) for v in range(200, 210)] +
            [get_val(v) for v in range(100, 110)] +
            [finish_read()] +
            [get_val(v) for v in range(200, 210)])
        return self.run_ops(DATA, False)
