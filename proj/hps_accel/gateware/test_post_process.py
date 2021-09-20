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

from .post_process import OutputParamsStorage, SaturateActivationPipeline

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
    def create_dut(self):
        return SaturateActivationPipeline        ()

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

