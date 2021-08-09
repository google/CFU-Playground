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
from .get import StatusRegister, GetInstruction


class StatusRegisterTest(TestBase):
    def create_dut(self):
        return StatusRegister()

    def test(self):
        DATA = [
            # (valid, payload), value
            ((0, 0), 0),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                with self.subTest(n=n, inputs=inputs, expected=expected):
                    valid, payload = inputs
                    yield self.dut.sink.valid.eq(valid)
                    yield self.dut.sink.payload.eq(payload)
                    yield Delay(0.25)
                    self.assertEqual((yield self.dut.value), expected)
                    yield
        self.run_sim(process, False)


class GetInstructionTest(TestBase):
    def create_dut(self):
        dut = GetInstruction()
        return dut

    def test(self):
        VER = Constants.REG_VERIFY
        INV = Constants.REG_INVALID
        DATA = [
            # (funct7, valid, payload), (output, read_strobe)
            ((INV, 0, 0), (0, 0)),
            ((INV, 1, 22), (0, 0)),
            ((INV, 0, 22), (0, 0)),
            ((VER, 0, 22), (22, 1)),
            ((INV, 1, 44), (0, 0)),
            ((INV, 0, 0), (0, 0)),
            ((INV, 0, 0), (0, 0)),
            ((VER, 0, 0), (44, 1)),
        ]

        def process():
            ver_sink = self.dut.sinks[VER]
            for n, (inputs, expected) in enumerate(DATA):
                #print(f"{n=}, {inputs=}, {expected=}")
                funct7, valid, payload = inputs
                yield self.dut.funct7.eq(funct7)
                yield ver_sink.valid.eq(valid)
                yield ver_sink.payload.eq(payload)
                yield self.dut.start.eq(1)
                yield
                yield ver_sink.valid.eq(0)
                yield self.dut.start.eq(0)
                while not (yield self.dut.done):
                    yield
                output, strobe = expected
                self.assertEqual((yield self.dut.output), output)
                self.assertEqual((yield self.dut.read_strobes[VER]), strobe)
                yield
        self.run_sim(process, False)

    def test_invalidate(self):
        # Tests behavior of invalidate signal
        def toggle(sig):
            yield sig.eq(1)
            yield
            yield sig.eq(0)

        def start(f7):
            yield self.dut.funct7.eq(f7)
            yield from toggle(self.dut.start)
            yield self.dut.funct7.eq(0)

        def send_sink(sink, payload):
            yield sink.payload.eq(payload)
            yield from toggle(sink.valid)

        def process():
            ver_sink = self.dut.sinks[Constants.REG_VERIFY]
            invalidate = self.dut.invalidates[Constants.REG_VERIFY]

            # send a value, start an instruction and read it immediately
            yield from send_sink(ver_sink, 1111)
            yield from start(Constants.REG_VERIFY)
            yield
            self.assertTrue((yield self.dut.done))
            self.assertEqual((yield self.dut.output), 1111)

            # mark invalid, start a get and ensure is not done until a
            # value is sent to the sink
            yield from toggle(invalidate)
            yield
            yield from start(Constants.REG_VERIFY)
            yield
            for _ in range(5):
                self.assertFalse((yield self.dut.done))
                yield
            yield from send_sink(ver_sink, 2222)
            self.assertFalse((yield self.dut.done))
            yield
            self.assertFalse((yield self.dut.done))
            yield
            self.assertTrue((yield self.dut.done))
            self.assertEqual((yield self.dut.output), 2222)

            # Next read should succeed immediately
            yield from start(Constants.REG_VERIFY)
            yield
            self.assertTrue((yield self.dut.done))
            self.assertEqual((yield self.dut.output), 2222)

        self.run_sim(process, False)