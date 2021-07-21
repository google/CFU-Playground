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

from nmigen import *
from nmigen_cfu import InstructionBase, Cfu


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


class HpsCfu(Cfu):
    def elab_instructions(self, m):
        m.submodules['ping'] = ping = PingInstruction()
        return {
            7: ping,
        }


def make_cfu():
    return HpsCfu()
