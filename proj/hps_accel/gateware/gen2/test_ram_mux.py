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

"""Tests for ram_mux.py"""

import itertools

from amaranth import unsigned
from amaranth.sim import Passive

from .conv2d_data import fetch_data
from .ram_mux import RamMux
from ..util import TestBase


class RamMuxTest(TestBase):
    """Tests RamMux class."""

    def create_dut(self):
        mux = RamMux()
        # Simulate LRAMs
        for i in range(4):
            self.m.d.sync += mux.lram_data[i].eq(mux.lram_addr[i] + i)
        return mux

    def set_inputs(self, phase, addr_in):
        yield self.dut.phase.eq(phase)
        for i in range(4):
            yield self.dut.addr_in[i].eq(addr_in[i])

    def check_outputs(self, expected):
        for i in range(4):
            self.assertEqual((yield self.dut.data_out[i]), expected[i])

    def test_it(self):
        dut = self.dut

        # Tests correct data for each phase, one cycle later
        # Checks in cases where phase changes and does not change
        DATA = [
            (0, [10, 20, 30, 40], None),
            (1, [50, 60, 70, 80], [10, 23, 32, 41]),
            (2, [90, 0, 10, 20], [51, 60, 73, 82]),
            (3, [30, 40, 50, 60], [92, 1, 10, 23]),
            (3, [70, 80, 90, 0], [33, 42, 51, 60]),
            (2, [10, 20, 30, 40], [73, 82, 91, 0]),
            (2, [50, 60, 70, 80], [12, 21, 30, 43]),
            (0, [0, 0, 0, 0], [52, 61, 70, 83]),
        ]

        def process():
            for (phase, addr_in, expected) in DATA:
                yield self.dut.phase.eq(phase)
                for i in range(4):
                    yield self.dut.addr_in[i].eq(addr_in[i])
                yield
                if expected is not None:
                    for i in range(4):
                        self.assertEqual(
                            (yield self.dut.data_out[i]), expected[i])

        self.run_sim(process, False)
