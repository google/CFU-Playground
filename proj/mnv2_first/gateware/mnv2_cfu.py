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
    def __init__(self):
        self.set_input_depth = RegisterSetter()
        self.set_output_depth = RegisterSetter()
        self.set_input_offset = RegisterSetter()
        self.set_output_offset = RegisterSetter()
        self.set_activation_min = RegisterSetter()
        self.set_activation_max = RegisterSetter()
        self.set_output_batch_size = RegisterSetter()
        self.store_output_mutiplier = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        self.store_output_shift = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        self.store_output_bias = ParamStoreSetter(
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH)
        xetters = {
            10: self.set_input_depth,
            11: self.set_output_depth,
            12: self.set_input_offset,
            13: self.set_output_offset,
            14: self.set_activation_min,
            15: self.set_activation_max,
            20: self.set_output_batch_size,
            21: self.store_output_mutiplier,
            22: self.store_output_shift,
            23: self.store_output_bias,
        }
        super().__init__(xetters)

    def register_xetters(self, m):
        m.submodules['set_input_depth'] = self.set_input_depth
        m.submodules['set_output_depth'] = self.set_output_depth
        m.submodules['set_input_offset'] = self.set_input_offset
        m.submodules['set_output_offset'] = self.set_output_offset
        m.submodules['set_activation_min'] = self.set_activation_min
        m.submodules['set_activation_max'] = self.set_activation_max
        m.submodules['set_output_batch_size'] = self.set_output_batch_size
        m.submodules['store_output_mutiplier'] = self.store_output_mutiplier
        m.submodules['store_output_shift'] = self.store_output_shift
        m.submodules['store_output_bias'] = self.store_output_bias

    def elab(self, m):
        self.register_xetters(m)


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
