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

"""Fetches data from RAM for input to Conv2D ops.

The RAM from which data is fetched consists of 4 32 bit wide, 16K words deep
LRAMs, with word addresses in rows across the LRAMs:

+--------+--------+--------+--------+
| LRAM 0 | LRAM 1 | LRAM 2 | LRAM 3 |
+--------+--------+--------+--------+
|    0   |    1   |    2   |    3   |
+--------+--------+--------+--------+
|    4   |    5   |    6   |    7   |
+--------+--------+--------+--------+
|    8   |    9   |   10   |   11   |
+--------+--------+--------+--------+
|  ...   |  ...   |  ...   |  ...   |
+--------+--------+--------+--------+

The main mode is used when Conv2D input data has a depth that is a multiple of
16 values per pixel. We call these groups of 16 pixels a "block". Each block
begins in LRAM 0.

In this main mode, four words are fetched concurrently, one each for four
separate pixels, with one word being fetched from each LRAM. This produces four
separate streams of pixel data. Assuming pixels are 16 bytes deep and thus
consist of 1 block of data, the fetch order would be:

+------+---------+---------+---------+---------+
| time | fetch 0 | fetch 1 | fetch 2 | fetch 3 |
+------+---------+---------+---------+---------+
|    0 |     0*  |     -   |     -   |     -   |
|    1 |     1   |     4*  |     -   |     -   |
|    2 |     2   |     5   |     8*  |     -   |
|    3 |     3   |     6   |     9   |    12*  |
|    4 |    16*  |     7   |    10   |    13   |
|    5 |    17   |    20*  |    11   |    14   |
|    6 |    18   |    21   |    24*  |    15   |
|    7 |    19   |    22   |    25   |    28*  |
+------+---------+---------+---------+---------+

(*) denotes the start of a new pixel.

TODO:
- handle padding in y or x directions

TODO: An alternate mode to deal with input layers
- one channel per input
- probably padding to include
- stride 2 in both directions
- no need to cross row boundaries
"""

from nmigen import Signal
from nmigen_cfu.util import SimpleElaboratable


class PixelAddressGenerator(SimpleElaboratable):
    """Generates address of each pixel in turn.

    Generates the starting address of each pixel. All addresses are expressed
    in block numbers.

    Intended to be used in the case where each pixel has a depth that is a
    multiple of 16.

    Attributes
    ----------

    base_addr: Signal(14), in
        A base number, added to all results

    num_pixels_x: Signal(9), in
        How many pixels in a row

    num_blocks_x: Signal(4), in
        Number of RAM blocks to advance to move to new pixel in X direction

    num_blocks_y: Signal(8), in
        Number of RAM blocks to advance between pixels in Y direction

    addr: Signal(14), out
        The output row address for the current pixel.

    start:
        Starts address generation. Addr will be updated on next cycle.

    next:
        Indicates current address has been used. Address will be updated on next
        cycle with next row address.
    """

    def __init__(self):
        self.base_addr = Signal(14)
        self.num_pixels_x = Signal(9)
        self.num_blocks_x = Signal(4)
        self.num_blocks_y = Signal(8)
        self.addr = Signal(14)
        self.start = Signal()
        self.next = Signal()

    def elab(self, m):
        pixel_x = Signal(9)
        pixel_row_begin_addr = Signal(14)

        with m.If(self.next):
            last_x = pixel_x + 1 == self.num_pixels_x
            with m.If(last_x):
                m.d.sync += [
                    self.addr.eq(pixel_row_begin_addr),
                    pixel_row_begin_addr.eq(
                        pixel_row_begin_addr + self.num_blocks_y),
                    pixel_x.eq(0),
                ]
            with m.Else():
                m.d.sync += [
                    self.addr.eq(self.addr + self.num_blocks_x),
                    pixel_x.eq(pixel_x + 1),
                ]
        with m.If(self.start):
            m.d.sync += [
                self.addr.eq(self.base_addr),
                pixel_row_begin_addr.eq(self.base_addr + self.num_blocks_y),
                pixel_x.eq(0)
            ]
