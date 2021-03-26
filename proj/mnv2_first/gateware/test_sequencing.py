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


from nmigen.sim import Delay

from nmigen_cfu import TestBase

from .sequencing import Delayer, GateCalculator, UpCounter


class UpCounterTest(TestBase):
    def create_dut(self):
        return UpCounter(5)

    def test(self):
        DATA = [
            # count all the way around a few times
            ((0, 0), (0, 0)),
            ((0, 0), (0, 0)),
            ((0, 1), (1, 0)),
            ((0, 1), (2, 0)),
            ((0, 1), (3, 1)),
            ((0, 1), (0, 0)),
            ((0, 0), (0, 0)),
            ((0, 1), (1, 0)),
            ((0, 0), (1, 0)),
            ((0, 1), (2, 0)),
            ((0, 0), (2, 0)),
            ((0, 1), (3, 1)),
            ((0, 0), (3, 0)),
            ((0, 1), (0, 0)),
            # try restart with or without count_en
            ((0, 1), (1, 0)),
            ((0, 1), (2, 0)),
            ((1, 0), (0, 0)),
            ((0, 1), (1, 0)),
            ((1, 1), (0, 0)),
        ]

        def process():
            yield self.dut.max.eq(4)
            for n, (inputs, expected) in enumerate(DATA):
                restart, count_en = inputs
                yield self.dut.restart.eq(restart)
                yield self.dut.count_en.eq(count_en)
                yield Delay(0.25)
                count, done = expected
                self.assertEqual((yield self.dut.count), count, f"case={n}")
                self.assertEqual((yield self.dut.done), done, f"case={n}")
                yield
        self.run_sim(process, True)


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
        self.run_sim(process, True)


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
            ((0, 1, 1, 1), 0),

            # Test various conditions
            ((0, 0, 0, 1), 0),
            ((1, 0, 0, 1), 0),
            ((0, 0, 1, 1), 1),
            ((0, 0, 1, 0), 0),
            ((0, 0, 0, 1), 0),
            ((0, 0, 1, 1), 1),
            ((0, 1, 1, 1), 0),
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
        self.run_sim(process, True)
