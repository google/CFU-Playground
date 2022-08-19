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

from amaranth_cfu import CfuTestBase, pack_vals

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
            ((0, 25, pack_vals(2, 3, 4, 5, offset=-128), 0), 0),
            ((0, 25, pack_vals(2, 12, 220, 51, offset=-128), 0), 0),
            ((0, 25, pack_vals(255, 255, 255, 255, offset=-128), 0), 0),
            ((0, 25, pack_vals(19, 17, 103, 11, offset=-128), 0), 0),
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

    def test_2dconv(self):
        # Run a whole pixel of data
        # 16 values in input (4 words)
        # 24 values in output
        # filter words = 16 * 24 / 4 = 96
        # Calculations are at
        # https://docs.google.com/spreadsheets/d/1tQeX8expePNFisVX0Jl5_ZmKCX1QHWVMGRlPebpmpas/edit
        def set_reg(reg, val):
            return ((0, reg, val, 0), 0)

        def set_out_channel_params(bias, mult, shift):
            yield set_reg(21, mult)
            yield set_reg(22, shift)
            yield set_reg(23, bias)

        def set_filter_val(val):
            return ((0, 24, val, 0), 0)

        def set_input_val(val):
            return ((0, 25, val, 0), 0)

        def get_output(expected_result):
            return ((0, 34, 0, 0), expected_result)

        def make_op_stream():
            def nums(start, count): return range(start, start + count)
            # Output offset -50,
            yield set_reg(13, -128)
            # Input depth 4 words, input offset 50, batch size 24 outputs (6 words)
            yield set_reg(10, 4)
            yield set_reg(12, 128)
            yield set_reg(20, 24)
            # activation min max = -128, +127,
            yield set_reg(14, -128)
            yield set_reg(15, 127)

            for _ in range(6):
                yield from set_out_channel_params(30_000, 31_000_000, -3)
                yield from set_out_channel_params(50_000, 50_000_000, -6)
                yield from set_out_channel_params(75_000, 56_000_000, -4)
                yield from set_out_channel_params(100_000, 50_000_000, -5)

            for f_vals in zip(nums(-17, 96), nums(3, 96),
                              nums(-50, 96), nums(5, 96)):
                yield set_filter_val(pack_vals(*f_vals))
            for i_vals in zip(nums(1, 4), nums(3, 4), nums(5, 4), nums(7, 4)):
                yield set_input_val(pack_vals(*i_vals))

            # Start calculation
            yield set_reg(33, 0)
            yield get_output(pack_vals(-125, -117, -24, -57))
            yield get_output(pack_vals(-63, -105, 32, -32))
            yield get_output(pack_vals(-1, -92, 88, -7))
            yield get_output(pack_vals(60, -80, 127, 17))
            yield get_output(pack_vals(122, -67, 127, 42))
            yield get_output(pack_vals(127, -55, 127, 67))

        return self.run_ops(make_op_stream(), False)
