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

"""Tests for mem.py"""

from nmigen.sim import Delay
from nmigen_cfu import TestBase

from .mem import SinglePortMemory


class SinglePortMemoryTest(TestBase):
    """Tests SinglePortMemory"""

    def create_dut(self):
        return SinglePortMemory(data_width=10, depth=16)

    def test_it(self):
        X = None
        DATA = [
            # (waddr, wdata, we, raddr), (rdata)
            ((0, 0, 0, 0), 0),
            # Write four words in address 8 - 11
            ((8, 111, 1, 0), 0),
            ((9, 222, 1, 0), X),
            ((10, 333, 1, 0), X),
            ((11, 444, 1, 0), X),

            # Read back the four words in a different order
            ((0, 0, 0, 11), X),
            ((0, 0, 0, 8), 444),
            ((0, 0, 0, 10), 111),
            ((0, 0, 0, 9), 333),
            ((0, 0, 0, 0), 222),
        ]

        def process():
            dut = self.dut
            for (waddr, wdata, we, raddr), rdata in DATA:
                yield dut.write_addr.eq(waddr)
                yield dut.write_data.eq(wdata)
                yield dut.write_enable.eq(we)
                yield dut.read_addr.eq(raddr)
                yield Delay(0.1)
                if rdata is not None:
                    self.assertEqual((yield dut.read_data), rdata)
                yield
        self.run_sim(process, False)
