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

from .mem import WideReadMemory


class WideReadMemoryTest(TestBase):
    """Tests WideReadMemory."""

    def create_dut(self):
        return WideReadMemory(depth=32)

    def test_it(self):
        X = None
        DATA = [
            # ((write addr, write data, read_addr), (expected words)),
            ((X, 0, 10), (0, 0, 0, 0)),
            # Write eight words
            ((0, 0, 0), (0, 0, 0, 0)),
            ((1, 1, 0), (0, 0, 0, 0)),
            ((2, 2, 0), (0, 0, 0, 0)),
            ((3, 3, 0), (0, 0, 0, 0)),
            ((4, 4, 0), (0, 0, 0, 0)),
            ((5, 5, 0), (0, 0, 0, 0)),
            ((6, 6, 0), (0, 0, 0, 0)),
            ((7, 7, 0), (0, 0, 0, 0)),
            # Read eight words
            ((X, 7, 0), (0, 0, 0, 0)),
            ((X, 7, 1), (0, 1, 2, 3)),
            ((X, 7, 2), (4, 5, 6, 7)),
            # Rewrite some of that data and read it out again
            ((5, 15, 0), (0, 0, 0, 0)),
            ((X, 0, 1), (0, 0, 0, 0)),
            ((X, 0, 0), (4, 15, 6, 7)),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                write_addr, write_data, read_addr = inputs
                if write_addr is None:
                    yield self.dut.write_enable.eq(0)
                else:
                    yield self.dut.write_enable.eq(1)
                    yield self.dut.write_addr.eq(write_addr)
                    yield self.dut.write_data.eq(write_data)
                yield self.dut.read_addr.eq(read_addr)
                yield Delay(0.25)
                if expected[0] is not None:
                    self.assertEqual((yield self.dut.read_data[:32]), expected[0])
                    self.assertEqual((yield self.dut.read_data[32:64]), expected[1])
                    self.assertEqual((yield self.dut.read_data[64:96]), expected[2])
                    self.assertEqual((yield self.dut.read_data[96:]), expected[3])
                yield
        self.run_sim(process, False)
