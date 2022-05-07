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
from amaranth_cfu import TestBase, SimpleElaboratable, pack_vals, simple_cfu, InstructionBase, CfuTestBase
import unittest


class MultiplyAccumulate4(SimpleElaboratable):
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


class MultiplyAccumulate4Test(TestBase):
    def create_dut(self):
        return MultiplyAccumulate4()

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

            # Interesting bug
            ((a(128, 0, 0, 0), b(-104, 0, 0, 0), 1, 0), 0),
            ((a(0, 51, 0, 0), b(0, 43, 0, 0), 1, 0), -13312),
            ((a(0, 0, 97, 0), b(0, 0, -82, 0), 1, 0), -11119),
            ((a(0, 0, 0, 156), b(0, 0, 0, -83), 1, 0), -19073),
            ((a(0, 0, 0, 0), b(0, 0, 0, 0), 1, 0), -32021),
        ]

        dut = self.dut

        def process():
            for (a_word, b_word, enable, clear), expected in DATA:
                yield dut.a_word.eq(a_word)
                yield dut.b_word.eq(b_word)
                yield dut.enable.eq(enable)
                yield dut.clear.eq(clear)
                yield Delay(0.1)  # Wait for input values to settle

                # Check on accumulator, as calcuated last cycle
                self.assertEqual(expected, (yield dut.accumulator))
                yield Tick()

        self.run_sim(process, write_trace=False)


class Macc4Instruction(InstructionBase):
    """Simple instruction that provides access to a Macc4

    The supported functions are:
        * 0: Reset accumulator
        * 1: 4-way multiply accumulate.
        * 2: Read accumulator
    """

    def elab(self, m):
        # Build the submodule
        m.submodules.macc4 = macc4 = MultiplyAccumulate4()

        # Inputs to the macc4
        m.d.comb += macc4.a_word.eq(self.in0)
        m.d.comb += macc4.b_word.eq(self.in1)

        # Only function 2 has a defined response, so we can
        # unconditionally set it.
        m.d.comb += self.output.eq(macc4.accumulator)

        with m.If(self.start):
            m.d.comb += [
                # We can always return control to the CPU on next cycle
                self.done.eq(1),

                # clear on function 0, enable on function 1
                macc4.clear.eq(self.funct7 == 0),
                macc4.enable.eq(self.funct7 == 1),
            ]


def make_cfu():
    return simple_cfu({0: Macc4Instruction()})


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        "Tests CFU plumbs to Madd4 correctly"
        def a(a, b, c, d): return pack_vals(a, b, c, d, offset=-128)
        def b(a, b, c, d): return pack_vals(a, b, c, d, offset=0)
        # These values were calculated with a spreadsheet
        DATA = [
            # ((fn3, fn7, op1, op2), result)
            ((0, 0, 0, 0), None),  # reset
            ((0, 1, a(130, 7, 76, 47), b(104, -14, -24, 71)), None),  # calculate
            ((0, 1, a(84, 90, 36, 191), b(109, 57, -50, -1)), None),
            ((0, 1, a(203, 246, 89, 178), b(-87, 26, 77, 71)), None),
            ((0, 1, a(43, 27, 78, 167), b(-24, -8, 65, 124)), None),
            ((0, 2, 0, 0), 59986),  # read result

            ((0, 0, 0, 0), None),  # reset
            ((0, 1, a(67, 81, 184, 130), b(81, 38, -116, 65)), None),
            ((0, 1, a(208, 175, 180, 198), b(-120, -70, 8, 11)), None),
            ((0, 1, a(185, 81, 101, 108), b(90, 6, -92, 83)), None),
            ((0, 1, a(219, 216, 114, 236), b(-116, -9, -109, -16)), None),
            ((0, 2, 0, 0), -64723),  # read result

            ((0, 0, 0, 0), None),  # reset
            ((0, 1, a(128, 0, 0, 0), b(-104, 0, 0, 0)), None),
            ((0, 1, a(0, 51, 0, 0),  b(0, 43, 0, 0)), None),
            ((0, 1, a(0, 0, 97, 0),  b(0, 0, -82, 0)), None),
            ((0, 1, a(0, 0, 0, 156), b(0, 0, 0, -83)), None),
            ((0, 2, a(0, 0, 0, 0),   b(0, 0, 0, 0)), -32021),
        ]
        self.run_ops(DATA)


if __name__ == '__main__':
    unittest.main()
