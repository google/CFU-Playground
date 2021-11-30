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

"""Tests for ram_input.py"""

from nmigen import unsigned
from nmigen_cfu import TestBase

from .ram_input import PixelAddressGenerator, RoundRobin4, ValueAddressGenerator


class PixelAddressGeneratorTest(TestBase):
    """Tests PixelAddressGenerator class"""

    def create_dut(self):
        return PixelAddressGenerator()

    def test_16_deep(self):
        dut = self.dut

        def process():
            # Configure for depth=16, 32 pixels wide
            yield dut.base_addr.eq(0x400)
            yield dut.num_pixels_x.eq(32)
            yield dut.num_blocks_x.eq(1)
            yield dut.num_blocks_y.eq(32)

            # Toggle start
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)
            yield dut.next.eq(1)
            yield

            # Read with no pauses
            for i in range(256):
                self.assertEqual((yield dut.addr), i + 0x400)
                yield

        self.run_sim(process, False)

    def test_64_deep(self):
        dut = self.dut

        def check(index):
            # Calcuate expected addr as 11 pixels * 4 rows for every 10 counts
            expected = 0x400 + (index // 10 * 44) + (index % 10) * 4
            yield dut.next.eq(1)
            yield
            self.assertEqual((yield dut.addr), expected)
            yield dut.next.eq(0)

        def process():
            # Configure for depth=64, 10 pixels wide
            # 4 pixels of padding at end of row
            yield dut.base_addr.eq(0x400)
            yield dut.num_pixels_x.eq(10)
            yield dut.num_blocks_x.eq(4)
            yield dut.num_blocks_y.eq(44)

            # Toggle start
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)

            # Read 4, wait 12, read another 4
            for i in range(0, 256, 4):
                for j in range(4):
                    yield from check(i + j)
                for _ in range(12):
                    yield

        self.run_sim(process, False)


class RoundRobin4Test(TestBase):
    """Tests RoundRobin4 class."""

    def create_dut(self):
        return RoundRobin4(shape=unsigned(8))

    def test_it(self):
        dut = self.dut
        X = None
        DATA = [
            # start, mux_in, phase, mux_out
            (1, [0, 0, 0, 0], X, [X, X, X, X]),
            (0, [0, 1, 2, 3], 0, [0, 3, 2, 1]),
            (0, [10, 11, 12, 13], 1, [11, 10, 13, 12]),
            (0, [20, 21, 22, 23], 2, [22, 21, 20, 23]),
            (0, [30, 31, 32, 33], 3, [33, 32, 31, 30]),
            (0, [40, 41, 42, 43], 0, [40, 43, 42, 41]),
            (0, [50, 51, 52, 53], 1, [51, 50, 53, 52]),
            (1, [60, 62, 62, 63], X, [X, X, X, X]),
            (0, [70, 71, 72, 73], 0, [70, 73, 72, 71]),
            (0, [80, 81, 82, 83], 1, [81, 80, 83, 82]),
        ]

        def process():
            for start, mux_in, phase, expected_mux_out in DATA:
                yield dut.start.eq(start)
                for sig, data in zip(dut.mux_in, mux_in):
                    yield sig.eq(data)
                yield
                if phase is not None:
                    self.assertEqual((yield dut.phase), phase)
                for sig, expected in zip(dut.mux_out, expected_mux_out):
                    if expected is not None:
                        actual = (yield sig)
                        expected = (expected)
                        self.assertEqual((yield sig), expected)
        self.run_sim(process, False)


class ValueAddressGeneratorTest(TestBase):
    """Tests ValueAddressGenerator class."""

    def create_dut(self):
        return ValueAddressGenerator()

    def config(self, start_addr, depth, num_blocks_y):
        yield self.dut.start_addr.eq(start_addr)
        yield self.dut.depth.eq(depth)
        yield self.dut.num_blocks_y.eq(num_blocks_y)

    def check(self, start_addr, depth, num_blocks_y):
        # generate expected addresses
        expected = []
        for row in range(4):
            for col in range(4):
                for i in range(depth):
                    expected += [start_addr +
                                 row * num_blocks_y +
                                 col * depth +
                                 i] * 4
        # start generator and check output
        yield self.dut.start.eq(1)
        yield
        yield self.dut.start.eq(0)
        for e in expected:
            self.assertEqual((yield self.dut.addr_out), e)
            yield

    def test_it_does_depth_16(self):
        dut = self.dut

        def process():
            yield from self.config(200, 1, 100)
            yield from self.check(200, 1, 100)
        self.run_sim(process, False)

    def test_it_does_depth_64(self):
        dut = self.dut

        def process():
            yield from self.config(2000, 4, 1000)
            yield from self.check(2000, 4, 1000)
        self.run_sim(process, False)

    def test_it_does_depth_48(self):
        dut = self.dut

        def process():
            yield from self.config(2000, 3, 1000)
            yield from self.check(2000, 3, 1000)
        self.run_sim(process, False)
