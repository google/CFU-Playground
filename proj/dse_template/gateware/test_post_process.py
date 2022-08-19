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

from amaranth.sim import Settle

from amaranth_cfu import TestBase

from.post_process import PostProcessXetter, PostProcessor


class PostProcessorTestCase(TestBase):
    def create_dut(self):
        return PostProcessor()

    def test(self):
        DATA = [
            # Test data generated from actual values captured during model
            # evaluations with the RISCV (non-CFU) code.
            #
            # NOTE: only negative shift values are present in this test data
            #
            # We hold the last 3 parameters (offset, activation_min,
            # activation_max) constant while processing completes.
            # TODO: remove this constraint
            ((-41202, 50965, 1368574433, -8, -128, -128, 127), -104),
            ((7862, 15508, 2113004963, -7, -128, -128, 127), 52),
            ((-1809, 14653, 1199953844, -6, -128, -128, 127), -16),
            ((1650, -472, 1515935785, -4, -128, -128, 127), -76),
            ((-157, 4501, 1938560225, -6, -128, -128, 127), -67),
            ((706, 6992, 1300414464, -6, -128, -128, 127), -55),
            ((-597, 1760, 1982196853, -6, -128, -128, 127), -111),
            ((-9096, -46522, 1916399180, -7, -128, -128, 127), -128),
            ((459, 3378, 1417058105, -5, -128, -128, 127), -49),
            ((4160, 17773, 2130104324, -7, -128, -128, 127), 42),
            ((-9003, 14124, 1774825651, -6, -128, -128, 127), -62),
            ((2692, 8282, 1954739939, -7, -128, -128, 127), -50),
            ((27408, 50965, 1368574433, -8, -128, -128, 127), 67),
            ((339, -128, 1291426357, -6, -128, -128, 127), -126),
            ((-5146, 15508, 2113004963, -7, -128, -128, 127), -48),
            ((-167, -768, 1280572629, -5, -128, -128, 127), -128),
            ((-125, 5048, 1115854788, -5, -128, -128, 127), -48),
            ((4381, 10502, 1904650626, -7, -128, -128, 127), -25),
            ((5141, -493, 1279881256, -6, -128, -128, 127), -85),
            ((0, 0, 0, 0, -128, -128, 127), None),
            ((0, 0, 0, 0, -128, -128, 127), None),
            ((0, 0, 0, 0, -128, -128, 127), None),
            ((0, 0, 0, 0, -128, -128, 127), None),

            ((11714, -12447, 1795228372, -7, -5, -128, 127), -10),
            ((12571, -12447, 1795228372, -7, -5, -128, 127), -4),
            ((0, 0, 0, 0, -5, -128, 127), None),
            ((0, 0, 0, 0, -5, -128, 127), None),
            ((0, 0, 0, 0, -5, -128, 127), None),
            ((0, 0, 0, 0, -5, -128, 127), None),

            ((-42127, 22500, 1279992908, -10, -4, -128, 127), -15),
            ((0, 0, 0, 0, -4, -128, 127), None),
            ((0, 0, 0, 0, -4, -128, 127), None),
            ((0, 0, 0, 0, -4, -128, 127), None),
            ((0, 0, 0, 0, -4, -128, 127), None),

            ((-18706, 12439, 1493407068, -9, 10, -128, 127), 1),
            ((0, 0, 0, 0, 10, -128, 127), None),
            ((0, 0, 0, 0, 10, -128, 127), None),
            ((0, 0, 0, 0, 10, -128, 127), None),
            ((0, 0, 0, 0, 10, -128, 127), None),

        ]

        def process():
            # Outputs are delayed by 4 cycles, so put in this data structure
            # with indices shifted by 4
            expected_outputs = [None, None, None, None] + [o for (_, o) in DATA]

            # Iterate through inputs as usual
            for n, (inputs, _) in enumerate(DATA):
                acc, bias, multiplier, shift, offset, activation_min, activation_max = inputs
                yield self.dut.accumulator.eq(acc)
                yield self.dut.bias.eq(bias)
                yield self.dut.multiplier.eq(multiplier)
                yield self.dut.shift.eq(shift)
                yield self.dut.offset.eq(offset)
                yield self.dut.activation_min.eq(activation_min)
                yield self.dut.activation_max .eq(activation_max)
                yield Settle()
                if expected_outputs[n] is not None:
                    self.assertEqual(
                        (yield self.dut.result), expected_outputs[n], f"cycle={n}")
                yield
        self.run_sim(process, False)


class PostProcessXetterTest(TestBase):
    def create_dut(self):
        return PostProcessXetter()

    def test(self):
        DATA = [
            # Small sample to show timing and wiring are correct
            ((5141, -493, 1279881256, -6, -128, -128, 127), -85),
            ((11714, -12447, 1795228372, -7, -5, -128, 127), -10),
            ((-18706, 12439, 1493407068, -9, 10, -128, 127), 1),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                acc, bias, multiplier, shift, offset, activation_min, activation_max = inputs
                yield self.dut.in0.eq(acc)
                yield self.dut.bias.eq(bias)
                yield self.dut.multiplier.eq(multiplier)
                yield self.dut.shift.eq(shift)
                yield self.dut.offset.eq(offset)
                yield self.dut.activation_min.eq(activation_min)
                yield self.dut.activation_max.eq(activation_max)
                yield self.dut.start.eq(1)
                yield
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                self.assertEqual(
                    (yield self.dut.output.as_signed()), expected, f"case={n}")
                yield
        self.run_sim(process, False)
