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

from nmigen.sim import Delay

from nmigen_cfu import TestBase

from .macc import ExplicitMacc4


def pack_vals(a, b, c, d):
    return ((a & 0xff)
            + ((b & 0xff) << 8)
            + ((c & 0xff) << 16)
            + ((d & 0xff) << 24))


class ExplicitMacc4Test(TestBase):
    def create_dut(self):
        return ExplicitMacc4()

    def test(self):
        DATA = [
            ((0, 0, 0), 0),
            ((2, 1, 1), 3),
            ((2, 1, 1), 3),
            ((128, pack_vals(-128, -128, -128, -128), pack_vals(1, 1, 1, 1)), 0),
            ((128, pack_vals(-128, -127, -126, -125),
              pack_vals(10, 11, 12, 13)), 1 * 11 + 2 * 12 + 3 * 13),
            ((128, pack_vals(127, 0, 0, 0),
              pack_vals(10, 11, 12, 13)), 10 * 255 + 11 * 128 + 12 * 128 + 13 * 128),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                input_offset, input_value, filter_value = inputs
                yield self.dut.input_offset.eq(input_offset)
                yield self.dut.in0.eq(input_value)
                yield self.dut.in1.eq(filter_value)
                yield self.dut.start.eq(1)
                yield Delay(0.25)
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual(
                    (yield self.dut.output.as_signed()), expected, f"case={n}")
                yield
        self.run_sim(process, True)
