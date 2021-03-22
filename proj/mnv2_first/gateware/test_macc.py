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

from .macc import Accumulator, Macc4Run1


class AccumulatorTest(TestBase):
    def create_dut(self):
        return Accumulator()

    def test(self):
        DATA = [
            ((1, 10, 0), 10),
            ((0, 25, 0), 10),
            ((1, 17, 0), 27),
            ((1, -29, 0), -2),
            ((1, 25, 1), 23),
            ((0, 25, 0), 0),
            ((1, 10, 0), 10),
            ((0, 5, 1), 10),
            ((0, 2, 0), 0),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                add_en, in_value, clear = inputs
                yield self.dut.add_en.eq(add_en)
                yield self.dut.in_value.eq(in_value)
                yield self.dut.clear.eq(clear)
                yield Delay(0.25)
                if expected is not None:
                    self.assertEqual((yield self.dut.result), expected, f"case={n}")
                yield
        self.run_sim(process, True)


class Macc4Run1Test(TestBase):
    def create_dut(self):
        return Macc4Run1(512)

    def test(self):
        DATA = [
            # Allow time to prepare
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            # Start, but not yet ready, then ready
            ((1, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            # Ready, not ready, ready, ready, not ready, ready
            ((0, 1, 0, 0), (1, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 1, 3, 0), (1, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 1, 2, 0), (1, 0, 0, 0, 0)),
            ((0, 1, 0, 0), (1, 0, 0, 0, 0)),
            ((0, 0, 5, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 7, 0), (0, 1, 17, 0, 0)),
            # wait for post processor
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 66), (0, 0, 0, 1, 66)),
            # Do one at full speed
            ((1, 1, 0, 0), (1, 0, 0, 0, 0)),
            ((0, 1, 0, 0), (1, 0, 0, 0, 0)),
            ((0, 1, 1, 0), (1, 0, 0, 0, 0)),
            ((0, 1, 2, 0), (1, 0, 0, 0, 0)),
            ((0, 0, 3, 0), (0, 0, 0, 0, 0)),
            ((0, 0, -44, 0), (0, 1, -38, 0, 0)),
            # wait for post processor
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0, 0, 0)),
            ((0, 0, 0, 99), (0, 0, 0, 1, 99)),
        ]

        def process():
            yield self.dut.input_depth.eq(4)
            for n, (inputs, expected) in enumerate(DATA):
                start, madd4_inputs_ready, madd4_result, pp_result = inputs
                yield self.dut.start.eq(start)
                yield self.dut.madd4_inputs_ready.eq(madd4_inputs_ready)
                yield self.dut.madd4_result.eq(madd4_result)
                yield self.dut.pp_result.eq(pp_result)
                yield Delay(0.25)
                madd4_start, pp_start, pp_accumulator, done, output = expected
                self.assertEqual((yield self.dut.madd4_start), madd4_start, f"case={n}")
                self.assertEqual((yield self.dut.pp_start), pp_start, f"case={n}")
                self.assertEqual((yield self.dut.pp_accumulator), pp_accumulator, f"case={n}")
                self.assertEqual((yield self.dut.done), done, f"case={n}")
                if done:
                    self.assertEqual((yield self.dut.output.as_signed()), output, f"case={n}")
                yield
        self.run_sim(process, False)
