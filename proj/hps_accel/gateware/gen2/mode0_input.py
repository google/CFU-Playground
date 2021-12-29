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

"""Fetches data from RAM for input layers of Conv2D ops (Mode 0).

This Mode0 fetcher is used to fetch Conv2D input for the input layers of a
model. These Conv 2D ops have:

- depth 1 input pixels
- 4x4 pixel input
- stride 2
- input width 322
- output width 160

Data is read through the RamMux, allowing two words to be read on every cycle.
"""

from nmigen import Signal
from nmigen_cfu.util import SimpleElaboratable

from .ram_mux import RamMux
from .utils import unsigned_upto


class EvenPixelAddressGenerator(SimpleElaboratable):
    """Generates address of even numbered pixels.

    Odd numbered pixels are assumed to be at a two byte offset from the
    preceding even numbered pixel. All addresses are in bytes.

    In practice all addresses produced will be a multiple of words offset from
    base_addr.

    Attributes
    ----------

    base_addr: Signal(18), in
        A base number, added to all results

    addr: Signal(18), out
        The byte address for the current pixel.

    start: Signal(), in
        Starts address generation. Addr will be updated on next cycle.

    next: Signal(), in
        Indicates current address has been used. Address will be produced a
        total of eight times each. On the eighth next toggle, a new address
        will be available on the following cycle.
    """

    # Number of addresses to generate for each row. There 160 output pixels
    # to calculate, but we only output every second address
    NUM_ADDRESSES_X = 80

    # Bytes between rows. Since is stride 2, we skip 2 rows
    INCREMENT_Y = 322 * 2

    def __init__(self):
        self.base_addr = Signal(18)
        self.addr = Signal(18)
        self.start = Signal()
        self.next = Signal()

    def elab(self, m):
        pixel_x = Signal(8)
        pixel_row_begin_addr = Signal(16)
        next_count = Signal(3)

        with m.If(self.next):
            m.d.sync += next_count.eq(next_count + 1)
            with m.If(next_count == 7):
                last_x = pixel_x + 1 == self.NUM_ADDRESSES_X
                with m.If(last_x):
                    m.d.sync += [
                        self.addr.eq(pixel_row_begin_addr),
                        pixel_row_begin_addr.eq(
                            pixel_row_begin_addr + self.INCREMENT_Y),
                        pixel_x.eq(0),
                    ]
                with m.Else():
                    m.d.sync += self.addr.eq(self.addr + 4)
                    m.d.sync += pixel_x.eq(pixel_x + 1)
        with m.If(self.start):
            m.d.sync += [
                self.addr.eq(self.base_addr),
                pixel_row_begin_addr.eq(self.base_addr + self.INCREMENT_Y),
                pixel_x.eq(0),
                next_count.eq(0)
            ]
