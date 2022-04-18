#!/bin/env python
# Copyright 2020 Google LLC
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

from amaranth import *
from amaranth.sim import Delay, Tick
from amaranth_cfu import TestBase, SimpleElaboratable, pack_vals
import unittest

class MultiplyAdd4(SimpleElaboratable):
    """Performs four, 8 bit wide multiply-accumulates in parallel.

    Uses `SimpleElaboratable` helper class as a convenience.
    """
    def __init__(self):
        # "a" and "b" inputs - each four, 8 bit signed numbers
        self.a_word = Signal(32)
        self.b_word = Signal(32)

        # clear to reset accumulator, enable to perform multiply- accumulate
        self.clear = Signal()
        self.enable = Signal()

        # result
        self.accumulator = Signal(signed(32))

    def elab(self, m):
        """The actual gateware produced"""

        # Divide a_word and b_word each into four, 8-bit parts
        a_bytes = [self.a_word[i:i+8].as_signed() for i in range(0, 32, 8)]
        b_bytes = [self.b_word[i:i+8].as_signed() for i in range(0, 32, 8)]

        # Calculate the sum of (a+offset)*b for each part
        calculations = [(a + Const(128)) * b for a, b in zip(a_bytes, b_bytes)]
        summed = Signal(signed(32))
        m.d.comb += summed.eq(sum(calculations))
            
        with m.If(self.clear):
            m.d.sync += self.accumulator.eq(0)
        with m.Elif(self.enable):
            m.d.sync += self.accumulator.eq(self.accumulator + summed)


class MultiplyAdd4Test(TestBase):
    def create_dut(self):
        return MultiplyAdd4()

    def test(self):

        def a(a, b, c, d): return pack_vals(a, b, c, d, offset=-128)
        def b(a, b, c, d): return pack_vals(a, b, c, d, offset=0)
        DATA = [
            # (a_word, b_word, enable, clear), expected accumulator
            ((a(0, 0, 0, 0),  b(0, 0, 0, 0), 0, 0), 0),

            # Simple tests: with just first byte
            ((a(10, 0, 0, 0), b(3, 0, 0, 0),  1, 0),   0),
            ((a(11, 0, 0, 0), b(-4, 0, 0, 0), 1, 0),  30),
            ((a(11, 0, 0, 0), b(-4, 0, 0, 0), 0, 0), -14),
            # Since was not enabled last cycle, accumulator will not change
            ((a(11, 0, 0, 0), b(-4, 0, 0, 0), 1, 0), -14),
            # Since was enabled last cycle, will change accumlator
            ((a(11, 0, 0, 0), b(-4, 0, 0, 0), 0, 1), -58),
            # Accumulator cleared
            ((a(11, 0, 0, 0), b(-4, 0, 0, 0), 0, 0),  0),

            # Uses all bytes (calculated on a spreadsheet)
            ((a(99, 22, 2, 1),      b(-2, 6, 7, 111), 1, 0),             0),
            ((a(2, 45, 79, 22),     b(-33, 6, -97, -22), 1, 0),         59),
            ((a(23, 34, 45, 56),    b(-128, -121, 119, 117), 1, 0),  -7884),
            ((a(188, 34, 236, 246), b(-87, 56, 52, -117), 1, 0),     -3035),
            ((a(131, 92, 21, 83),   b(-114, -72, -31, -44), 1, 0),  -33997),
            ((a(74, 68, 170, 39),   b(102, 12, 53, -128), 1, 0),    -59858),
            ((a(16, 63, 1, 198),    b(29, 36, 106, 62), 1, 0),      -47476),
            ((a(0, 0, 0, 0),        b(0, 0, 0, 0), 0, 1),           -32362),        
        ]

        dut = self.dut

        def process():
            for (a_word, b_word, enable, clear), expected in DATA:
                yield dut.a_word.eq(a_word)
                yield dut.b_word.eq(b_word)
                yield dut.enable.eq(enable)
                yield dut.clear.eq(clear)
                yield Delay(0.1) # Wait for input values to settle

                # Check on accumulator, as calcuated last cycle
                self.assertEqual(expected, (yield dut.accumulator))
                yield Tick()

        self.run_sim(process, write_trace=False)

if __name__ == '__main__':
    unittest.main()
