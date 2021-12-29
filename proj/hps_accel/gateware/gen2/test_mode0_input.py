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

from nmigen_cfu import TestBase
from .mode0_input import EvenPixelAddressGenerator


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
