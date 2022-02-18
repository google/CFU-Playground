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

from amaranth import Signal
from amaranth.sim import Settle

from amaranth_cfu import InstructionTestBase, TestBase

from .registerfile import Xetter, RegisterSetter, RegisterFileInstruction


class RegisterSetterTest(TestBase):
    def create_dut(self):
        return RegisterSetter()

    def test_setget(self):
        DATA = [
            ((0, 00, 00), (0, 0, 0, 0)),
            # Set 23, then 45
            ((1, 23, 00), (1, 0, 0, 0)),
            ((1, 45, 00), (1, 23, 23, 1)),
            ((0, 12, 99), (0, 0, 45, 1)),
            ((0, 00, 99), (0, 0, 45, 0)),
            # Set 88 (also gets 45)
            ((1, 88, 99), (1, 45, 45, 0)),
            ((0, 00, 99), (0, 0, 88, 1)),
        ]

        def process():
            for n, ((start, in0, in1), (done, output, value, set)
                    ) in enumerate(DATA):
                yield self.dut.start.eq(start)
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield Settle()
                self.assertEqual((yield self.dut.done), done, f"cycle={n}")
                self.assertEqual((yield self.dut.output), output, f"cycle={n}")
                self.assertEqual((yield self.dut.value), value, f"cycle={n}")
                self.assertEqual((yield self.dut.set), set, f"cycle={n}")
                yield
        self.run_sim(process, False)


class _AccumulateXetter(Xetter):
    """For unit tests"""

    def __init__(self):
        super().__init__()
        self.value = Signal(32)

    def elab(self, m):
        m.d.sync += self.done.eq(0)
        with m.FSM():
            with m.State("waiting"):
                with m.If(self.start):
                    m.d.sync += self.value.eq(self.in0 + self.in1 + self.value)
                    m.next = "calculating"
            with m.State("calculating"):
                m.d.sync += self.output.eq(self.value)
                m.d.sync += self.done.eq(1)
                m.next = "waiting"


class _MyRegisterFileInstruction(RegisterFileInstruction):
    def elab_xetters(self, m):
        m.submodules['rs1'] = rs1 = RegisterSetter()
        m.submodules['rs2'] = rs2 = RegisterSetter()
        m.submodules['acc'] = adder = _AccumulateXetter()
        self.register_xetter(1, rs1)
        self.register_xetter(2, rs2)
        self.register_xetter(9, adder)


class RegisterFileInstructionTest(InstructionTestBase):
    def create_dut(self):
        return _MyRegisterFileInstruction()

    def test(self):
        self.verify([
            # Accumulate "setter"
            (9, 12, 10, 22),
            (9, 9, 1, 32),
            # Set Reg 1, Reg 2
            (1, 7777, 1, 0),
            (2, 8888, 1, 0),
            # Get Reg 1, Reg2
            (1, 0, 1, 7777),
            (2, 0, 1, 8888),
            # Do Reg 1 a few times in a row
            (1, 2, 1, 0),
            (1, 3, 1, 2),
            (1, 4, 1, 3),
            # One more accumulate
            (9, 17, 15, 64),
        ], False)
