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

"""Fetches data from RAM for input to Conv2D ops (Mode1).

This Mode1 fetcher is used when the Conv2D input data has a depth that is
a multiple of 16. Each pixel's data is aligned on 16 byte boundaries.

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

We call each group of 4 words (16 bytes) a "block". Each input pixels data
begins on a block boundary and is an exact multiple of a number of blocks long.
The first word for each pixel is in LRAM0, the second in LRAM1 and so on.

The input fetcher produces four streams of pixel data suitable for input to the
systolic array. Each stream consists of a 4x4 square of pixels extracted from
the larger input buffer.

In the X direction, the blocks of pixel data are sequential - data for pixels
(1, 0) is directly after pixel (0,0). The following table shows the memory
access pattern at the beginning of a fetch of four pixels where input
depth = 16.

+------+---------+---------+---------+---------+
| time | fetch 0 | fetch 1 | fetch 2 | fetch 3 |
+------+---------+---------+---------+---------+
|    0 |     0   |     -   |     -   |     -   |
|    1 |     1   |     4   |     -   |     -   |
|    2 |     2   |     5   |     8   |     -   |
|    3 |     3   |     6   |     9   |    12   |
|    4 |     4   |     7   |    10   |    13   |
|    5 |     5   |     8   |    11   |    14   |
|    6 |     6   |     9   |    12   |    15   |
|    7 |     7   |    10   |    13   |    26   |
+------+---------+---------+---------+---------+

Note that, because the starts of fetches for each stream of data are delayed by
a cycle, each is working from a different LRAM bank on each cycle.

In the Y direction, some number of blocks must be skipped so address generation
is a little more complicated. There are two classes involved in address
generation: the `PixelAddressGenerator` generates the start addresses from
which data is to be read, and the `ValueAddressGenerator` generates the
addresses for all the data for a given output pixel from that start address.
"""

from amaranth import Array, Mux, Signal, unsigned

from ..util import SimpleElaboratable
from .utils import unsigned_upto


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
        The output block address for the current pixel.

    start: Signal(), in
        Starts address generation. Addr will be updated to base_addr on next
        cycle.

    next: Signal(), in
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


class PixelAddressRepeater(SimpleElaboratable):
    """Repeats addresses from PixelAddressGenerator.

    The systolic array requires multiple passes over input data. This class
    provides that functionatlity by repeating the pixel start addresses
    generated from PixelAddress Generator.

    Pixel addresses are repeated in groups of four, which matches the
    number of outputs of the InputFetcher and inputs to the systolic array.

    Attributes
    ----------

    repeats: Signal(unsigned_upto(64)), in
        The number of times each stream of input pixel data is to be repeated.

    next: Signal(), in
        Indicates current address has been used. Address will be updated on next
        cycle with next row address.

    addr: Signal(14), out
        Output address

    start: Signal(), in
        Starts address generation. Addr will be updated on next cycle.

    gen_next: Signal(), out
        Indicates that a new pixel address is required.

    gen_addr: Signal(14), in
        Input from the PixelAddressGenerator

    """

    def __init__(self):
        self.repeats = Signal(unsigned_upto(64))
        self.next = Signal()
        self.addr = Signal(14)
        self.start = Signal()
        self.gen_next = Signal()
        self.gen_addr = Signal(14)

    def elab(self, m):
        group = Signal(range(4))
        repeat_count = Signal.like(self.repeats)
        mem = Array([Signal(14, name=f"mem{i}") for i in range(4)])

        with m.If(repeat_count == 0):
            # On first repeat - pass through next and addr and record addresses
            m.d.comb += self.gen_next.eq(self.next)
            m.d.comb += self.addr.eq(self.gen_addr)
            with m.If(self.next):
                m.d.sync += mem[group].eq(self.gen_addr)
        with m.Else():
            # Subsequently use recorded data
            m.d.comb += self.addr.eq(mem[group])

        # Update group and repeat_count on next
        with m.If(self.next):
            m.d.sync += group.eq(group + 1)
            with m.If(group == 3):
                m.d.sync += repeat_count.eq(repeat_count + 1)
                with m.If(repeat_count + 1 == self.repeats):
                    m.d.sync += repeat_count.eq(0)

        with m.If(self.start):
            m.d.sync += repeat_count.eq(0)
            m.d.sync += group.eq(0)


