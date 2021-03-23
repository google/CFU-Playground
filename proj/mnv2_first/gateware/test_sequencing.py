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

from .sequencing import UpCounter


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
