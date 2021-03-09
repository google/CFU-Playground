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

from .post_process import SRDHMInstruction, RoundingDividebyPOTInstruction
from .param_store import ParamStoreSetter
from .registerfile import RegisterFileInstruction, RegisterSetter

from nmigen_cfu import Cfu

OUTPUT_CHANNEL_PARAM_DEPTH = 512


class Mnv2RegisterInstruction(RegisterFileInstruction):

    def elab_xetters(self, m):
        m.submodules['set_input_depth'] = set_input_depth = RegisterSetter()
        m.submodules['set_output_depth'] = set_output_depth = RegisterSetter()
        m.submodules['set_input_offset'] = set_input_offset = RegisterSetter()
        m.submodules['set_output_offset'] = set_output_offset = RegisterSetter()
        m.submodules['set_activation_min'] = set_activation_min = RegisterSetter()
        m.submodules['set_activation_max'] = set_activation_max = RegisterSetter()
        m.submodules['set_output_batch_size'] = set_output_batch_size = RegisterSetter()
        m.submodules['store_output_mutiplier'] = store_output_mutiplier = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        m.submodules['store_output_shift'] = store_output_shift = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        m.submodules['store_output_bias'] = store_output_bias = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        self.register_xetter(10, set_input_depth)
        self.register_xetter(11, set_output_depth)
        self.register_xetter(12, set_input_offset)
        self.register_xetter(13, set_output_offset)
        self.register_xetter(14, set_activation_min)
        self.register_xetter(15, set_activation_max)
        self.register_xetter(20, set_output_batch_size)
        self.register_xetter(21, store_output_mutiplier)
        self.register_xetter(22, store_output_shift)
        self.register_xetter(23, store_output_bias)


class Mnv2Cfu(Cfu):
    """Simple CFU for Mnv2.

    Most functionality is provided through a single set of registers.
    """

    def __init__(self):
        super().__init__({
            0: Mnv2RegisterInstruction(),
            6: RoundingDividebyPOTInstruction(),
            7: SRDHMInstruction(),
        })

    def elab(self, m):
        super().elab(m)


def make_cfu():
    return Mnv2Cfu()
