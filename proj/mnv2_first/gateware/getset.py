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


from typing import OrderedDict
from nmigen import Signal
from nmigen_cfu import InstructionBase, SimpleElaboratable, ValueBuffer


class Xetter(SimpleElaboratable):
    """Setter/Getter base class.

    In many ways, this is a cut down version of an instruction. Like an instruction,
    it has two inputs and one output. Processing is controlled with start and end signals.

    Unlike an instuction, Xetter does not have funct7 available.

    Public Interface
    ----------------
    start: Signal input
        When to start executing this instruction. Set only for one cycle.
    in0: Signal(32) input
        The first operand. Only available when `start` is signalled.
    in1: Signal(32) input
        The second operand. Only available when `start` is signalled.
    done: Signal() output
        Single cycle signal to indicate that processing has finished.
    output: Signal(32) output
        The result. Must be valid when `done` is signalled.
    """

    def __init__(self):
        self.start = Signal()
        self.done = Signal()
        self.in0 = Signal(32)
        self.in1 = Signal(32)
        self.output = Signal(32)


class RegisterSetter(Xetter):
    """A Setter for a value.

    Sets new value from in0. Return previous value on set.

    Parameters
    ----------
    width: int
        Number of bits in the Xetter value (1-32)

    Public Interface
    ----------------
    value: Signal(width) output
        The value held by this register. It will be set from in0.
    set: Signal output
        This signal is pulsed high for a single cycle when register is set.
    """

    def __init__(self, width=32):
        super().__init__()
        self.value = Signal(width)
        self.set = Signal()

    def elab(self, m):
        m.d.sync += self.set.eq(0)
        with m.If(self.start):
            m.d.sync += self.value.eq(self.in0),
            m.d.sync += self.set.eq(1),
            m.d.comb += self.output.eq(self.value)
            m.d.comb += self.done.eq(1)


class GetSetInstruction(InstructionBase):
    """Aggregates a number instructions that allow a CPU to get and set values.

    The instruction uses funct7 to identify a "Xetter" to which to delegate.
    """

    def __init__(self, xetters):
        """Constructor

        Parameters
        ----------

        xetters: mapping of register number (integer 0-127) to a subclass of Xetter.
        """
        super().__init__()
        self.xetters = OrderedDict(xetters)

    def elab(self, m):
        # By default, wire done to start to prevent hangs
        m.d.comb += self.done.eq(self.start)

        # Based on funct7, route start, done and output signals
        m.submodules['f7buf'] = f7buf = ValueBuffer(self.funct7, self.start)
        for reg, x in self.xetters.items():
            m.d.comb += [
                x.in0.eq(self.in0),
                x.in1.eq(self.in1),
            ]
            with m.If(f7buf.output == reg):
                m.d.comb += [
                    x.start.eq(self.start),
                    self.output.eq(x.output),
                    self.done.eq(x.done),
                ]
