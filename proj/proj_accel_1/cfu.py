#!/bin/env python
# Copyright 2020 Google LLC
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
from nmigen_cfu import SimpleElaboratable, InstructionBase, TestBase, InstructionTestBase, Cfu, CfuTestBase

import unittest

class StoreInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))

    def elab(self, m):
        with m.If(self.start):
            with m.If(self.in0 == 10):
                m.d.sync += self.max_width.eq(self.in1s)
            with m.Elif(self.in0 == 11):
                m.d.sync += self.max_height.eq(self.in1s)
            m.d.comb += [
                self.done.eq(1),
                self.output.eq(1),
            ]
        return m

class StoreInstructionTest(TestBase):
    def create_dut(self):
        return StoreInstruction()

    def test_start(self):
        DATA = [
            # Only set max_width and max_height when start is 1.
            ((1,10,5),(1,1,0,0)),
            ((1,11,6),(1,1,5,0)),
            # Check that when start is 0, max_width and max_height remains the same.
            ((0,5,7),(0,0,5,6)),
            ((0,1,1),(0,0,5,6)),
            ((1,10,7),(1,1,5,6)),
            ((0,0,0),(0,0,7,6)),
            ((1,11,9),(1,1,7,6)),
            ((0,2,3),(0,0,7,9)),
            ((1,9,19),(1,1,7,9)),
            ((0,4,3),(0,0,7,9)),
            ((1,10,-3),(1,1,7,9)),
            ((0,1,6),(0,0,-3,9)),
            ((1,11,-4),(1,1,-3,9)),
            ((0,1,3),(0,0,-3,-4)),
        ]
        def process():
            for n,(inputs,outputs) in enumerate(DATA):
                start,in0,in1s = inputs
                done,output,width,height = outputs
                yield self.dut.start.eq(start)
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1s)
                yield
                self.assertEqual((yield self.dut.done),done)
                self.assertEqual((yield self.dut.output),output)
                self.assertEqual((yield self.dut.max_width),width)
                self.assertEqual((yield self.dut.max_height),height)
        self.run_sim(process, True)

class ReadInstruction(InstructionBase):
    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))

    def elab(self, m):
        m.d.comb += self.done.eq(1)
        with m.If(self.in0 == 10):
            m.d.comb += [
                self.output.eq(self.max_width),
            ]
        with m.Elif(self.in0 == 11):
            m.d.comb += [
                self.output.eq(self.max_height),
            ]
        return m

class ReadInstructionTest(TestBase):
    def create_dut(self):
        return ReadInstruction()

    def test_start(self):
        def process():
            width = 1234
            height = 5678
            yield self.dut.max_width.eq(width)
            yield self.dut.max_height.eq(height)
            yield self.dut.in0.eq(10)
            yield
            self.assertEqual((yield self.dut.done),1)
            self.assertEqual((yield self.dut.output),width)
            yield self.dut.in0.eq(11)
            yield
            self.assertEqual((yield self.dut.done),1)
            self.assertEqual((yield self.dut.output),height)
        self.run_sim(process, True)

class DoubleCompareInstruction(InstructionBase):
    """The 4 comparisons will be performed in parallel
    """
    def __init__(self):
        super().__init__()
        self.max_width = Signal(signed(32))
        self.max_height = Signal(signed(32))

    def elab(self, m):
        m.d.comb += [
            self.output.eq((self.in0s >= 0) & (self.in0s < self.max_width) & (self.in1s >= 0) & (self.in1s < self.max_height)),
            self.done.eq(1)
        ]

class DoubleCompareInstructionTest(TestBase):
    def create_dut(self):
        return DoubleCompareInstruction()

    def test_double_compare(self):
        DATA = [
            ((0,0,2,2),1),
            ((4,5,4,5),0),
            ((19,20,10,10),0),
            ((11,13,11,12),0),
            ((18,20,19,21),1),
            ((-3,1,5,6),0),
            ((-2,-2,5,6),0),
        ]
        def process():
            for n,(inputs,expected_output) in enumerate(DATA):
                in0,in1,width,height = inputs
                yield self.dut.in0.eq(in0)
                yield self.dut.in1.eq(in1)
                yield self.dut.max_width.eq(width)
                yield self.dut.max_height.eq(height)
                yield
                self.assertEqual((yield self.dut.output),expected_output)
        self.run_sim(process, True)

class ProjAccel1Cfu(Cfu):
    def __init__(self):
        self.dc = DoubleCompareInstruction()
        self.store = StoreInstruction()
        self.read = ReadInstruction()
        super().__init__({
            0: self.dc,
            1: self.store,
            2: self.read,
        })
    def elab(self,m):
        super().elab(m)
        m.d.comb += [
            self.dc.max_height.eq(self.store.max_height),
            self.dc.max_width.eq(self.store.max_width),
            self.read.max_height.eq(self.store.max_height),
            self.read.max_width.eq(self.store.max_width),
        ]

class ProjAccel1CfuTest(CfuTestBase):
    def create_dut(self):
        return ProjAccel1Cfu()

    def test_proj_accel1_cfu(self):
        DATA = [
            # Store the max_width and max_height values.
            ((1,10,6),None),
            ((1,11,7),None),
            # Output the max_width and max_height values.
            ((2,10,0),6),
            ((2,11,0),7),
            ((2,1,0),0),
            ((2,2,0),0),
            # Start the compare of in_x and in_y.
            ((0,1,1),1),
            ((0,5,6),1),
            ((0,0,0),1),
            ((0,5,7),0),
            ((0,6,7),0),
            ((0,10,10),0),
            # Test that negative values of in_x or in_y are not in range.
            ((0,-7,7),0),
            ((0,-10,-10),0),
            # Store the max_width and max_height values.
            ((1,10,20),None),
            ((1,11,18),None),
            # Output the max_width and max_height values.
            ((2,10,0),20),
            ((2,11,0),18),
            # Start the compare of in_x and in_y.
            ((0,10,12),1),
            ((0,3,10),1),
            ((0,19,17),1),
            ((0,20,20),0),
            ((0,24,25),0),
        ]
        return self.run_ops(DATA)

def make_cfu():
    return ProjAccel1Cfu()

if __name__ == '__main__':
    unittest.main()