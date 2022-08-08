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

"""Tests for mode0_input.py"""

from amaranth import Memory

from .conv2d_data import fetch_data
from .mode0_input import (
    EvenPixelAddressGenerator,
    Mode0InputFetcher,
    ValueAddressGenerator,
    ValueReader)
from .ram_mux import RamMux
from ..util import TestBase
from ..util import pack_vals


class EvenPixelAddressGeneratorTest(TestBase):
    """Tests EvenPixelAddressGenerator class."""

    def create_dut(self):
        return EvenPixelAddressGenerator()

    def test_it(self):
        dut = self.dut
        base_addr = 0x1234

        def expected_addr(n):
            # Each value should be generated 8 times
            index = n // 8
            # 80 values per row
            row, col = index // 80, index % 80
            return base_addr + row * 322 * 2 + col * 4

        def process():
            yield dut.base_addr.eq(base_addr)
            yield
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)
            yield
            for i in range(2000):
                # One next pulse every 4 cycles
                yield dut.next.eq(1)
                yield
                self.assertEqual((yield dut.addr), expected_addr(i))
                yield dut.next.eq(0)
                yield
                self.assertEqual((yield dut.addr), expected_addr(i + 1))
                yield
                yield

        self.run_sim(process, False)


class ValueAddressGeneratorTest(TestBase):
    """Tests ValueAddressGenerator class."""

    def create_dut(self):
        return ValueAddressGenerator()

    def test_it(self):
        dut = self.dut
        DATA = [
            # (reset, start, start_addr), (first, last, addr_out)
            ((1, 0, 1000), (0, 0, None)),
            # Check not running after reset
            ((0, 0, 1000), (0, 0, 1000)),
            ((0, 0, 1000), (0, 0, 1000)),
            # Start and let cycle a few times
            ((0, 1, 1000), (0, 0, 1000)),
            ((0, 0, 1000), (1, 0, 1000)),
            ((0, 0, 1000), (0, 0, 1322)),
            ((0, 0, 1000), (0, 0, 1644)),
            ((0, 0, 1000), (0, 1, 1966)),  # end cycle
            ((0, 0, 1004), (1, 0, 1004)),
            ((0, 0, 1004), (0, 0, 1326)),
            ((0, 0, 1004), (0, 0, 1648)),
            ((0, 0, 1004), (0, 1, 1970)),  # end cycle
            # Reset and check not running after reset
            ((1, 0, 1000), (1, 0, None)),
            ((0, 0, 1000), (0, 0, 1000)),
            ((0, 0, 1000), (0, 0, 1000)),
        ]

        def process():
            for (reset, start, start_addr), (first, last, addr_out) in DATA:
                yield dut.reset.eq(reset)
                yield dut.start.eq(start)
                yield dut.start_addr.eq(start_addr)
                yield
                self.assertEqual((yield dut.first), first)
                self.assertEqual((yield dut.last), last)
                if addr_out is not None:
                    self.assertEqual((yield dut.addr_out), addr_out)

        self.run_sim(process, False)


