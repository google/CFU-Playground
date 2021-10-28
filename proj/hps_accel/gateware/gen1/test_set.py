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

from .constants import Constants
from .set import ConfigurationRegister, SetInstruction


class ConfigurationRegisterTest(TestBase):
    def create_dut(self):
        return ConfigurationRegister()

    def test(self):
        DATA = [
            # (new_en, new_value, ready) (valid, value)
            ((0, 0, 0), (0, 0)),
            ((0, 10, 0), (0, 0)),
            # set value 20, check valid deasserts on ready
            ((1, 20, 0), (0, 0)),
            ((0, 30, 0), (1, 20)),
            ((0, 30, 0), (1, 20)),
            ((0, 30, 1), (1, 20)),
            ((0, 30, 0), (0, 20)),
            # new_en asserted for multiple cycles
            ((1, 30, 0), (0, 20)),
            ((1, 30, 0), (1, 30)),
            ((1, 30, 1), (1, 30)),
            ((0, 40, 0), (1, 30)),
            ((0, 40, 1), (1, 30)),
            ((0, 40, 0), (0, 30)),
            # ready asserted for multiple cycles
            ((0, 40, 1), (0, 30)),
            ((0, 40, 1), (0, 30)),
            ((0, 40, 0), (0, 30)),
            ((1, 50, 0), (0, 30)),
            ((0, 50, 1), (1, 50)),
            ((0, 50, 1), (0, 50)),
            ((0, 50, 0), (0, 50)),
            ((0, 50, 0), (0, 50)),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                with self.subTest(n=n, inputs=inputs, expected=expected):
                    new_en, new_value, ready = inputs
                    yield self.dut.new_en.eq(new_en)
                    yield self.dut.new_value.eq(new_value)
                    yield self.dut.output.ready.eq(ready)
                    yield Delay(0.25)
                    valid, value = expected
                    self.assertEqual((yield self.dut.output.valid), valid)
                    self.assertEqual((yield self.dut.value), value)
                    if valid:
                        self.assertEqual((yield self.dut.output.payload), value)
                    yield
        self.run_sim(process, False)


class SetInstructionTest(TestBase):
    def create_dut(self):
        return SetInstruction()

    def test(self):
        VER = Constants.REG_VERIFY
        INV = Constants.REG_INVALID
        DATA = [
            # (funct7, in0, in1), (verify register value)
            ((INV, 0, 0), 0),
            ((VER, 10, 20), 10),
            ((INV, 0, 0), 10),
            ((VER, 99, 200), 99),
            ((INV, 55, 44), 99),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                with self.subTest(n=n, inputs=inputs, expected=expected):
                    funct7, in0, in1 = inputs
                    yield self.dut.funct7.eq(funct7)
                    yield self.dut.in0.eq(in0)
                    yield self.dut.in1.eq(in1)
                    yield self.dut.start.eq(1)
                    yield
                    yield self.dut.start.eq(0)
                    while not (yield self.dut.done):
                        yield
                    yield # one cycle to let verify value flow through
                    self.assertEqual((yield self.dut.values[VER]), expected)
                    yield
        self.run_sim(process, False)

    def test_write_strobe(self):
        VER = Constants.REG_VERIFY
        def process():
            yield self.dut.funct7.eq(VER)
            yield self.dut.in0.eq(123)
            yield self.dut.in1.eq(456)
            yield self.dut.start.eq(1)
            yield
            self.assertEqual((yield self.dut.write_strobes[VER]), 1)
            yield self.dut.start.eq(0)
            yield
            self.assertEqual((yield self.dut.write_strobes[VER]), 0)
        self.run_sim(process, False)
