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

from amaranth import unsigned
from amaranth.hdl.rec import Layout
from amaranth.sim.core import Settle

from .flow import FlowRestrictor
from ..util import TestBase


class FlowRestrictorTest(TestBase):

    def create_dut(self):
        return FlowRestrictor(unsigned(8))

    def input_producer(self, values):
        """
        Returns a simulation process which sends the given sequence of values
        to the input endpoint of the DUT.
        """
        def process():
            yield self.dut.input.valid.eq(1)
            for value in values:
                yield self.dut.input.payload.eq(value)
                yield
                while (yield self.dut.input.ready) != 1:
                    yield
            yield self.dut.input.valid.eq(0)
        return process

    def check_paused(self):
        """
        Checks that the DUT is in its idle state: holding the stream paused,
        and ready to be triggered to release new values.
        """
        yield Settle()
        for _ in range(10):
            self.assertEqual((yield self.dut.input.ready), 0)
            self.assertEqual((yield self.dut.output.valid), 0)
            self.assertEqual((yield self.dut.release.ready), 1)
            yield

    def trigger(self, n):
        """Tells the DUT to release N values through its stream."""
        self.assertEqual((yield self.dut.release.ready), 1)
        yield self.dut.release.payload.eq(n)
        yield self.dut.release.valid.eq(1)
        yield
        yield self.dut.release.valid.eq(0)

    def check_output_values(self, expected_values):
        """Checks that the DUT produces the expected values on its output."""
        yield self.dut.output.ready.eq(1)
        for expected_value in expected_values:
            yield Settle()
            self.assertEqual((yield self.dut.output.valid), 1)
            self.assertEqual((yield self.dut.output.payload), expected_value)
            # It can't be triggered to release more values while it's busy.
            self.assertEqual((yield self.dut.release.ready), 0)
            yield
        yield self.dut.output.ready.eq(0)

    def test_release_one(self):
        self.sim.add_sync_process(self.input_producer([99]))

        def process():
            yield from self.check_paused()
            # Trigger release of 1 value through the stream.
            yield from self.trigger(1)
            yield from self.check_output_values([99])
            # After releasing 1 value, it should go back to paused.
            yield from self.check_paused()
        self.run_sim(process)

    def test_release_many(self):
        values = list(range(10, 15))
        self.sim.add_sync_process(self.input_producer(values))

        def process():
            yield from self.check_paused()
            # Trigger release of 5 values through the stream.
            yield from self.trigger(5)
            yield from self.check_output_values(values)
            # After releasing 5 values, it should go back to paused.
            yield from self.check_paused()
        self.run_sim(process)

    def test_release_batches(self):
        # 13 values going in, released in a batch of 7 then a batch of 6.
        values = list(range(50, 63))
        self.sim.add_sync_process(self.input_producer(values))

        def process():
            yield from self.check_paused()
            # Trigger the first batch.
            yield from self.trigger(7)
            yield from self.check_output_values(values[:7])
            # After releasing the first batch, it should go back to paused.
            yield from self.check_paused()
            # Trigger the next batch.
            yield from self.trigger(6)
            yield from self.check_output_values(values[7:])
            # It should go back to paused again.
            yield from self.check_paused()
        self.run_sim(process)
