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

"""Gateware for the accelerator."""

from amaranth import Signal, signed, unsigned
from .constants import Constants
from .macc import get_macc_block_class
from ..util import SimpleElaboratable


class SystolicArray(SimpleElaboratable):
    """A systolic array of multiply-accumulators.

    Parameters
    ----------

    specialize_nx: bool
      True to explicitly use Crosslink/NX DSP blocks, otherwise use regular
      verilog multiply operation.

    a_size: int
      The number of A words processed concurrently

    b_size: int
      The number of B words processed concurrently

    n: int
        The number of multipliers. Four is the usual value.

    a_shape: Shape
        The shape of each the value packed into the A input. If the A
        input is used for Conv2D activation values, signed(9) or
        unsigned(8) might be appropriate values.

    b_shape: Shape
        The shape of each the value packed into the B input. If the B
        input is used for Conv2D filter values, signed(8) would be the
        appropriate shape.

    accumulator_shape: Shape
        The shape of the accumulator. The accumulator should have
        enough precision that it does not overflow under normal
        operation. signed(32) is usually large enough, but a narrower
        accumulator may be sufficient, and will make more efficient
        use of the FPGA fabric.

    Attributes
    ----------

    a_inputs: [Signal(n * a_shape.width)], in
      List of words forming the A inputs

    b_inputs: [Signal(n * b_shape.width)], in
      List of words forming the B inputs

    first: Signal, in
      Indicates first word being processed at top left of array

    last: Signal, in
      Indicates last word being processed at top left of array

    accumulator: [Signal(accumulator_shape)] * (a_size * b_size), out
      The accumulator result from each macc unit

    accumulator_new: [Signal()] * (a_size * b_size), out
      The accumulator update strobe from each macc unit
    """

    def __init__(self, specialize_nx=False, a_size=Constants.SYS_ARRAY_HEIGHT,
                 b_size=Constants.SYS_ARRAY_WIDTH, n=4,
                 a_shape=signed(9), b_shape=signed(8),
                 accumulator_shape=signed(32)):
        self._specialize_nx = specialize_nx
        self._a_size = a_size
        self._b_size = b_size
        self._n = n
        self._a_shape = a_shape
        self._b_shape = b_shape
        self._accumulator_shape = accumulator_shape

        self.input_a = [Signal(unsigned(n * a_shape.width), name=f"input_a{i}")
                        for i in range(a_size)]
        self.input_b = [Signal(unsigned(n * b_shape.width), name=f"input_b{i}")
                        for i in range(b_size)]

        self.first = Signal()
        self.last = Signal()

        self.accumulator = [Signal(accumulator_shape)
                            for _ in range(a_size * b_size)]
        self.accumulator_new = [Signal() for _ in range(a_size * b_size)]

    def elab(self, m):
        maccs = [[None for _ in range(self._b_size)]
                  for _ in range(self._a_size)]
        for i in range(self._a_size):
            for j in range(self._b_size):
                klass = get_macc_block_class(self._specialize_nx)
                macc = klass(self._n, self._a_shape, self._b_shape,
                                 self._accumulator_shape)
                maccs[i][j] = macc

        for i in range(self._a_size):
            for j in range(self._b_size):
                m.submodules[f'macc_{i}_{j}'] = maccs[i][j]
                a_in = self.input_a[i] if j == 0 else maccs[i][j - 1].output_a
                b_in = self.input_b[j] if i == 0 else maccs[i - 1][j].output_b
                if i == 0 and j == 0:
                    first_in = self.first
                    last_in = self.last
                elif j == 0:
                    first_in = maccs[i - 1][0].output_first
                    last_in = maccs[i - 1][0].output_last
                else:
                    first_in = maccs[i][j - 1].output_first
                    last_in = maccs[i][j - 1].output_last
                acc_idx = i + j * self._a_size
                m.d.comb += [
                    maccs[i][j].input_a.eq(a_in),
                    maccs[i][j].input_b.eq(b_in),
                    maccs[i][j].input_first.eq(first_in),
                    maccs[i][j]. input_last.eq(last_in),
                    self.accumulator[acc_idx].eq(
                        maccs[i][j].output_accumulator),
                    self.accumulator_new[acc_idx].eq(
                        maccs[i][j].output_accumulator_new)
                ]
