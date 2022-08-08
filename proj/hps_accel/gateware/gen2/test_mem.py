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

import random

from amaranth.sim import Delay

from .mem import LoopingAddressGenerator, LoopingCounter, SinglePortMemory
from ..util import TestBase


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


class LoopingCounterTest(TestBase):
    """Tests LoopingCounter."""

    def create_dut(self):
        return LoopingCounter(4)

    def test_it(self):
        X = None
        DATA = [
            # (count, reset, next), (value, last)
            # Begin with count 4
            ((4, 1, 0), (X, X)),
            ((4, 0, 0), (0, 0)),
            ((4, 0, 0), (0, 0)),
            ((4, 0, 1), (0, 0)),
            ((4, 0, 0), (1, 0)),
            ((4, 0, 0), (1, 0)),
            ((4, 0, 1), (1, 0)),
            ((4, 0, 1), (2, 0)),
            ((4, 0, 1), (3, 1)),
            ((4, 0, 1), (0, 0)),
            ((4, 0, 0), (1, 0)),
            # Now with count 3
            ((3, 1, 0), (X, X)),
            ((3, 0, 1), (0, 0)),
            ((3, 0, 1), (1, 0)),
            ((3, 0, 1), (2, 1)),
            ((3, 0, 1), (0, 0)),
            ((3, 0, 1), (1, 0)),
            ((3, 0, 0), (2, 1)),
            ((3, 0, 0), (2, 1)),
        ]

        def process():
            dut = self.dut
            for (count, reset, next_), (value, last) in DATA:
                yield dut.count.eq(count)
                yield dut.reset.eq(reset)
                yield dut.next.eq(next_)
                yield Delay(0.1)
                if value is not None:
                    self.assertEqual((yield dut.value), value)
                if last is not None:
                    self.assertEqual((yield dut.last), last)
                yield
        self.run_sim(process, False)


class LoopingAddressGeneratorTest(TestBase):
    """Tests Looping Address Generator."""

    def create_dut(self):
        return LoopingAddressGenerator(depth=16, max_repeats=8)

    def test_addresses(self):
        def check_addresses(count, repeats):
            dut = self.dut
            # Set parameters
            yield dut.next.eq(0)
            yield dut.params_input.payload.count.eq(count)
            yield dut.params_input.payload.repeats.eq(repeats)
            yield dut.params_input.valid.eq(1)
            yield
            yield dut.params_input.valid.eq(0)
            yield
            # Check generated addresses
            yield self.dut.next.eq(1)
            expected = [n for n in range(count) for _ in range(repeats)]
            for value in expected:
                for _ in range(random.randrange(0, 2)):
                    yield dut.next.eq(0)
                    yield
                yield dut.next.eq(1)
                yield
                self.assertEqual((yield dut.addr), value)

        def process():
            yield from check_addresses(16, 8)
            yield from check_addresses(15, 7)
            yield from check_addresses(12, 1)
        self.run_sim(process, False)
