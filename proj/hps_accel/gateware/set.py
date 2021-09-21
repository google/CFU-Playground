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
from nmigen_cfu import InstructionBase, SimpleElaboratable

from .constants import Constants
from .stream import Endpoint, connect


class ConfigurationRegister(SimpleElaboratable):
    """A register set by the CPU.

    Allows a CPU to provide data to gateware.

    Attributes
    ----------

    output: Endpoint(unsigned(32))
      An output stream of values. A new value onto the stream whenever
      the register is set.

    value: unsigned(32), out
      The value held by the register.

    new_en: Signal(1), in
      Indicates to register that a new value is being presented on new_value

    new_value: unsigned(32), in
      New value for the register. Read when "set" is asserted.
    """

    def __init__(self):
        super().__init__()
        self.output = Endpoint(unsigned(32))
        self.value = self.output.payload
        self.new_en = Signal()
        self.new_value = Signal(32)

    def elab(self, m):
        with m.If(self.output.is_transferring()):
            m.d.sync += self.output.valid.eq(0)

        with m.If(self.new_en):
            m.d.sync += self.value.eq(self.new_value)
            m.d.sync += self.output.valid.eq(1)


class SetInstruction(InstructionBase):
    """An instruction used to set values into a register of the CFU.

    Sets a configuration register from in0.

    Attributes
    ----------

    output_streams: dict[id, Endpoint[unsigned(32)]], out
      Value output for each register.

    values: dict[id, unsigned(32)], out
      Values as set into registers.

    write_strobes: dict[id, Signal(1)], out
      Asserted for one cycle when the corresponding register id is written.
    """

    # The list of all register IDs that may be set
    REGISTER_IDS = [
        Constants.REG_FILTER_NUM_WORDS,
        Constants.REG_INPUT_NUM_WORDS,
        Constants.REG_INPUT_OFFSET,
        Constants.REG_SET_FILTER,
        Constants.REG_SET_INPUT,
        Constants.REG_OUTPUT_OFFSET,
        Constants.REG_OUTPUT_MIN,
        Constants.REG_OUTPUT_MAX,
        Constants.REG_FILTER_INPUT_NEXT,
        Constants.REG_VERIFY,
        Constants.REG_OUTPUT_PARAMS_RESET,
        Constants.REG_OUTPUT_BIAS,
        Constants.REG_OUTPUT_MULTIPLIER,
        Constants.REG_OUTPUT_SHIFT,
    ]

    def __init__(self):
        super().__init__()
        self.output_streams = {
            i: Endpoint(
                unsigned(32)) for i in self.REGISTER_IDS}
        self.values = {i: Signal(32) for i in self.REGISTER_IDS}
        self.write_strobes = {i: Signal(1) for i in self.REGISTER_IDS}

    def elab(self, m: Module):
        registers = {i: ConfigurationRegister() for i in self.REGISTER_IDS}
        for i, register in registers.items():
            m.submodules[f"reg_{i:02x}"] = register
            m.d.comb += connect(register.output, self.output_streams[i])
            m.d.comb += self.values[i].eq(register.value)
            m.d.comb += self.write_strobes[i].eq(0)  # strobes off by default

        with m.If(self.start):
            # Consider making self.done.eq(1) combinatorial
            m.d.sync += self.done.eq(1)
            with m.Switch(self.funct7):
                for i, register in registers.items():
                    with m.Case(i):
                        m.d.comb += register.new_en.eq(1)
                        m.d.comb += register.new_value.eq(self.in0)
                        m.d.comb += self.write_strobes[i].eq(1)
        with m.Else():
            m.d.sync += self.done.eq(0)
