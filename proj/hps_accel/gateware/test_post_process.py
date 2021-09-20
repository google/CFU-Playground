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

import random

from nmigen.sim import Delay
from nmigen_cfu import TestBase

from .post_process import (OutputParamsStorage, SaturateActivationPipeline,
                           PostProcessPipeline)

SETTLE_DELAY = Delay(0.25)


class OutputParamsStorageTest(TestBase):
    def create_dut(self):
        return OutputParamsStorage()

    def set_write_data(self, seed):
        """Given a seed, randomly set write_data"""
        random.seed(seed)
        data = self.dut.write_data
        yield data.bias.eq(random.randrange(-(2**15), 2**15))
        yield data.multiplier.eq(random.randrange(0x4000_0000, 0x8000_0000))
        yield data.shift.eq(random.randrange(4, 11))

    def write(self, seed):
        yield from self.set_write_data(seed)
        yield self.dut.write_enable.eq(1)
        yield
        yield self.dut.write_enable.eq(0)
        yield

    def check_read_data(self, seed):
        """Given a seed, check that it matches record generated from same seeed"""
        random.seed(seed)
        data = self.dut.read_data
        self.assertEqual((yield data.bias), random.randrange(-(2**15), 2**15))
        self.assertEqual((yield data.multiplier), random.randrange(0x4000_0000, 0x8000_0000))
        self.assertEqual((yield data.shift), random.randrange(4, 11))

    def check_read(self, seed):
        yield self.dut.read_enable.eq(1)
        yield
        yield self.dut.read_enable.eq(0)
        yield
        yield from self.check_read_data(seed)

    def test_it_works(self):
        """Set 8 numbers and read them back"""
        def process():
            for n in range(8):
                yield from self.write(n)
            for n in range(8):
                yield from self.check_read(n)
        self.run_sim(process, False)

    def test_it_reads_multiple_times(self):
        """Set 16 numbers and read them back many times"""
        def process():
            for n in range(8, 24):
                yield from self.write(n)
            for n in range(8, 24):
                yield from self.check_read(n)
            for n in range(8, 24):
                yield from self.check_read(n)
            for n in range(8, 24):
                yield from self.check_read(n)
        self.run_sim(process, False)

    def test_it_can_be_reset(self):
        """Show store can be reset and reused."""
        def process():
            for n in range(20, 28):
                yield from self.write(n)
            for n in range(20, 28):
                yield from self.check_read(n)

            yield self.dut.reset.eq(1)
            yield
            yield self.dut.reset.eq(0)
            yield

            for n in range(120, 128):
                yield from self.write(n)
            for n in range(120, 128):
                yield from self.check_read(n)
        self.run_sim(process, False)


class SaturateActivationPipelineTest(TestBase):
    """Tests the SaturateActivationPipeline"""

    def create_dut(self):
        return SaturateActivationPipeline()

    def test_it_works(self):
        """Show store can be reset and reused."""
        TEST_CASES = [
            # (offset, min, max, input), expected result
            ((0, 0, 0, 0), 0),
            ((-128, -128, 127, 0), -128),
            ((-128, -128, 127, 10), -118),
            ((-128, -128, 127, -50), -128),
            ((-128, -128, 127, 500), 127),
        ]

        def process():
            yield self.dut.output.ready.eq(1)
            for (offset, min, max, input_), expected in TEST_CASES:
                yield self.dut.offset.eq(offset)
                yield self.dut.min.eq(min)
                yield self.dut.max.eq(max)
                yield
                yield self.dut.input.payload.eq(input_)
                yield self.dut.input.valid.eq(1)
                yield
                yield self.dut.input.valid.eq(0)
                while not (yield self.dut.output.valid):
                    yield
                self.assertEqual((yield self.dut.output.payload), expected)
        self.run_sim(process, False)


class PostProcessPipelineTest(TestBase):
    """Tests the entire post process pipeline"""

    def create_dut(self):
        return PostProcessPipeline()

    def test_it_works(self):
        TEST_CASES = [
            # ((acc_in,bias,multiplier,shift), expected)
            ((-15150, 2598, 1170510491, 8), -128),
            ((-432, 2193, 2082838296, 9), -125),
            ((37233, -18945, 1368877765, 9), -105),
            ((-294, 1851, 1661334583, 8), -123),
            ((3908, 1994, 1384690194, 8), -113),
            ((153, 1467, 1177612918, 8), -125),
        ]

        def process():
            yield self.dut.output.ready.eq(1)
            yield self.dut.offset.eq(-128)
            yield self.dut.activation_min.eq(-128)
            yield self.dut.activation_max.eq(127)
            yield
            for (acc_in, bias, multiplier, shift), expected in TEST_CASES:
                self.assertEqual((yield self.dut.read_strobe), 0)
                yield self.dut.read_data.bias.eq(bias)
                yield self.dut.read_data.multiplier.eq(multiplier)
                yield self.dut.read_data.shift.eq(shift)
                yield self.dut.input.payload.eq(acc_in)
                yield self.dut.input.valid.eq(1)
                yield
                self.assertEqual((yield self.dut.read_strobe), 1)
                yield self.dut.input.valid.eq(0)
                while not (yield self.dut.output.valid):
                    yield
                self.assertEqual((yield self.dut.output.payload), expected)
        self.run_sim(process, False)
