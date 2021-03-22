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

    def test_simple(self):
        DATA = [
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

            # Restart, store eight more filters, retrieve again
            ((0, 20, 8, 0), 0),
            ((0, 24, 111, 0), 0),
            ((0, 24, 222, 0), 0),
            ((0, 24, 333, 0), 0),
            ((0, 24, 444, 0), 0),
            ((0, 24, 555, 0), 0),
            ((0, 24, 666, 0), 0),
            ((0, 24, 777, 0), 0),
            ((0, 24, 888, 0), 0),
            ((0, 110, 0, 0), 111),
            ((0, 110, 0, 0), 222),
            ((0, 110, 0, 0), 333),
            ((0, 110, 0, 0), 444),
            ((0, 110, 0, 0), 555),
            ((0, 110, 0, 0), 666),
            ((0, 110, 0, 0), 777),
            ((0, 110, 0, 0), 888),
            ((0, 110, 0, 0), 111),
            ((0, 110, 0, 0), 222),
            ((0, 110, 0, 0), 333),
            ((0, 110, 0, 0), 444),

            # Store 4 filter value words
            ((0, 20, 4, 0), 8),
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

    def test_macc_4_run_1(self):
        DATA = []

        def set_reg(reg, val):
            return ((0, reg, val, 0), 0)

        def set_out_channel_params(mult, shift, bias):
            yield set_reg(21, mult)
            yield set_reg(22, shift)
            yield set_reg(23, bias)

        def set_filter_val(val):
            return ((0, 24, val, 0), 0)

        def set_input_val(val):
            return ((0, 25, val, 0), 0)

        def macc_4_run_1(expected_result):
            return ((0, 32, 0, 0), expected_result)

        def make_op_stream():
            def nums(start, count): return range(start, start + count)
            # Output offset 999,
            yield set_reg(13, -128)
            # Input depth 8, input offset 128, batch size 16
            yield set_reg(10, 8)
            yield set_reg(12, 128)
            yield set_reg(20, 16)
            # activation min max = -128, +127,
            yield set_reg(14, -128)
            yield set_reg(15, 127)

            yield from set_out_channel_params(2000000, -5, 555000)
            yield from set_out_channel_params(18000010, -3, 100000)

            for f_vals in zip(nums(2, 16), nums(3, 16),
                              nums(4, 16), nums(5, 16)):
                yield set_filter_val(pack_vals(*f_vals))
            for i_vals in zip(nums(1, 8), nums(3, 8), nums(5, 8), nums(7, 8)):
                yield set_input_val(pack_vals(*i_vals))
            # Accumulator = 30600
            # -111 = (((30600 + 555000) * 2000000 / 2**31) / 2 ** 5) - 128
            yield macc_4_run_1(-111)
            # Accumulator = 65288
            # 45 = (((65288 + 100000) * 18000010 / 2 **31) / 2 ** 3) - 128
            yield macc_4_run_1(45)

        return self.run_ops(make_op_stream(), True)
