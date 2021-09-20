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
from .post_process import SaturatingRoundingDoubleHighMul, RoundingDivideByPowerOfTwo
from .stream import Endpoint, BinaryPipelineActor



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
