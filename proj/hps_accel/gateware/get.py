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

from nmigen import unsigned, Signal
from nmigen.hdl.dsl import Module
from nmigen_cfu import InstructionBase
from util import SimpleElaboratable
from .constants import Constants
from .stream import Sink, Source, glue_sinks


class StatusRegister(SimpleElaboratable):
    """A register set by gateware.

    Allows gateware to provide data to a CPU

    Attributes
    ----------

    sink: Sink(unsigned(32)), in
      A sink for new values. "ready" is always asserted because the
      register is always ready to receive new data.

    value: unsigned(32), out
      The value held by the register. Received from sink.payload.

    """

    def __init__(self):
        super().__init__()
        self.sink = Sink(unsigned(32))
        self.value = Signal(32)

    def elab(self, m):
        m.d.comb += self.sink.ready.eq(1)
        with m.If(self.sink.is_transferring()):
            m.d.sync += self.value.eq(self.sink.payload)


class GetInstruction(InstructionBase):
    """An instruction used by CPU to get values from the CFU.

    Returns current value of each register

    Attributes
    ----------

    sinks: dict[id, Sink[unsigned(32)]], in
      Value sinks for each register.

    read_strobes: dict[id, Signal(1)], out
      Asserted for one cycle when the corresponding register id is read.
    """

    # The list of all register IDs that may be fetched
    REGISTER_IDS = [Constants.REG_MACC_OUT, Constants.REG_VERIFY]

    def __init__(self):
        super().__init__()
        self.sinks = {i: Sink(unsigned(32), name=f"sink_{i:02x}")
                      for i in self.REGISTER_IDS}
        self.read_strobes = {i: Signal() for i in self.REGISTER_IDS}

    def elab(self, m: Module):
        # Make registers and plumb sinks and read_strobes through
        registers = {i: StatusRegister() for i in self.REGISTER_IDS}
        for i, register in registers.items():
            m.submodules[f"reg_{i:02x}"] = register
            m.d.comb += glue_sinks(self.sinks[i], register.sink)

        # By default, all strobes off, and not done
        m.d.sync += [s.eq(0) for s in self.read_strobes.values()]
        m.d.sync += self.done.eq(0)
        with m.If(self.start):
            m.d.sync += self.done.eq(1)
            with m.Switch(self.funct7):
                for i, register in registers.items():
                    with m.Case(i):
                        m.d.sync += self.output.eq(registers[i].value)
                        m.d.sync += self.read_strobes[i].eq(1)
                with m.Default():
                    m.d.sync += self.output.eq(0)
