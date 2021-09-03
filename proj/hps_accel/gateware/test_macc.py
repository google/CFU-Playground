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


from nmigen.hdl.ast import Cat, Const, signed
from nmigen.sim import Delay

from nmigen_cfu import TestBase

from .macc import MultiplyAccumulate


class MultiplyAccumulateTest(TestBase):
    def create_dut(self):
        return MultiplyAccumulate(3)

    def test(self):
        DATA = [
            # (enable, offset, (input 0, 1, 2), (filter 0, 1, 2)), expected output
            ((1, 0, (0, 0, 0), (0, 0, 0)), 0),
            ((1, 10, (0, 1, 2), (10, 10, 10)), 0),
            ((1, 10, (0, 1, 2), (12, 12, 12)), 0),
            
            # nb: results from 2 cycles ago
            ((1, 128, (-128, 127, 0), (-128, 127, 12)), 330),
            ((0, 128, (-128, 127, 1), (127, -77, -15)), 396),  # disabled
            ((1, 128, (-128, 127, -8), (-128, 127, 23)), 396),
            ((1, 128, (33, 45, 2), (-55, -66, -77)), 33921),
            ((1, 0, (0, 0, 0), (0, 0, 0)), 35145),
            ((1, 0, (0, 0, 0), (0, 0, 0)), -30283),
            ((1, 0, (0, 0, 0), (0, 0, 0)), 0),
            ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                enable, offset, in_vals, filter_vals = inputs
                yield self.dut.enable.eq(enable)
                yield self.dut.offset.eq(offset)
                self.assertEqual((yield self.dut.operands.ready), 1, f"case={n}")
                yield self.dut.operands.payload['inputs'].eq(
                        Cat(*[Const(v, signed(8)) for v in in_vals]))
                yield self.dut.operands.payload['filters'].eq(
                        Cat(*[Const(v, signed(8)) for v in filter_vals]))
                yield self.dut.operands.valid.eq(1)
                yield self.dut.result.ready.eq(1)
                yield Delay(0.25)
                if expected is not None:
                    self.assertEqual((yield self.dut.result.valid), 1, f"case={n}")
                    self.assertEqual((yield self.dut.result.payload), expected, f"case={n}")
                yield
        self.run_sim(process, False)