class ValueAddressGenerator(SimpleElaboratable):
    """Generates addresses within a single pixel.

    Specifically for a 4x4 2DConv, works with a PixelAddressGenerator to find
    addresses of individual values. It reads `depth` * 4 * 32bit words,
    then moves down and repeats this. An external counter re-starts the
    generator once it has read 4 complete rows of input.

    Attributes
    ----------

    start: Signal, in
        Begin generating addresses from the start_addr.

    start_addr: Signal(14), in
        Address of start of first pixel, from a PixelAddressGenerator.

    depth: Signal(3), in
        Number of 16-byte blocks to read per pixel. Max depth is 7 which is 112
        values/pixel).

    num_blocks_y: Signal(10), in
        Number of blocks per row.

    addr_out: Signal(14), out
        Current output address
    """

    def __init__(self):
        self.start = Signal()
        self.start_addr = Signal(14)
        self.depth = Signal(3)
        self.num_blocks_y = Signal(10)
        self.addr_out = Signal(14)

    def elab(self, m):
        x_count = Signal(7)
        next_row_addr = Signal(14)
        addr = Signal(14)

        with m.If(self.start):
            # Start overrides other behaviors
            m.d.comb += self.addr_out.eq(self.start_addr)
            m.d.sync += [
                addr.eq(self.start_addr),
                x_count.eq(1),
                next_row_addr.eq(self.start_addr + self.num_blocks_y),
            ]
        with m.Else():
            m.d.comb += self.addr_out.eq(addr)
            # x_size is the number of cycles to read 4 consecutive pixels
            x_size = Signal(7)
            m.d.comb += x_size.eq(self.depth << 4)
            with m.If(x_count != (x_size - 1)):
                m.d.sync += x_count.eq(x_count + 1)
                with m.If(x_count[:2] == 3):
                    m.d.sync += addr.eq(addr + 1)
            with m.Else():
                # x_count == x_size - 1 ==> End of row
                m.d.sync += [
                    addr.eq(next_row_addr),
                    next_row_addr.eq(next_row_addr + self.num_blocks_y),
                    x_count.eq(0),
                ]


