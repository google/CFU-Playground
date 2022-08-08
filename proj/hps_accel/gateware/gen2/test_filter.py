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

"""Tests for filter.py"""

from .filter import FilterStore
from ..util import TestBase


class FilterStoreTest(TestBase):
    """Tests FilterStore class"""

    def create_dut(self):
        return FilterStore()

    def read_three_times(self):
        dut = self.dut
        yield dut.start.eq(1)
        yield
        yield dut.start.eq(0)
        yield
        yield
        for _ in range(3):
            for addr in range(512):
                for store in range(2):
                    expected = 10000 + 1000 * store + (addr - store) % 512
                    self.assertEqual((yield dut.values_out[store]), expected,
                                        f"store={store}, addr={addr}")
                yield

    def test_it(self):
        dut = self.dut

        def process():
            # Write 512 valuees to memory 0, then 1
            yield dut.size.eq(512)
            write = dut.write_input
            for store in range(2):
                yield write.payload.store.eq(store)
                for addr in range(512):
                    yield write.valid.eq(1)
                    yield write.payload.addr.eq(addr)
                    yield write.payload.data.eq(10000 + 1000 * store + addr)
                    yield
                    self.assertTrue((yield write.ready))
                    yield write.valid.eq(0)
            # Read all values three times
            yield
            yield from self.read_three_times()

            # Allow to continue a while
            for _ in range(123):
                yield

            # Fetch values three more times
            yield from self.read_three_times()
            

        self.run_sim(process, False)
