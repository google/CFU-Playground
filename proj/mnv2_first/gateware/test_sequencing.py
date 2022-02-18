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


from amaranth.sim import Delay

from amaranth_cfu import TestBase

from .delay import Delayer
from .sequencing import Delayer, GateCalculator, Sequencer, UpCounter


class UpCounterTest(TestBase):
    def create_dut(self):
        return UpCounter(5)

    def test(self):
        DATA = [
            # count all the way around a few times
            ((0, 0), 0),
            ((0, 0), 0),
            ((0, 1), 0),
            ((0, 1), 0),
            ((0, 1), 0),
            ((0, 1), 1),
            ((0, 0), 0),
            ((0, 1), 0),
            ((0, 0), 0),
            ((0, 1), 0),
            ((0, 0), 0),
            ((0, 1), 0),
            ((0, 0), 0),
            ((0, 1), 1),
            # try restart with or without count_en
            ((0, 1), 0),
            ((0, 1), 0),
            ((1, 0), 0),
            ((0, 1), 0),
            ((1, 1), 0),
        ]

        def process():
            yield self.dut.max.eq(4)
            for n, (inputs, expected) in enumerate(DATA):
                restart, en = inputs
                yield self.dut.restart.eq(restart)
                yield self.dut.en.eq(en)
                yield Delay(0.25)
                self.assertEqual((yield self.dut.done), expected, f"case={n}")
                yield
        self.run_sim(process, False)


class DelayerTest(TestBase):
    def create_dut(self):
        return Delayer(3)

    def test(self):
        DATA = [
            (0, 0),
            (1, 0),
            (0, 0),
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 0),
            (1, 0),
            (1, 1),
            (1, 1),
            (0, 1),
            (0, 1),
            (0, 1),
        ]

        def process():
            for n, (input, expected) in enumerate(DATA):
                yield self.dut.input.eq(input)
                yield Delay(0.25)
                self.assertEqual((yield self.dut.output), expected, f"case={n}")
                yield
        self.run_sim(process, False)


class GateCalculatorTest(TestBase):
    def create_dut(self):
        return GateCalculator()

    def test(self):
        DATA = [
            # Start, stop without blockages
            ((0, 0, 1, 1), 0),
            ((1, 0, 1, 1), 1),
            ((0, 0, 1, 1), 1),
            ((0, 0, 1, 1), 1),
            ((0, 1, 1, 1), 1),
            ((0, 0, 1, 1), 0),

            # Test various conditions
            ((0, 0, 0, 1), 0),
            ((1, 0, 0, 1), 0),
            ((0, 0, 1, 1), 1),
            ((0, 0, 1, 0), 0),
            ((0, 0, 0, 1), 0),
            ((0, 0, 1, 1), 1),
            ((0, 1, 1, 1), 1),
            ((0, 0, 1, 1), 0),
        ]

        def process():
            for n, (input, expected) in enumerate(DATA):
                start_run, all_output_finished, in_store_ready, fifo_has_space = input
                yield self.dut.start_run.eq(start_run)
                yield self.dut.all_output_finished.eq(all_output_finished)
                yield self.dut.in_store_ready.eq(in_store_ready)
                yield self.dut.fifo_has_space.eq(fifo_has_space)
                yield Delay(0.25)
                self.assertEqual((yield self.dut.gate), expected, f"case={n}")
                yield
        self.run_sim(process, False)


class SequencerTest(TestBase):
    def create_dut(self):
        return Sequencer()

    def test(self):

        def data():
            yield (0, 0, 1), (0, 0, 0, 0, 0, 0)
            yield (1, 1, 0), (0, 0, 0, 0, 0, 0)
            yield (0, 0, 1), (0, 0, 0, 0, 0, 0)

            # read input and filter, starting pipeline
            for i in range(24):
                yield (0, 1, 1), (1, 0, i != 0, 0, 0, 0)
                yield (0, 1, 1), (1, 0, i != 0, i != 0, 0, 0)
                yield (0, 1, 1), (1, 0, 1, 0, 0, 0)
                yield (0, 1, 1), (1, 0, 1, 0, 0, 0)
                yield (0, 1, 1), (1, 0, 1, 0, 0, 0)
                yield (0, 1, 1), (1, 0, 1, 0, i != 0, i != 0 and i % 4 == 0)
                yield (0, 1, 1), (1, 0, 1, 0, 0, 0)
                yield (0, 1, 1), (1, i == 23, 1, 0, 0, 0)

            # Wait for output to work through - gate should be off
            yield (0, 1, 1), (0, 0, 1, 0, 0, 0)
            yield (0, 1, 1), (0, 0, 1, 1, 0, 0)
            yield (0, 1, 1), (0, 0, 0, 0, 0, 0)
            yield (0, 1, 1), (0, 0, 0, 0, 0, 0)
            yield (0, 1, 1), (0, 0, 0, 0, 0, 0)
            yield (0, 1, 1), (0, 0, 0, 0, 1, 1)
            yield (0, 1, 1), (0, 0, 0, 0, 0, 0)
            yield (0, 0, 1), (0, 0, 0, 0, 0, 0)

        def process():
            # test, input = 32 values (8 words), output = 24 values (6 words),
            # so 32*24/4 = 192 filter words
            yield self.dut.input_depth_words.eq(8)
            yield self.dut.filter_value_words.eq(192)

            for n, (inputs, expected) in enumerate(data()):
                start_run, in_store_ready, fifo_has_space = inputs
                yield self.dut.start_run.eq(start_run)
                yield self.dut.in_store_ready.eq(in_store_ready)
                yield self.dut.fifo_has_space.eq(fifo_has_space)
                yield Delay(0.25)
                gate, all_output_finished, madd_done, acc_done, pp_done, out_word_done = expected
                self.assertEqual((yield self.dut.gate), gate, f"case={n}")
                self.assertEqual((yield self.dut.all_output_finished), all_output_finished, f"case={n}")
                self.assertEqual((yield self.dut.madd_done), madd_done, f"case={n}")
                self.assertEqual((yield self.dut.acc_done), acc_done, f"case={n}")
                self.assertEqual((yield self.dut.pp_done), pp_done, f"case={n}")
                self.assertEqual((yield self.dut.out_word_done), out_word_done, f"case={n}")
                yield

        self.run_sim(process, False)
