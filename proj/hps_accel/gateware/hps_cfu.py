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
from nmigen_cfu import Cfu, InstructionBase

from .constants import Constants
from .get import GetInstruction
from .set import SetInstruction
from .stream import BinaryCombinatorialActor


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


class AddOneActor(BinaryCombinatorialActor):
    """A binary actor that adds one to a stream of integers.

    Used to implement the verification register.
    """

    def __init__(self):
        super().__init__(unsigned(32), unsigned(32))

    def transform(self, m, input, output):
        m.d.comb += output.eq(input + 1)


class HpsCfu(Cfu):

    def connect_verify_register(self, m, set, get):
        set_source = set.sources[Constants.REG_VERIFY]
        get_sink = get.sinks[Constants.REG_VERIFY]
        m.submodules["add_one"] = add_one = AddOneActor()
        m.d.comb += [
            set_source.connect(add_one.sink),
            add_one.source.connect(get_sink)
        ]

    def elab_instructions(self, m):
        m.submodules['set'] = set = SetInstruction()
        m.submodules['get'] = get = GetInstruction()

        self.connect_verify_register(m, set, get)

        m.submodules['ping'] = ping = PingInstruction()
        return {
            Constants.INS_GET: get,
            Constants.INS_SET: set,
            Constants.INS_PING: ping,
        }


def make_cfu():
    return HpsCfu()
