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

from .output import OutputQueueGetter


class OutputQueueGetterTest(TestBase):
    def create_dut(self):
        return OutputQueueGetter()

    def test(self):
        DATA = [
            # FIFO ready first
            ((0, 0, 0), (0, 0, 0)),
            ((0, 12, 1), (0, 0, 0)),
            ((0, 12, 1), (0, 0, 0)),
            ((1, 12, 1), (1, 1, 12)),

            # Xetter started first
            ((0, 0, 0), (0, 0, 0)),
            ((1, 0, 0), (1, 0, 0)),
            ((0, 0, 0), (1, 0, 0)),
            ((0, 24, 1), (1, 1, 24)),
            ((0, 0, 0), (0, 0, 0)),

            # Ready at same time
            ((1, 44, 1), (1, 1, 44)),
            ((1, 33, 1), (1, 1, 33)),
            ((1, 22, 1), (1, 1, 22)),
            ((0, 0, 0), (0, 0, 0)),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                start, r_data, r_rdy = inputs
                yield self.dut.start.eq(start)
                yield self.dut.r_data.eq(r_data)
                yield self.dut.r_rdy.eq(r_rdy)
                yield Delay(0.25)
                r_en, done, output = expected
                self.assertEqual((yield self.dut.r_en), r_en, f"case={n}")
                self.assertEqual((yield self.dut.done), done, f"case={n}")
                if done:
                    self.assertEqual((yield self.dut.output), output, f"case={n}")
                yield
        self.run_sim(process, False)
