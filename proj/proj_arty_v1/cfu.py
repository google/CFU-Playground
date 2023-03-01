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

from amaranth import *
from amaranth_cfu import InstructionBase, InstructionTestBase, simple_cfu, CfuTestBase
import unittest

# See proj_example for further example instructions


class TemplateInstruction(InstructionBase):
    """Template instruction
    """

    def elab(self, m):
        with m.If(self.start):
            m.d.sync += self.output.eq(self.in0 + self.in1)
            m.d.sync += self.done.eq(1)
        with m.Else():
            m.d.sync += self.done.eq(0)


class TemplateInstructionTest(InstructionTestBase):
    def create_dut(self):
        return TemplateInstruction()

    def test(self):
        self.verify([
            (0, 0, 0),
            (4, 5, 9),
            (0xffffffff, 0xffffffff, 0xfffffffe),
        ])


def make_cfu():
    return simple_cfu({
        # Add instructions here...
        0: TemplateInstruction(),
    })


class CfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        DATA = [
            # Test CFU calls here...
            ((0, 22, 22), 44),
        ]
        return self.run_ops(DATA)


if __name__ == '__main__':
    unittest.main()
