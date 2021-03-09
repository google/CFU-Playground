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

from nmigen import Signal
from nmigen_cfu.cfu import InstructionTestBase
from util import DualPortMemory
from .param_store import CircularIncrementer, ParamStoreSetter
from .registerfile import RegisterSetter, Xetter, RegisterFileInstruction


class _CircularGetter(Xetter):
    """Wraps a Circular Reader.

    For testing.

    Public Interface
    ----------------
    next: Signal output
        Go to next address
    r_data: Signal(width) output
        Next address
    """

    def __init__(self):
        super().__init__()
        self.next = Signal()
        self.r_data = Signal(32)

    def elab(self, m):
        m.d.comb += [
            # Output always ready
            self.done.eq(1),
            # Output is whatever reader says
            self.output.eq(self.r_data),
            # Step reader on every start
            self.next.eq(self.start),
        ]


class GetSetInstructionTest(InstructionTestBase):
    def create_dut(self):
        m = self.m
        m.submodules['dp'] = dp = DualPortMemory(
            width=8, depth=32, is_sim=True)
        m.submodules['inc'] = inc = CircularIncrementer(32)
        m.submodules['psset'] = psset = ParamStoreSetter(8, 32)
        m.submodules['psget'] = psget = _CircularGetter()
        m.submodules['reg'] = reg = RegisterSetter()
        m.d.comb += [
            # Restart param store when reg is set
            psset.restart.eq(reg.set),
            inc.restart.eq(reg.set),
            # Incrementer is limited to number of items set and increments
            # whenever an item is retrieved
            inc.limit.eq(psset.count),
            inc.next.eq(psget.next),
            # Hook memory up to various components
            psget.r_data.eq(dp.r_data),
            dp.r_addr.eq(inc.r_addr),
            dp.w_en.eq(psset.w_en),
            dp.w_addr.eq(psset.w_addr),
            dp.w_data.eq(psset.w_data),
        ]
        return RegisterFileInstruction({
            1: psset,
            2: psget,
            9: reg,
        })

    def test(self):
        self.verify([
            # Restart
            (9, 0, 0, 0),
            # Put a thing in memory
            (1, 12, 0, 0),
            # Read it, twice.
            (2, 0, 0, 12),
            (2, 0, 0, 12),
            # Put more things in memory
            (1, 13, 0, 0),
            (1, 14, 0, 0),
            (1, 15, 0, 0),
            # Read it all back
            (2, 0, 0, 12),
            (2, 0, 0, 13),
            (2, 0, 0, 14),
            (2, 0, 0, 15),
            (2, 0, 0, 12),
            (2, 0, 0, 13),
        ], True)
