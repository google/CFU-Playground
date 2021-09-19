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

from nmigen import Mux, Signal, unsigned, signed, Module
from nmigen_cfu import InstructionBase, SimpleElaboratable

from .constants import Constants
from .stream import Endpoint, BinaryPipelineActor

SRDHM_INPUT_LAYOUT = [
    ('a', signed(32)),
    ('b', signed(32)),
]

RDBPOT_INPUT_LAYOUT = [
    ('dividend', signed(32)),
    ('shift', unsigned(4))
]


class SaturatingRoundingDoubleHighMul(BinaryPipelineActor):
    """Performs an SRDHM operation.

    This is approximately a 32x32 mulitiplication where only the high 32
    bits are returned. It actually returns double the value, which is
    possible because both inputs are signed and so the raw result of the
    multiplication is only a 63 bit number.

    Only tested for

    * 'a' in the range +/- (64 * 16 * 128) (i.e 18bits including sign).
      This is the range required for processing 4x4 convs with depths
      up to 64.
    * 'b' in the range 0x4000_0000 to 0x7000_0000 as this appears to be
      the range used the hps model.

    Attributes
    ----------

    input: Stream(SRDHM_INPUT_LAYOUT), in
      The calculation to perform.

    output: Stream(signed(32)), out
      The result.

    This pipeline neither provides nor respects back pressure.
    """
    PIPELINE_CYCLES = 3

    def __init__(self):
        super().__init__(SRDHM_INPUT_LAYOUT, signed(32), self.PIPELINE_CYCLES)

    def transform(self, m, in_value, out_value):
        # Cycle 0: register inputs
        a = in_value.a
        reg_a = Signal(signed(32))
        reg_b = Signal(signed(32))
        m.d.sync += reg_a.eq(Mux(a >= 0, a, -a))
        m.d.sync += reg_b.eq(in_value.b)

        # Cycle 1: multiply to register
        # both operands are positive, so result always positive
        reg_ab = Signal(signed(63))
        m.d.sync += reg_ab.eq(reg_a * reg_b)

        # Cycle 2: nudge, take high bits and sign
        positive_2 = self.delay(m, 2, a >= 0)  # Whether input positive
        nudged = reg_ab + Mux(positive_2, (1 << 30), (1 << 30) - 1)
        high_bits = Signal(signed(32))
        m.d.comb += high_bits.eq(nudged[31:])
        with_sign = Mux(positive_2, high_bits, -high_bits)
        m.d.sync += out_value.eq(with_sign)


class RoundingDivideByPowerOfTwo(BinaryPipelineActor):
    """Divides its input by a power of two, rounding appropriately.

    Attributes
    ----------

    input: Stream(RDBPOT_INPUT_LAYOUT), in
      The calculation to perform.

    output: Stream(signed(32)), out
      The result.

    This pipeline neither provides nor respects back pressure.
    """
    PIPELINE_CYCLES = 3

    def __init__(self):
        super().__init__(RDBPOT_INPUT_LAYOUT, signed(32), self.PIPELINE_CYCLES)

    def transform(self, m, in_value, out_value):
        # Cycle 0: register inputs
        dividend = Signal(signed(32))
        shift = Signal(4)
        m.d.sync += dividend.eq(in_value.dividend)
        m.d.sync += shift.eq(in_value.shift)

        # Cycle 1: calculate
        result = Signal(signed(32))
        remainder = Signal(signed(32))
        threshold = Signal(signed(32))
        quotient = Signal(signed(32))
        rounding = Signal()
        with m.Switch(shift):
            for n in range(3, 12):
                with m.Case(n):
                    mask = (1 << n) - 1
                    m.d.comb += remainder.eq(dividend & mask)
                    m.d.comb += threshold.eq((mask >> 1) +
                                             Mux(dividend < 0, 1, 0))
                    m.d.comb += quotient.eq(dividend >> n)

        m.d.sync += result.eq(quotient + Mux(remainder > threshold, 1, 0))

        # Cycle 2: send output
        m.d.sync += out_value.eq(result)


class MathInstruction(InstructionBase):
    """An instruction used to perform specialist math operations.

    This instruction is likely to be replaced with more comprehensive
    gateware in future.

    Attributes
    ----------

    None additional.
    """

    def elab(self, m: Module):
        m.submodules.srdhm = srdhm = SaturatingRoundingDoubleHighMul()
        m.d.comb += srdhm.output.ready.eq(1)
        m.submodules.rdbpot = rdbpot = RoundingDivideByPowerOfTwo()
        m.d.comb += rdbpot.output.ready.eq(1)

        m.d.sync += self.done.eq(0)
        with m.FSM(reset="WAIT_START"):
            with m.State("WAIT_START"):
                with m.If(self.start):
                    with m.Switch(self.funct7):
                        with m.Case(Constants.MATH_SRDHM):
                            m.d.comb += [
                                srdhm.input.payload.a.eq(self.in0s),
                                srdhm.input.payload.b.eq(self.in1s),
                                srdhm.input.valid.eq(1),
                            ]
                            m.next = "SRDHM_RUN"
                        with m.Case(Constants.MATH_RDBPOT):
                            m.d.comb += [
                                rdbpot.input.payload.dividend.eq(self.in0s),
                                rdbpot.input.payload.shift.eq(-self.in1s),
                                rdbpot.input.valid.eq(1),
                            ]
                            m.next = "RDBPOT_RUN"
                        with m.Default():
                            m.d.sync += self.done.eq(1)
            with m.State("SRDHM_RUN"):
                with m.If(srdhm.output.valid):
                    m.d.sync += self.output.eq(srdhm.output.payload)
                    m.d.sync += self.done.eq(1)
                    m.next = "WAIT_START"
            with m.State("RDBPOT_RUN"):
                with m.If(rdbpot.output.valid):
                    m.d.sync += self.output.eq(rdbpot.output.payload)
                    m.d.sync += self.done.eq(1)
                    m.next = "WAIT_START"
