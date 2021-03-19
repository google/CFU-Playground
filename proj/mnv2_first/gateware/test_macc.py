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

from nmigen_cfu import TestBase, pack_vals

from .macc import AccumulatorRegisterXetter, ExplicitMacc4, ImplicitMacc4


class ExplicitMacc4Test(TestBase):
    def create_dut(self):
        return ExplicitMacc4()

    def test(self):
        DATA = [
            ((0, 0, 0), 0),
            ((2, 1, 1), 3),
            ((2, 1, 1), 3),
            ((128, pack_vals(-128, -128, -128, -128), pack_vals(1, 1, 1, 1)), 0),
            ((128, pack_vals(-128, -127, -126, -125),
              pack_vals(10, 11, 12, 13)), 1 * 11 + 2 * 12 + 3 * 13),
            ((128, pack_vals(127, 0, 0, 0),
              pack_vals(10, 11, 12, 13)), 10 * 255 + 11 * 128 + 12 * 128 + 13 * 128),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                input_offset, input_value, filter_value = inputs
                yield self.dut.input_offset.eq(input_offset)
                yield self.dut.in0.eq(input_value)
                yield self.dut.in1.eq(filter_value)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual(
                    (yield self.dut.output.as_signed()), expected, f"case={n}")
                yield
        self.run_sim(process, False)


class AccumulatorRegisterXetterTest(TestBase):
    def create_dut(self):
        return AccumulatorRegisterXetter()

    def test_setget(self):
        DATA = [
            ((0, 0, 0, 0), (0, 0, 0)),

            # Add a few things
            ((0, 0, 1, 0), (0, 0, 0)),
            ((0, 0, 0, 0), (0, 0, 0)),
            ((0, 0, 1, 10), (0, 0, 0)),
            ((0, 0, 1, 22), (0, 0, 10)),
            ((0, 0, 0, 0), (0, 0, 32)),

            # Read and set to 50
            ((1, 50, 0, 0), (1, 32, 32)),
            ((0, 0, 0, 0), (0, 0, 50)),

            # Add a few more things
            ((0, 0, 1, 3), (0, 0, 50)),
            ((0, 0, 1, 7), (0, 0, 53)),
            ((0, 0, 1, 1), (0, 0, 60)),
            ((0, 0, 1, 5), (0, 0, 61)),
        ]

        def process():
            for n, ((start, in0, add_en, add_data), (done, output, value)
                    ) in enumerate(DATA):
                yield self.dut.start.eq(start)
                yield self.dut.in0.eq(in0)
                yield self.dut.add_en.eq(add_en)
                yield self.dut.add_data.eq(add_data)
                yield Delay(0.25)
                self.assertEqual((yield self.dut.done), done, f"cycle={n}")
                if done:
                    self.assertEqual((yield self.dut.output), output, f"cycle={n}")
                self.assertEqual((yield self.dut.value), value, f"cycle={n}")
                yield
        self.run_sim(process, False)


class ImplicitMacc4Test(TestBase):
    def create_dut(self):
        return ImplicitMacc4()

    def test(self):
        DATA = [
            ((0, 0, 0, 0), 0),
            ((2, 1, 1, 0), 3),
            ((2, 1, 1, 3), 3),
            ((128, pack_vals(-128, -128, -128, -128), pack_vals(1, 1, 1, 1), 0), 0),
            ((128, pack_vals(-128, -127, -126, -125),
              pack_vals(10, 11, 12, 13), 0), 1 * 11 + 2 * 12 + 3 * 13),
            ((128, pack_vals(127, 0, 0, 0),
              pack_vals(10, 11, 12, 13), 12), 10 * 255 + 11 * 128 + 12 * 128 + 13 * 128),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                input_offset, input_value, filter_value, i_ready_wait = inputs
                yield self.dut.input_offset.eq(input_offset)
                yield self.dut.f_data.eq(filter_value)
                yield self.dut.i_data.eq(input_value)
                yield self.dut.i_ready.eq(i_ready_wait == 0)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    i_ready_wait -= 1
                    yield self.dut.i_ready.eq(i_ready_wait == 0)
                    yield
                self.assertEqual(
                    (yield self.dut.output.as_signed()), expected, f"case={n}")
                yield
        self.run_sim(process, False)
