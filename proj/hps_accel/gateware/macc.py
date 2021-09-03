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


from nmigen import Array, Shape, Signal, signed
from nmigen.hdl.rec import Layout
from nmigen_cfu.util import all_words, tree_sum, SimpleElaboratable

from .stream import Endpoint


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
    operands: Endpoint() input
        Stream of operands. The payload of this stream is a layout with two
        fields, 'inputs' and 'filters'. Each field is N 8-bit signed values.
    result: Endpoint(signed(32)) output
        Stream of results from the multiply and add operation.
        For each input and filter packet, a result packet is produced.
    """
    PIPELINE_CYCLES = 2

    def __init__(self, n):
        self._n = n
        self.enable = Signal()
        self.offset = Signal(signed(9))
        self.operands = Endpoint(Layout([
                ('inputs', Shape(8 * n)), ('filters', Shape(8 * n))]))
        self.result = Endpoint(signed(32))

    def elab(self, m):
        # TODO(dcallagh): add pipeline flow control
        m.d.comb += self.operands.ready.eq(1)
        m.d.comb += self.result.valid.eq(1)

        # Chop operands payload into 8-bit signed signals
        inputs = [self.operands.payload['inputs'][i:i + 8].as_signed()
                  for i in range(0, 8 * self._n, 8)]
        filters = [self.operands.payload['filters'][i:i + 8].as_signed()
                   for i in range(0, 8 * self._n, 8)]

        # Product is 17 bits: 8 bits * 9 bits = 17 bits
        products = [
            Signal(
                signed(17),
                name=f"product_{i:02x}") for i in range(
                self._n)]
        with m.If(self.enable):
            for i_val, f_val, product in zip(inputs, filters, products):
                f_tmp = Signal(signed(9))
                m.d.sync += f_tmp.eq(f_val)
                i_tmp = Signal(signed(9))
                m.d.sync += i_tmp.eq(i_val + self.offset)
                # TODO: consider whether to register output of multiplication
                m.d.comb += product.eq(i_tmp * f_tmp)

            m.d.sync += self.result.payload.eq(tree_sum(products))
