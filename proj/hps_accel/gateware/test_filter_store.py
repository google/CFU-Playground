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


from nmigen_cfu import TestBase
from nmigen_cfu.util import pack128

from .filter_store import FilterStore


class FilterStoreTest(TestBase):
    def create_dut(self):
        return FilterStore(depth=12)

    # Test data which we fill into the store in reset_and_fill()
    # and expect to read back out of it in read()
    filter_values = list(range(11, 11 + 12))

    def reset_and_fill(self):
        yield self.dut.num_words_input.payload.eq(len(self.filter_values))
        yield self.dut.num_words_input.valid.eq(1)
        # Setting num_words_input.valid triggers a reset,
        # but it will take either 1 or 2 cycles to take effect,
        # depending on where in the FSM we triggered the reset.
        while (yield self.dut.num_words_input.ready) != 1:
            yield
        yield self.dut.num_words_input.valid.eq(0)
        # Need to wait 1 cycle before sending the first input
        yield
        yield self.dut.data_input.valid.eq(1)
        for filter_value in self.filter_values:
            self.assertEqual((yield self.dut.data_input.ready), 1)
            yield self.dut.data_input.payload.eq(filter_value)
            yield
        yield self.dut.data_input.valid.eq(0)

    def read_out(self):
        for i in range(0, len(self.filter_values), 4):
            yield self.dut.next.eq(1)
            yield
            yield self.dut.next.eq(0)
            yield self.dut.data_output.ready.eq(1)
            while (yield self.dut.data_output.valid) != 1:
                yield
            self.assertEqual((yield self.dut.data_output.payload),
                             pack128(*self.filter_values[i:i + 4]))

    def test_it(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    # TODO(dcallagh): this version cannot stream with zero latency
    def xtest_it_can_stream_output(self):
        def process():
            yield from self.reset_and_fill()
            # Set up for streaming output. We will receive output every cycle.
            yield self.dut.data_output.ready.eq(1)
            yield self.dut.next.eq(1)
            # Currently 1 cycle delay before streaming starts
            yield
            for i in range(0, len(self.filter_values), 4):
                yield
                self.assertEqual((yield self.dut.data_output.valid), 1)
                self.assertEqual((yield self.dut.data_output.payload),
                                 pack128(*self.filter_values[i:i + 4]))
        self.run_sim(process)

    def test_it_wraps_back_to_the_start_when_reading(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.read_out()
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_tolerate_delays_while_filling(self):
        def process():
            yield self.dut.num_words_input.payload.eq(len(self.filter_values))
            yield self.dut.num_words_input.valid.eq(1)
            yield
            yield self.dut.num_words_input.valid.eq(0)
            yield
            for filter_value in self.filter_values:
                # Delay before we present each value
                yield self.dut.data_input.valid.eq(0)
                for _ in range(10):
                    self.assertEqual((yield self.dut.data_input.ready), 1)
                    yield
                yield self.dut.data_input.valid.eq(1)
                yield self.dut.data_input.payload.eq(filter_value)
                yield
            yield self.dut.data_input.valid.eq(0)
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_tolerate_delays_while_reading(self):
        def process():
            yield from self.reset_and_fill()
            for i in range(0, len(self.filter_values), 4):
                yield self.dut.data_output.ready.eq(0)
                yield self.dut.next.eq(1)
                yield
                yield self.dut.next.eq(0)
                # Delay before consuming each value
                # (Delaying for an odd number of cycles is more likely to catch
                # bugs, since the store contains an even number of elements)
                for _ in range(13):
                    yield
                yield self.dut.data_output.ready.eq(1)
                self.assertEqual((yield self.dut.data_output.valid), 1)
                self.assertEqual((yield self.dut.data_output.payload),
                                 pack128(*self.filter_values[i:i + 4]))
                yield
        self.run_sim(process)

    def test_it_can_be_reset_while_filling(self):
        def process():
            # Reset and partially fill some elements
            yield self.dut.num_words_input.payload.eq(len(self.filter_values))
            yield self.dut.num_words_input.valid.eq(1)
            yield
            yield self.dut.num_words_input.valid.eq(0)
            yield
            self.assertEqual((yield self.dut.data_input.ready), 1)
            yield self.dut.data_input.payload.eq(99)
            yield self.dut.data_input.valid.eq(1)
            yield
            self.assertEqual((yield self.dut.data_input.ready), 1)
            yield self.dut.data_input.payload.eq(98)
            yield
            yield self.dut.data_input.valid.eq(0)
            # Now reset and fill again from the start
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_be_reset_after_filling(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_be_reset_while_reading(self):
        def process():
            yield from self.reset_and_fill()
            # Read past the first values
            yield self.dut.next.eq(1)
            yield
            yield self.dut.next.eq(0)
            yield
            # Now reset and fill again from the start
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)
