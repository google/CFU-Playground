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


from nmigen_cfu import TestBase

from .ram_input import PixelAddressGenerator


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