class Mode1InputFetcher(SimpleElaboratable):
    """Fetches input vectors for Conv2D.

    Coordinates a "normal mode" input fetch, where input data depth is a
    multiple of 16.

    Attributes
    ----------

    reset: Signal, in
        Pulsed to stop producing values. This ensures that invalid first
        and last signals are not produced.

    start: Signal, in
        Pulsed to begin producing data. There is a delay of 2 cycles between
        the start signal and the first valid data being produced.

    base_addr: Signal(18), in
        A base address, in bytes. Assumed to be a multiple of 16

    num_pixels_x: Signal(9), in
        How many pixels in a row

    pixel_advance_x: Signal(4), in
        Number of RAM blocks to advance to move to new pixel in X direction

    pixel_advance_y: Signal(8), in
        Number of RAM blocks  to advance between pixels in Y direction

    depth: Signal(3), in
        Number of 16-byte blocks to read per pixel. Max depth is 7 which is 112
        values/pixel). Total number of cycles per output pixel is
        depth * (4 cycles/block) * 4 (x dim) * 4 (y dim) = 64 * depth.

    repeats: Signal(unsigned_upto(64)), in
        The number of times each stream of input pixel data is to be repeated.

    ram_mux_phase: Signal(range(4)), out
        The phase provided to the RamMux

    ram_mux_addr: [Signal(14)] * 4, out
        Addresses to send to the RAM Mux

    ram_mux_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.

    data_out: [Signal(32)] * 4, out
        Data for each of four pixels.

    first: Signal(), out
        Indicates first data for a pixel available at data_out[0]. First data
        will arrive at data_out[1] a cycle later and so on. This signal is not
        valid until 2 cycles after start.

    last: Signal(), out
        Indicates last data for a pixel available at data_out[0]. Last data
        will arrive at data_out[1] a cycle later and so on.
    """

    def __init__(self):
        self.reset = Signal()
        self.start = Signal()
        self.base_addr = Signal(18)
        self.num_pixels_x = Signal(9)
        self.pixel_advance_x = Signal(4)
        self.pixel_advance_y = Signal(8)
        self.depth = Signal(3)
        self.num_repeats = Signal(unsigned_upto(64))
        self.ram_mux_phase = Signal(range(4))
        self.ram_mux_addr = [Signal(14, name=f"rm_addr{i}") for i in range(4)]
        self.ram_mux_data = [Signal(32, name=f"rm_data{i}") for i in range(4)]
        self.data_out = [Signal(32, name=f"data_out{i}") for i in range(4)]
        self.first = Signal()
        self.last = Signal()

    def elab(self, m):
        m.submodules["pixel_ag"] = pixel_ag = PixelAddressGenerator()
        m.submodules["repeater"] = repeater = PixelAddressRepeater()
        value_ags = [ValueAddressGenerator() for _ in range(4)]
        for i, v in enumerate(value_ags):
            m.submodules[f"value_ag{i}"] = v

        # Connect pixel address generator and repeater
        m.d.comb += [
            pixel_ag.base_addr.eq(self.base_addr >> 4),
            pixel_ag.num_pixels_x.eq(self.num_pixels_x),
            pixel_ag.num_blocks_x.eq(self.pixel_advance_x),
            pixel_ag.num_blocks_y.eq(self.pixel_advance_y),
            repeater.repeats.eq(self.num_repeats),
            pixel_ag.next.eq(repeater.gen_next),
            repeater.gen_addr.eq(pixel_ag.addr),
            pixel_ag.start.eq(self.start),
            repeater.start.eq(self.start),
        ]

        # Connect value address generators
        for v in value_ags:
            m.d.comb += [
                v.start_addr.eq(repeater.addr),
                v.depth.eq(self.depth),
                v.num_blocks_y.eq(self.pixel_advance_y),
            ]

        # cycle_counter counts cycles through reading input data
        max_cycle_counter = Signal(9)
        m.d.comb += max_cycle_counter.eq((self.depth << 6) - 1)
        cycle_counter = Signal(9)

        # Stop running on reset. Start running on start
        running = Signal()
        with m.If(self.reset):
            m.d.sync += running.eq(0)
        with m.Elif(self.start):
            m.d.sync += running.eq(1)
            m.d.sync += cycle_counter.eq(0)
        with m.Elif(running):
            rollover = cycle_counter == max_cycle_counter
            m.d.sync += cycle_counter.eq(Mux(rollover, 0, cycle_counter + 1))

        # Calculate when to start value address generators and when to get
        # next pixel address
        next_pixel = 0
        for i in range(4):
            start_gen = Signal()
            m.d.comb += start_gen.eq(running & (cycle_counter == i))
            m.d.comb += value_ags[i].start.eq(start_gen)
            next_pixel |= start_gen
        m.d.comb += repeater.next.eq(next_pixel)

        # Generate first and last signals
        m.d.sync += [
            self.first.eq(running & (cycle_counter == 0)),
            self.last.eq(running & (cycle_counter == max_cycle_counter)),
        ]

        # Connect to RamMux
        m.d.comb += self.ram_mux_phase.eq(cycle_counter[:2])
        for i in range(4):
            m.d.comb += [
                self.ram_mux_addr[i].eq(value_ags[i].addr_out),
                self.data_out[i].eq(self.ram_mux_data[i]),
            ]
