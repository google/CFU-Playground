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

from nmigen import unsigned
from nmigen.hdl.rec import Layout
from nmigen.sim.core import Settle, Tick

from nmigen_cfu.util import TestBase

from .flow import FlowRestrictor


class FlowRestrictorTest(TestBase):

    def create_dut(self):
        return FlowRestrictor(unsigned(8))

    def test_it(self):
        def input_producer():
            yield self.dut.input.valid.eq(1)
            # Send 6 values through the stream, matching the total number of
            # releases triggered by process() below.
            for i in range(10, 16):
                yield self.dut.input.payload.eq(i)
                yield Tick()
                while (yield self.dut.input.ready) != 1:
                    yield Tick()
        self.sim.add_process(input_producer)
        def process():
            # After reset, the stream should stay paused.
            for _ in range(10):
                self.assertEqual((yield self.dut.output.valid), 0)
                self.assertEqual((yield self.dut.release.ready), 1)
                yield
            # Trigger release of 1 value through the stream.
            yield self.dut.release.payload.eq(1)
            yield self.dut.release.valid.eq(1)
            yield
            yield Settle()
            yield self.dut.release.valid.eq(0)
            self.assertEqual((yield self.dut.output.valid), 1)
            self.assertEqual((yield self.dut.output.payload), 10)
            yield self.dut.output.ready.eq(1)
            self.assertEqual((yield self.dut.release.ready), 0)
            yield
            yield Settle()
            # After releasing 1 value, it should go back to paused.
            for _ in range(10):
                self.assertEqual((yield self.dut.output.valid), 0)
                self.assertEqual((yield self.dut.release.ready), 1)
                yield
            # Trigger release of 5 more values through the stream.
            yield self.dut.release.payload.eq(5)
            yield self.dut.release.valid.eq(1)
            yield
            yield Settle()
            yield self.dut.release.valid.eq(0)
            yield self.dut.output.ready.eq(1)
            expected_values = [11, 12, 13, 14, 15]
            for expected_value in expected_values:
                self.assertEqual((yield self.dut.output.valid), 1)
                self.assertEqual((yield self.dut.output.payload),
                                 expected_value)
                self.assertEqual((yield self.dut.release.ready), 0)
                yield
                yield Settle()
            # After releasing 5 more values, it should go back to paused.
            for _ in range(10):
                self.assertEqual((yield self.dut.output.valid), 0)
                self.assertEqual((yield self.dut.release.ready), 1)
                yield
        self.run_sim(process)
