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

from nmigen import Signal, signed

from nmigen_cfu import SimpleElaboratable

from .registerfile import Xetter


class ExplicitMacc4(Xetter):
    """A Macc4 that operates on in0 (input_vals) and in1 (filter_vals).

    Public Interface
    ----------------
    input_offset: Signal(signed(8)) input
        Offset to be added to all inputs.

    """

    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(9))

    def elab(self, m):
        muls = []
        for n in range(4):
            tmp = Signal(signed(9))
            inval = self.in0.word_select(n, 8).as_signed()
            fval = self.in1.word_select(n, 8).as_signed()
            mul = Signal(signed(32))
            m.d.comb += [
                tmp.eq(inval + self.input_offset),
                mul.eq(tmp * fval)
            ]
            muls.append(mul)
        m.d.comb += [
            self.output.eq(sum(muls)),
            self.done.eq(1),
        ]
