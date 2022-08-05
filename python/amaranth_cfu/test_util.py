#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
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

__package__ = 'amaranth_cfu'

from amaranth import Signal
from amaranth.sim import Settle, Delay

from .util import SequentialMemoryReader, TestBase, ValueBuffer, SequentialMemoryReader


class ValueBufferTest(TestBase):
    def create_dut(self):
        self.capture = Signal()
        self.in_signal = Signal(4)
        return ValueBuffer(self.in_signal, self.capture)

    def test(self):
        DATA = [
            ((0, 0), 0),
            ((1, 5), 5),
            ((0, 3), 5),
            ((0, 2), 5),
            ((0, 2), 5),
            ((1, 2), 2),
            ((0, 2), 2),
            ((0, 2), 2),
        ]

        def process():
            for n, ((capture, in_sig), expected_output) in enumerate(DATA):
                yield self.in_signal.eq(in_sig)
                yield self.capture.eq(capture)
                yield Settle()
                self.assertEqual((yield self.dut.output), expected_output, f"cycle={n}")
                yield
        self.run_sim(process, False)


class SequentialMemoryReaderTest(TestBase):
    def create_dut(self):
        return SequentialMemoryReader(width=16, max_depth=8)

    def test(self):
        DATA = [
            # Restart and iterate through at irregular intervals, wrapping
            ((1, 0, 0x00), (0, None)),
            ((0, 0, 0xaa), (1, 0xaa)),
            ((0, 0, 0xbb), (1, 0xaa)),
            ((0, 1, 0xbb), (1, 0xaa)),
            ((0, 1, 0xbb), (2, 0xbb)),
            ((0, 0, 0xcc), (3, 0xcc)),
            ((0, 1, 0xdd), (3, 0xcc)),
            ((0, 0, 0xdd), (0, 0xdd)),
            ((0, 1, 0xaa), (0, 0xdd)),
            ((0, 1, 0xaa), (1, 0xaa)),
            ((0, 0, 0xbb), (2, 0xbb)),
            # Restart and iterate every cycle
            ((1, 0, 0xcc), (0, None)),
            ((0, 1, 0xaa), (1, 0xaa)),
            ((0, 1, 0xbb), (2, 0xbb)),
            ((0, 1, 0xcc), (3, 0xcc)),
            ((0, 1, 0xdd), (0, 0xdd)),
            ((0, 1, 0xaa), (1, 0xaa)),
        ]

        def process():
            yield self.dut.limit.eq(4)  # depth constant for this test
            yield
            for n, (inputs, outputs) in enumerate(DATA):
                restart, next, mem_data = inputs
                yield self.dut.restart.eq(restart)
                yield self.dut.next.eq(next)
                yield self.dut.mem_data.eq(mem_data)
                yield Delay(0.1)
                mem_addr, data = outputs
                self.assertEqual((yield self.dut.mem_addr), mem_addr, f"cycle={n}")
                if data is not None:
                    self.assertEqual((yield self.dut.data), data, f"cycle={n}")
                yield
        self.run_sim(process)
