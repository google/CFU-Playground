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

            # Test setting and getting accumulator. Leave at zero
            ((0, 16, 59, 0), 0),
            ((0, 16, 0, 0), 59),

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

        def set_input_depth(val):
            return ((0, 10, val, 0), 0)

        def set_input_offset(val):
            return ((0, 12, val, 0), 0)

        def get_set_accum(new_val, old_val):
            return ((0, 16, new_val, 0), old_val)

        def set_output_batch_size(val):
            return ((0, 20, val, 0), 0)

        def set_filter_val(val):
            return ((0, 24, val, 0), 0)

        def set_input_val(val):
            return ((0, 25, val, 0), 0)

        def macc_4_run_1():
            return ((0, 32, 0, 0), 0)

        def make_op_stream():
            def nums(start, count): return range(start, start + count)
            yield set_input_depth(8)
            yield set_input_offset(128)
            yield set_output_batch_size(16)
            for f_vals in zip(nums(2, 16), nums(3, 16),
                              nums(4, 16), nums(5, 16)):
                yield set_filter_val(pack_vals(*f_vals))
            for i_vals in zip(nums(1, 8), nums(3, 8), nums(5, 8), nums(7, 8)):
                yield set_input_val(pack_vals(*i_vals))
            yield get_set_accum(0, 0)
            yield macc_4_run_1()
            yield get_set_accum(0, 30600)
            yield macc_4_run_1()
            yield get_set_accum(0, 65288)

        return self.run_ops(make_op_stream(), False)
