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


from nmigen import Array, Signal, signed
from nmigen_cfu.util import all_words, tree_sum, SimpleElaboratable


class MultiplyAccumulate(SimpleElaboratable):
    """An N-wide 8 bit multiply and add unit,

    Performs the calculation:
      result = sum((i_data[n] + offset) * f_data[n] for n in range(N))

    The calculation completes 2 cycles after inputs are applied.

    Parmameters
    -----------

    n: int
        The number of multipliers

    Attributes
    ----------

    enable: Signal() input
        When enabled, calculation resumes from when last disabled.
    offset: Signal(signed(9)) input
        Offset to be added to all inputs.
    inputs: list[Signal(signed(8))] input
        The N input values
    filters: list[Signal(signed(8))] input
        The N filter values
    result: Signal(signed(32)) output
        Result of the multiply and add operation
    """
    PIPELINE_CYCLES = 2

    def __init__(self, n):
        self._n = n
        self.enable = Signal()
        self.offset = Signal(signed(9))

        def sig8(name, idx):
            return Signal(signed(8), name=f"{name}_{idx:02x}")

        self.inputs = [sig8("input", i) for i in range(n)]
        self.filters = [sig8("filter", i) for i in range(n)]
        self.result = Signal(signed(32))

    def elab(self, m):
        # Product is 17 bits: 8 bits * 9 bits = 17 bits
        products = [
            Signal(
                signed(17),
                name=f"product_{i:02x}") for i in range(
                self._n)]
        with m.If(self.enable):
            for i_val, f_val, product in zip(
                    self.inputs, self.filters, products):
                f_tmp = Signal(signed(9))
                m.d.sync += f_tmp.eq(f_val)
                i_tmp = Signal(signed(9))
                m.d.sync += i_tmp.eq(i_val + self.offset)
                # TODO: consider whether to register output of multiplication
                m.d.comb += product.eq(i_tmp * f_tmp)

            m.d.sync += self.result.eq(tree_sum(products))
