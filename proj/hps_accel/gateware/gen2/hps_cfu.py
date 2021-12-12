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

from nmigen import Signal
from nmigen_cfu import Cfu, InstructionBase

from .constants import Constants


class PingInstruction(InstructionBase):
    """An instruction used to verify simple CFU functionality.

    Adds the two arguments and stores the result. The previously stored value
    is returned.
    """

    def elab(self, m):
        stored_value = Signal(32)
        with m.If(self.start):
            m.d.sync += [
                stored_value.eq(self.in0 + self.in1),
                self.output.eq(stored_value),
                self.done.eq(1),
            ]
        with m.Else():
            m.d.sync += self.done.eq(0)


class GetInstruction(InstructionBase):
    """Handles sending values from CFU to CPU.

    Attributes
    ----------

    reg_verify_value: Signal(32), in
       The value to return for the verify register.
    """

    def __init__(self):
        super().__init__()
        self.reg_verify_value = Signal(32)

    def elab(self, m):
        # Currently only implements REG_VERIFY
        m.d.sync += self.done.eq(0)
        with m.If(self.start):
            m.d.sync += self.output.eq(self.reg_verify_value)
            m.d.sync += self.done.eq(1)


class SetInstruction(InstructionBase):
    """Handles sending values from CPU to CFU

    Attributes
    ----------

    reg_verify_value: Signal(32), out
       The value last set into the verify register
    """

    def __init__(self):
        super().__init__()
        self.reg_verify_value = Signal(32)

    def elab(self, m):
        # Currently only implements REG_VERIFY
        m.d.sync += self.done.eq(self.start)
        with m.If(self.start):
            m.d.sync += self.reg_verify_value.eq(self.in0)
            m.d.sync += self.done.eq(1)


class MemoryReadInstruction(InstructionBase):
    """Reads arena memory via 2nd LRAM port.

    Validates that memory ports are correctly passed through.

    Attributes
    ----------

    lram_addr: [Signal(14)] * 4, out
        Address for each LRAM bank

    lram_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.
    """

    def __init__(self):
        super().__init__()
        self.lram_addr = [Signal(32, name=f'addr{i}') for i in range(4)]
        self.lram_data = [Signal(32, name=f'data{i}') for i in range(4)]

    def elab(self, m):
        # assumes in0 holds state while CFU executing
        m.d.sync += self.done.eq(self.start)
        for i in range(4):
            m.d.comb += self.lram_addr[i].eq(self.in0[2:])
            with m.If(self.in0[:2] == i):
                m.d.comb += self.output.eq(self.lram_data[i])


class HpsCfu(Cfu):
    """Gen2 accelerator CFU.

    Assumes working with a slimopt+cfu VexRiscV, which rsp_ready is
    always true.
    """

    def connect_verify(self, m, set_, get):
        """Connects the verify register get and set halves"""
        m.d.comb += get.reg_verify_value.eq(set_.reg_verify_value + 1)

    def connect_mem(self, m, mem):
        """Connects memory ports to the mem instruction"""

        for i in range(4):
            m.d.comb += [
                self.lram_addr[i].eq(mem.lram_addr[i]),
                mem.lram_data[i].eq(self.lram_data[i])
            ]

    def elab_instructions(self, m):
        m.submodules['ping'] = ping = PingInstruction()
        m.submodules['set'] = set_ = SetInstruction()
        m.submodules['get'] = get = GetInstruction()
        m.submodules['mem'] = mem = MemoryReadInstruction()

        self.connect_verify(m, set_, get)
        self.connect_mem(m, mem)

        return {
            Constants.INS_GET: get,
            Constants.INS_SET: set_,
            Constants.INS_MEM: mem,
            Constants.INS_PING: ping,
        }


def make_cfu():
    return HpsCfu()
