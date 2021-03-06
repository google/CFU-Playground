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

from cfu import InstructionBase
from nmigen_cfu import Mux, Signal, signed

from nmigen_cfu import SimpleElaboratable


INT32_MIN = 0x8000_0000
INT32_MAX = 0x7fff_ffff


class SRDHM(SimpleElaboratable):
    """Implements gemmlowp::SaturatingRoundingDoublingHighMul

    It multiplies two 32 bit numbers, then returns bits 62 to 31 of the
    64 bit result. This is 2x the high word (allowing for saturating and
    rounding).

    Implemented as a pipeline so that results are always available 3
    cycles after setting inputs.

    Note that there is a bug to investigated here. This implementation
    matches the behavior of the compiled source, however, "nudge" may be
    one of two values.

    Public Interface
    ----------------
      a: Signal(signed(32)) input
        First operand
      b: Signal(signed(32)) input
        Second operand
      result: Signal(signed(32)) output
        The result of a*b
    """

    def __init__(self):
        self.a = Signal(signed(32))
        self.b = Signal(signed(32))
        self.result = Signal(signed(32))

    def elab(self, m):
        areg = Signal.like(self.a)
        breg = Signal.like(self.b)
        ab = Signal(signed(64))
        overflow = Signal()

        # for some reason negative nudge is not used
        nudge = 1 << 30

        # cycle 0, register a and b
        m.d.sync += [
            areg.eq(self.a),
            breg.eq(self.b),
        ]
        # cycle 1, decide if this is an overflow and multiply
        m.d.sync += [
            overflow.eq((areg == INT32_MIN) & (breg == INT32_MIN)),
            ab.eq(areg * breg),
        ]
        # cycle 2, apply nudge determine result
        m.d.sync += [
            self.result.eq(Mux(overflow, INT32_MAX, (ab + nudge)[31:])),
        ]


class SRDHMInstruction(InstructionBase):
    def elab(self, m):
        m.submodules['srdhm'] = srdhm = SRDHM()
        countdown = Signal(signed(3))
        m.d.comb += self.done.eq(countdown == 0)

        m.d.comb += [
            srdhm.a.eq(self.in0),
            srdhm.b.eq(self.in1),
            self.output.eq(srdhm.result),
        ]
        with m.If(self.start):
            m.d.sync += countdown.eq(2)
        with m.Else():
            m.d.sync += countdown.eq(Mux(countdown != -1, countdown - 1, -1))


def rounding_divide_by_pot(x, exponent):
    """Implements gemmlowp::RoundingDivideByPOT

    This divides by a power of two, rounding to the nearest whole number.
    """
    mask = (1 << exponent) - 1
    remainder = x & mask
    threshold = (mask >> 1) + x[31]
    rounding = Mux(remainder > threshold, 1, 0)
    return (x >> exponent) + rounding


class RoundingDividebyPOTInstruction(InstructionBase):
    def elab(self, m):
        m.d.comb += [
            self.output.eq(rounding_divide_by_pot(self.in0s, self.in1[:5])),
            self.done.eq(1),
        ]
