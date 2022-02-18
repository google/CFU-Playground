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
from amaranth import Mux, Signal, signed
from amaranth_cfu import SimpleElaboratable, TestBase
from amaranth.sim import Settle
import unittest


class ValueBuffer(SimpleElaboratable):
    """Buffers a signal.

    Parameters:
        inp: A Signal
            The signal to buffer

    Interface:
        capture: Signal()
            Input.
            When high, captures input while transparently placing on output.
            When low, output is equal to last captured input.
        output: Signal(like inp)
            Output. The last captured input.
    """

    def __init__(self, inp):
        self.capture = Signal()
        self.input = inp
        self.output = Signal.like(inp)

    def elab(self, m):
        captured = Signal.like(self.input)
        with m.If(self.capture):
            m.d.sync += captured.eq(self.input)
        m.d.comb += self.output.eq(Mux(self.capture, self.input, captured))


class ValueBufferTest(TestBase):
    def create_dut(self):
        self.in_signal = Signal(4)
        return ValueBuffer(self.in_signal)

    def test(self):
        DATA = [
            ((0, 0), 0),
            ((1, 5), 5),
            ((0, 3), 5),
            ((0, 2), 5),
            ((0, 2), 5),
            ((1, 2), 2),
            ((0, 2), 2),
            ((0, 2), 2),
        ]

        def process():
            for n, ((capture, in_sig), expected_output) in enumerate(DATA):
                yield self.in_signal.eq(in_sig)
                yield self.dut.capture.eq(capture)
                yield Settle()
                self.assertEqual((yield self.dut.output), expected_output, f"cycle={n}")
                yield
        self.run_sim(process, False)

if __name__ == '__main__':
    unittest.main()