class ValueReaderTest(TestBase):
    """Tests ValueReader class."""

    def create_dut(self):
        # Create a value reader connected via a RamMux to memories simulating
        # LRAMs with each byte is set to the value of its byte address
        reader = ValueReader()
        self.m.submodules["ram_mux"] = ram_mux = RamMux()
        self.m.d.comb += ram_mux.phase.eq(reader.ram_mux_phase)

        def make_ram(n, init):
            mem = Memory(width=32, depth=4, init=init)
            self.m.submodules[f"rp{n}"] = rp = mem.read_port(transparent=False)
            self.m.d.comb += [
                ram_mux.lram_data[n].eq(rp.data),
                rp.addr.eq(ram_mux.lram_addr[n]),
                rp.en.eq(1),
                ram_mux.addr_in[n].eq(reader.ram_mux_addr[n]),
                reader.ram_mux_data[n].eq(ram_mux.data_out[n]),
            ]
        make_ram(0, [0x03020100, 0x13121110, 0x23222120, 0x33323130, ])
        make_ram(1, [0x07060504, 0x17161514, 0x27262524, 0x37363534, ])
        make_ram(2, [0x0b0a0908, 0x1b1a1918, 0x2b2a2928, 0x3b3a3938, ])
        make_ram(3, [0x0f0e0d0c, 0x1f1e1d1c, 0x2f2e2d2c, 0x3f3e3d3c, ])
        return reader

    def test_it(self):
        dut = self.dut

        DATA = [
            # addr, val0, val1
            # Test all 8 cases using block 1 (with overlap to block 2)
            (0x10, 0x13121110, 0x15141312),
            (0x12, 0x15141312, 0x17161514),
            (0x14, 0x17161514, 0x19181716),
            (0x16, 0x19181716, 0x1b1a1918),
            (0x18, 0x1b1a1918, 0x1d1c1b1a),
            (0x1a, 0x1d1c1b1a, 0x1f1e1d1c),
            (0x1c, 0x1f1e1d1c, 0x21201f1e),
            (0x1e, 0x21201f1e, 0x23222120),
            # Test more addresses from other blocks
            (0x00, 0x03020100, 0x05040302),
            (0x06, 0x09080706, 0x0b0a0908),
            (0x28, 0x2b2a2928, 0x2d2c2b2a),
            (0x2a, 0x2d2c2b2a, 0x2f2e2d2c),
            (0x2e, 0x31302f2e, 0x33323130),
        ]

        def process():
            val1_delayed = 0
            for i in range(len(DATA) + 1):
                if i < len(DATA):
                    addr, _, _ = DATA[i]
                yield dut.addr.eq(addr)
                yield
                if i > 1:
                    self.assertEqual((yield dut.data_out[1]), val1_delayed)
                if i > 0:
                    _, val0, val1 = DATA[i - 1]
                    self.assertEqual((yield dut.data_out[0]), val0)
                    val1_delayed = val1

        self.run_sim(process, False)


class Mode0InputFetcherTest(TestBase):
    """Tests Mode0InputFetcher class."""
    BASE_ADDR = 0xA0

    def create_dut(self):
        fetcher = Mode0InputFetcher()
        # Connect RAM Mux with simulated LRAMs containing data
        self.m.submodules["ram_mux"] = ram_mux = RamMux()
        self.m.d.comb += ram_mux.phase.eq(fetcher.ram_mux_phase)
        for i in range(4):
            pad = [0] * (self.BASE_ADDR // 16)
            init = (pad + self.data.input_data[i::4])[:1024]
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
        self.data = fetch_data('sample_conv_06')
        self.raw_input = self.data.raw_input_data
        super().setUp()

    def expected_values(self, n):
        # Get values for a given pixel number
        # Each even/odd pair should be generated 8 times
        index = n // 16 * 2 + (n & 1)
        # 160 values per row
        row, col = index // 160, index % 160
        addr = row * 322 * 2 + col * 2
        return [
            pack_vals(*self.raw_input[i: i + 4])
            for i in range(addr, addr + 4 * 322, 322)
        ]

    def test_it(self):
        dut = self.dut
        data = self.data

        def process():
            yield dut.base_addr.eq(self.BASE_ADDR)
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

            # For each of the two outputs, capture values between first and last
            # Number of pixels of output we want to capture
            # Test with 3 rows
            num_pixels = 3 * data.output_dims[2] * 8
            actual = [[], []]
            pixel = 0
            cycle = 0
            first_seen = last_seen = -10
            while pixel < num_pixels:
                if (yield dut.first):
                    first_seen = cycle
                if (yield dut.last):
                    last_seen = cycle

                for i in range(2):
                    if cycle == first_seen + i:
                        actual[i] = []
                    actual[i].append((yield dut.data_out[i]))
                    if cycle == last_seen + i:
                        expected = self.expected_values(pixel)
                        self.assertEqual(
                            actual[i], expected, msg=f"differ at pixel {pixel}")
                        pixel += 1
                cycle += 1
                yield

        self.run_sim(process, False)
