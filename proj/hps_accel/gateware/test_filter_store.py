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

from .filter_store import FilterStore


class FilterStoreTest(TestBase):
    def create_dut(self):
        return FilterStore(depth=12)

    # Test data which we fill into the store in reset_and_fill()
    # and expect to read back out of it in read()
    filter_values = list(range(11, 11 + 12))

    def reset_and_fill(self):
        self.assertEqual((yield self.dut.num_words.ready), 1)
        yield self.dut.num_words.payload.eq(len(self.filter_values))
        yield self.dut.num_words.valid.eq(1)
        # Need to wait 1 cycle before sending the first input
        yield
        yield self.dut.num_words.valid.eq(0)
        yield self.dut.input.valid.eq(1)
        for filter_value in self.filter_values:
            self.assertEqual((yield self.dut.input.ready), 1)
            yield self.dut.input.payload.eq(filter_value)
            yield
        yield self.dut.input.valid.eq(0)

    def read_out(self):
        for i in range(0, len(self.filter_values), 4):
            yield self.dut.next.eq(1)
            yield
            yield self.dut.next.eq(0)
            yield self.dut.output[0].ready.eq(1)
            yield self.dut.output[1].ready.eq(1)
            yield self.dut.output[2].ready.eq(1)
            yield self.dut.output[3].ready.eq(1)
            while (yield self.dut.output[0].valid) != 1:
                yield
            self.assertEqual((yield self.dut.output[0].valid), 1)
            self.assertEqual((yield self.dut.output[1].valid), 1)
            self.assertEqual((yield self.dut.output[2].valid), 1)
            self.assertEqual((yield self.dut.output[3].valid), 1)
            self.assertEqual((yield self.dut.output[0].payload), self.filter_values[i + 0])
            self.assertEqual((yield self.dut.output[1].payload), self.filter_values[i + 1])
            self.assertEqual((yield self.dut.output[2].payload), self.filter_values[i + 2])
            self.assertEqual((yield self.dut.output[3].payload), self.filter_values[i + 3])

    def test_it(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_stream_output(self):
        def process():
            yield from self.reset_and_fill()
            # Set up for streaming output. We will receive four output words
            # every cycle.
            yield self.dut.output[0].ready.eq(1)
            yield self.dut.output[1].ready.eq(1)
            yield self.dut.output[2].ready.eq(1)
            yield self.dut.output[3].ready.eq(1)
            yield self.dut.next.eq(1)
            # Currently 3 cycle delay before streaming starts
            yield
            yield
            yield
            for i in range(0, len(self.filter_values), 4):
                yield
                self.assertEqual((yield self.dut.output[0].valid), 1)
                self.assertEqual((yield self.dut.output[1].valid), 1)
                self.assertEqual((yield self.dut.output[2].valid), 1)
                self.assertEqual((yield self.dut.output[3].valid), 1)
                self.assertEqual((yield self.dut.output[0].payload), self.filter_values[i + 0])
                self.assertEqual((yield self.dut.output[1].payload), self.filter_values[i + 1])
                self.assertEqual((yield self.dut.output[2].payload), self.filter_values[i + 2])
                self.assertEqual((yield self.dut.output[3].payload), self.filter_values[i + 3])
        self.run_sim(process)

    def test_it_wraps_back_to_the_start_when_reading(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.read_out()
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_tolerate_delays_while_filling(self):
        def process():
            yield self.dut.num_words.payload.eq(len(self.filter_values))
            yield self.dut.num_words.valid.eq(1)
            yield
            yield self.dut.num_words.valid.eq(0)
            for filter_value in self.filter_values:
                # Delay before we present each value
                yield self.dut.input.valid.eq(0)
                for _ in range(10):
                    self.assertEqual((yield self.dut.input.ready), 1)
                    yield
                yield self.dut.input.valid.eq(1)
                yield self.dut.input.payload.eq(filter_value)
                yield
            yield self.dut.input.valid.eq(0)
            yield from self.read_out()
        self.run_sim(process)

    def test_it_can_tolerate_delays_while_reading(self):
        def process():
            yield from self.reset_and_fill()
            for i in range(0, len(self.filter_values), 4):
                yield self.dut.output[0].ready.eq(0)
                yield self.dut.output[1].ready.eq(0)
                yield self.dut.output[2].ready.eq(0)
                yield self.dut.output[3].ready.eq(0)
                yield self.dut.next.eq(1)
                yield
                yield self.dut.next.eq(0)
                # Delay before consuming each value
                # (Delaying for an odd number of cycles is more likely to catch
                # bugs, since the store contains an even number of elements)
                for _ in range(13):
                    yield
                yield self.dut.output[0].ready.eq(1)
                yield self.dut.output[1].ready.eq(1)
                yield self.dut.output[2].ready.eq(1)
                yield self.dut.output[3].ready.eq(1)
                while not (yield self.dut.output[0].valid):
                    yield
                self.assertEqual((yield self.dut.output[1].valid), 1)
                self.assertEqual((yield self.dut.output[2].valid), 1)
                self.assertEqual((yield self.dut.output[3].valid), 1)
                self.assertEqual((yield self.dut.output[0].payload), self.filter_values[i + 0])
                self.assertEqual((yield self.dut.output[1].payload), self.filter_values[i + 1])
                self.assertEqual((yield self.dut.output[2].payload), self.filter_values[i + 2])
                self.assertEqual((yield self.dut.output[3].payload), self.filter_values[i + 3])
        self.run_sim(process)

    def test_it_can_be_reset_while_filling(self):
        def process():
            # Reset and partially fill some elements
            yield self.dut.num_words.payload.eq(len(self.filter_values))
            yield self.dut.num_words.valid.eq(1)
            yield
            yield self.dut.num_words.valid.eq(0)
            self.assertEqual((yield self.dut.input.ready), 1)
            yield self.dut.input.payload.eq(99)
            yield self.dut.input.valid.eq(1)
            yield
            self.assertEqual((yield self.dut.input.ready), 1)
            yield self.dut.input.payload.eq(99)
            yield
            # Now reset and fill again from the start
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    # TODO(dcallagh): fix reset logic so that this case passes.
    # It currently breaks because the first output values get stuck at their
    # output sources after the first fill, and remain stuck there during the
    # second fill and up to the subsequent read.
    def xtest_it_can_be_reset_after_filling(self):
        def process():
            yield from self.reset_and_fill()
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)

    # TODO(dcallagh): as above, fix reset logic
    def xtest_it_can_be_reset_while_reading(self):
        def process():
            yield from self.reset_and_fill()
            # Read past the first values
            while (yield self.dut.output[0].valid) != 1:
                yield
            yield self.dut.next.eq(1)
            yield
            yield self.dut.next.eq(0)
            yield
            # Now reset and fill again from the start
            yield from self.reset_and_fill()
            yield from self.read_out()
        self.run_sim(process)
