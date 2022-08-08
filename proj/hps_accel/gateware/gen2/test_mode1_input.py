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

"""Tests for mode1_input.py"""

import itertools

from amaranth import Memory, unsigned
from amaranth.sim import Passive, Delay, Settle

from .conv2d_data import fetch_data
from .mode1_input import (
    Mode1InputFetcher,
    PixelAddressGenerator,
    PixelAddressRepeater,
    ValueAddressGenerator)
from .ram_mux import RamMux
from ..util import TestBase


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


class PixelAddressRepeaterTest(TestBase):
    """Tests PixelAddressRepeater class."""

    def create_dut(self):
        return PixelAddressRepeater()

    def test_it(self):
        dut = self.dut

        def addr_generator():
            yield Passive()
            n = 0
            dut.gen_addr.eq(n)
            while True:
                if (yield dut.gen_next):
                    n += 1
                    yield dut.gen_addr.eq(n)
                yield
        self.add_process(addr_generator)

        def process():
            yield dut.repeats.eq(8)
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)
            yield
            for i in (range(0, 256, 4)):
                for _ in range(8):
                    for j in range(4):
                        yield dut.next.eq(1)
                        yield
                        yield dut.next.eq(0)
                        self.assertEqual((yield dut.addr), i + j)
                    for _ in range(12):
                        yield

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


class Mode1InputFetcherTest(TestBase):
    """Tests Mode1InputFetcher class."""

    BASE_ADDR = 0x120

    def create_dut(self):
        fetcher = Mode1InputFetcher()
        # Connect RAM Mux with simulated LRAMs
        self.m.submodules["ram_mux"] = ram_mux = RamMux()
        self.m.d.comb += ram_mux.phase.eq(fetcher.ram_mux_phase)
        for i in range(4):
            padding = [0] * (self.BASE_ADDR // 16)
            init = (padding + self.data.input_data[i::4])[:1024]
            mem = Memory(width=32, depth=1024, init=init)
            rp = mem.read_port(transparent=False)
            self.m.d.comb += [
                ram_mux.lram_data[i].eq(rp.data),
                rp.addr.eq(ram_mux.lram_addr[i]),
                rp.en.eq(1),
                ram_mux.addr_in[i].eq(fetcher.ram_mux_addr[i]),
                fetcher.ram_mux_data[i].eq(ram_mux.data_out[i]),
            ]
            self.m.submodules[f"rp{i}"] = rp
        return fetcher

    def setUp(self):
        self.data = fetch_data('sample_conv_05')
        super().setUp()

    def pixel_input_values(self, index):
        # Get values for a given pixel number
        # TODO: allow for stride != 1, num_repeats != 8

        # We repeat each pixel 8 times, in groups of 4
        pixel = (index // (8 * 4)) * 4 + index % 4
        data = self.data
        in_x_dim = data.input_dims[2]
        out_x_dim = data.output_dims[2]
        word_depth = data.input_dims[3] // 4
        pixel_y, pixel_x = pixel // out_x_dim, pixel % out_x_dim
        result = []
        for row in range(4):
            row_start_addr = (
                (pixel_y + row) * in_x_dim + pixel_x) * word_depth
            result += data.input_data[row_start_addr:
                                      row_start_addr + word_depth * 4]
        return result

    def test_it(self):
        dut = self.dut
        data = self.data

        captured_outputs = [[] for _ in range(4)]

        def process():
            # Configure the dut to match the input
            depth = data.input_dims[3]
            in_x_dim = data.input_dims[2]
            out_x_dim = data.output_dims[2]

            yield dut.base_addr.eq(self.BASE_ADDR)
            yield dut.num_pixels_x.eq(out_x_dim)
            yield dut.pixel_advance_x.eq(depth // 16)
            yield dut.pixel_advance_y.eq((depth // 16) * in_x_dim)
            yield dut.depth.eq(depth // 16)
            yield dut.num_repeats.eq(8)
            yield
            # Reset, let it run for a bit, then toggle start high to begin
            yield dut.reset.eq(1)
            yield
            yield dut.reset.eq(0)
            for _ in range(10):
                yield
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)
            yield

            # For each of the four outputs, capture values between first and last
            # Number of pixels of output we want to capture
            # Test with 3 rows
            num_pixels = 3 * data.output_dims[2]
            actual = [[], [], [], []]
            pixel = 0
            cycle = 0
            first_seen = last_seen = -10
            while pixel < num_pixels:
                if (yield dut.first):
                    first_seen = cycle
                if (yield dut.last):
                    last_seen = cycle

                for i in range(4):
                    if cycle == first_seen + i:
                        actual[i] = []
                    actual[i].append((yield dut.data_out[i]))
                    if cycle == last_seen + i:
                        expected = self.pixel_input_values(pixel)
                        self.assertEqual(
                            actual[i], expected, msg=f"differ at pixel {pixel}")
                        pixel += 1
                cycle += 1
                yield

        self.run_sim(process, False)
