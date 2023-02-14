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

from amaranth import C, Module, Signal, signed
from amaranth_cfu import all_words, InstructionBase, InstructionTestBase, pack_vals, simple_cfu
import unittest


# Custom instruction inherits from the InstructionBase class.
class SimdMac(InstructionBase):
    def __init__(self, input_offset=128) -> None:
        super().__init__()

        self.input_offset = C(input_offset, signed(9))

    # `elab` method implements the logic of the instruction.
    def elab(self, m: Module) -> None:
        words = lambda s: all_words(s, 8)

        # SIMD multiply step:
        self.prods = [Signal(signed(16)) for _ in range(4)]
        for prod, w0, w1 in zip(self.prods, words(self.in0), words(self.in1)):
            m.d.comb += prod.eq(
                (w0.as_signed() + self.input_offset) * w1.as_signed())

        m.d.sync += self.done.eq(0)
        # self.start signal high for one cycle when instruction started.
        with m.If(self.start):
            with m.If(self.funct7):
                m.d.sync += self.output.eq(0)
            with m.Else():
                # Accumulate step:
                m.d.sync += self.output.eq(self.output + sum(self.prods))
            # self.done signal indicates instruction is completed.
            m.d.sync += self.done.eq(1)


# Tests for the instruction inherit from InstructionTestBase class.
class SimdMacTest(InstructionTestBase):
    def create_dut(self):
        return SimdMac()

    def test(self):
        # self.verify method steps through expected inputs and outputs.
        self.verify([
            (1, 0, 0, 0),  # reset
            (0, pack_vals(-128, 0, 0, 1), pack_vals(111, 0, 0, 1), 129 * 1),
            (0, pack_vals(0, -128, 1, 0), pack_vals(0, 52, 1, 0), 129 * 2),
            (0, pack_vals(0, 1, 0, 0), pack_vals(0, 1, 0, 0), 129 * 3),
            (0, pack_vals(1, 0, 0, 0), pack_vals(1, 0, 0, 0), 129 * 4),
            (0, pack_vals(0, 0, 0, 0), pack_vals(0, 0, 0, 0), 129 * 4),
            (0, pack_vals(0, 0, 0, 0), pack_vals(-5, 0, 0, 0), 0xffffff84),
            (1, 0, 0, 0),  # reset
            (0, pack_vals(-12, -128, -88, -128), pack_vals(-1, -7, -16,
                                                           15), 0xfffffd0c),
            (1, 0, 0, 0),  # reset
            (0, pack_vals(127, 127, 127, 127), pack_vals(127, 127, 127,
                                                         127), 129540),
            (1, 0, 0, 0),  # reset
            (0, pack_vals(127, 127, 127,
                          127), pack_vals(-128, -128, -128, -128), 0xfffe0200),
        ])


# Expose make_cfu function for cfu_gen.py
def make_cfu():
    # Associate cfu_op0 with SimdMac.
    return simple_cfu({0: SimdMac()})


# Use `../../scripts/pyrun cfu.py` to run unit tests.
if __name__ == '__main__':
    unittest.main()

# from amaranth import *
# from amaranth_cfu import InstructionBase, InstructionTestBase, simple_cfu, CfuTestBase
# import unittest

# # See proj_example for further example instructions


# class TemplateInstruction(InstructionBase):
#     """Template instruction
#     """

#     def elab(self, m):
#         with m.If(self.start):
#             m.d.sync += self.output.eq(self.in0 + self.in1)
#             m.d.sync += self.done.eq(1)
#         with m.Else():
#             m.d.sync += self.done.eq(0)


# class TemplateInstructionTest(InstructionTestBase):
#     def create_dut(self):
#         return TemplateInstruction()

#     def test(self):
#         self.verify([
#             (0, 0, 0),
#             (4, 5, 9),
#             (0xffffffff, 0xffffffff, 0xfffffffe),
#         ])


# def make_cfu():
#     return simple_cfu({
#         # Add instructions here...
#         0: TemplateInstruction(),
#     })


# class CfuTest(CfuTestBase):
#     def create_dut(self):
#         return make_cfu()

#     def test(self):
#         DATA = [
#             # Test CFU calls here...
#             ((0, 22, 22), 44),
#         ]
#         return self.run_ops(DATA)


# if __name__ == '__main__':
#     unittest.main()
