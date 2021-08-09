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

from nmigen import Signal, unsigned
from nmigen.hdl.dsl import Module
from nmigen_cfu import InstructionBase
from util import SimpleElaboratable

from .constants import Constants
from .stream import Sink, Source, glue_sources


class ConfigurationRegister(SimpleElaboratable):
    """A register set by the CPU.

    Allows a CPU to provide data to gateware.

    Attributes
    ----------

    source: Source(unsigned(32))
      A source of values. Asserts "valid" whenever a new value is set into
      the register and deasserts "valid" after "ready" is also asserted.
      Will continue to present the value of the register as the source payload
      after the read.

    value: unsigned(32), out
      The value held by the register. Alias for source.payload.

    new_en: Signal(1), in
      Indicates to register that a new value is being presented on new_value

    new_value: unsigned(32), in
      New value for the register. Read when "set" is asserted.
    """

    def __init__(self):
        super().__init__()
        self.source = Source(unsigned(32))
        self.value = self.source.payload
        self.new_en = Signal()
        self.new_value = Signal(32)

    def elab(self, m):
        with m.If(self.source.is_transferring()):
            m.d.sync += self.source.valid.eq(0)

        with m.If(self.new_en):
            m.d.sync += self.value.eq(self.new_value)
            m.d.sync += self.source.valid.eq(1)


class SetInstruction(InstructionBase):
    """An instruction used to set values into a register of the CFU.

    Sets a configuration register from in0.

    Attributes
    ----------

    sources: dict[id, Source[unsigned(32)]], out
      Value sources for each register.
    values: dict[id, unsigned(32)], out
      Values as set into registers.
    """

    # The list of all register IDs that may be set
    REGISTER_IDS = [
        Constants.REG_INPUT_NUM_WORDS,
        Constants.REG_INPUT_OFFSET,
        Constants.REG_SET_INPUT,
        Constants.REG_MACC_INPUT_0,
        Constants.REG_MACC_INPUT_1,
        Constants.REG_MACC_INPUT_2,
        Constants.REG_MACC_INPUT_3,
        Constants.REG_MACC_FILTER_0,
        Constants.REG_MACC_FILTER_1,
        Constants.REG_MACC_FILTER_2,
        Constants.REG_MACC_FILTER_3,
        Constants.REG_VERIFY]

    def __init__(self):
        super().__init__()
        self.sources = {i: Source(unsigned(32)) for i in self.REGISTER_IDS}
        self.values = {i: Signal(32) for i in self.REGISTER_IDS}

    def elab(self, m: Module):
        registers = {i: ConfigurationRegister() for i in self.REGISTER_IDS}
        for i, register in registers.items():
            m.submodules[f"reg_{i:02x}"] = register
            m.d.comb += glue_sources(register.source, self.sources[i])
            m.d.comb += self.values[i].eq(register.value)

        with m.If(self.start):
            m.d.sync += self.done.eq(1)
            with m.Switch(self.funct7):
                for i, register in registers.items():
                    with m.Case(i):
                        m.d.comb += register.new_en.eq(1)
                        m.d.comb += register.new_value.eq(self.in0)
        with m.Else():
            m.d.sync += self.done.eq(0)
