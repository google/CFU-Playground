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
16 values per pixel. We call these groups of 16 bytes a "block". Each block
fits exactly in 4 words (4 bytes * 4 bytes/word = 16 bytes). Blocks are each
spread across the four LRAMs, beginning in LRAM 0.

In this main mode, four words are fetched concurrently, one word for each of
four separate pixels. This produces four separate streams of pixel data.

Each stream of pixel data corresponds to the input data for the calculation of
a channel of an output pixel in a Conv2D operation. It therefore requires
fetching data for a 4x4 group of pixels.In the X direction, the blocks of
pixel data are sequential - data for pixels (1, 0) is directly after pixel
(0,0). The following table shows the memory access pattern at the beginning
of a fetch of four pixels.

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

TODO:
- handle padding in y or x directions

TODO: An alternate mode to deal with input layers
- one channel per input
- probably padding to include
- stride 2 in both directions
- no need to cross row boundaries
"""

from nmigen import Mux, Signal, unsigned
from nmigen_cfu.util import SimpleElaboratable

from .utils import delay


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


class RoundRobin4(SimpleElaboratable):
    """Connects four sets of input and output signals to each other in turn.

    Each input is connected to an output, but that output rotates on
    each cycle. There are four ways in which connections are made,
    indicated by the 'phase' signal.

    +-------+-------+-------+-------+-------+
    | Phase | out 0 | out 1 | out 2 | out 3 |
    +-------+-------+-------+-------+-------+
    |    0  |   0   |   3   |   2   |   1   |
    |    1  |   1   |   0   |   3   |   2   |
    |    2  |   2   |   1   |   0   |   3   |
    |    3  |   3   |   2   |   1   |   0   |
    +-------+-------+-------+-------+-------+

    Parameters
    ----------

    shape: Shape
        The shape of the four signals to be connected

    Attributes
    ----------

    mux_in: [Signal(shape) * 4], in
        The incoming signals.

    mux_out: [Signal(shape) * 4], out
        The incoming signals connected as per the current phase.

    phase: Signal(range(4)), out
        The current phase, indicating which signal is connected to
        which output.

    start: Signal(), in
        Resets phase to 0 on next cycle.
    """

    def __init__(self, *, shape):
        self.mux_in = [Signal(shape, name=f"in_{i}") for i in range(4)]
        self.mux_out = [Signal(shape, name=f"out_{i}") for i in range(4)]
        self.phase = Signal(range(4))
        self.start = Signal()

    def elab(self, m):
        # phase is a free running counter with reset
        m.d.sync += self.phase.eq(self.phase + 1)
        with m.If(self.start):
            m.d.sync += self.phase.eq(0)

        # Connect outputs to inputs depending on phase
        def connect_for_phase(p):
            for i in range(4):
                m.d.comb += self.mux_out[i].eq(self.mux_in[(p - i) % 4])
        with m.Switch(self.phase):
            for p in range(4):
                with m.Case(p):
                    connect_for_phase(p)


class ValueAddressGenerator(SimpleElaboratable):
    """Generates addresses within a single pixel.

    Specifically for a 4x4 2DConv, works with a PixelAddressGenerator to find
    addresses of individual values. It reads `columns` * 4 * 32bit words,
    then moves down and repeats this three times.

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


class InputFetcher(SimpleElaboratable):
    """Fetches input vectors for Conv2D.

    Coordinates a "normal mode" input fetch, where input data depth is a
    multiple of 16.

    This is a free-running component which synchronizes its start when
    "start" is pulsed high.


    Attributes
    ----------

    start: Signal, in
        Pulsed to reset and restart logic with the given numbers. There is
        a delay of __ cycles between start and the first valid data produced.

    base_addr: Signal(14), in
        A base number, added to all results

    num_pixels_x: Signal(9), in
        How many pixels in a row

    num_blocks_x: Signal(4), in
        Number of RAM blocks to advance to move to new pixel in X direction

    num_blocks_y: Signal(8), in
        Number of RAM blocks  to advance between pixels in Y direction

    depth: Signal(3), in
        Number of 16-byte blocks to read per pixel. Max depth is 7 which is 112
        values/pixel). Total number of cycles per output pixel is
        depth * (4 cycles/block) * 4 (x dim) * 4 (y dim) = 64 * depth.

    lram_addr: [Signal(14)] * 4, out
        Address for each LRAM bank

    lram_data: [Signal(32)] * 4, in
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
        self.start = Signal()
        self.base_addr = Signal(14)
        self.num_pixels_x = Signal(9)
        self.num_blocks_x = Signal(4)
        self.num_blocks_y = Signal(8)
        self.depth = Signal(3)
        self.lram_addr = [Signal(14, name=f"lram_addr{i}") for i in range(4)]
        self.lram_data = [Signal(32, name=f"lram_data{i}") for i in range(4)]
        self.data_out = [Signal(32, name=f"data_out{i}") for i in range(4)]
        self.first = Signal()
        self.last = Signal()

    def elab(self, m):
        m.submodules["pixel_ag"] = pixel_ag = PixelAddressGenerator()
        m.submodules["rraddr"] = rr_addr = RoundRobin4(shape=unsigned(14))
        m.submodules["rrdata"] = rr_data = RoundRobin4(shape=unsigned(32))
        value_ags = [ValueAddressGenerator() for _ in range(4)]
        for i, v in enumerate(value_ags):
            m.submodules[f"value_ag{i}"] = v

        # Connect pixel address generator inputs
        m.d.comb += [
            pixel_ag.base_addr.eq(self.base_addr),
            pixel_ag.num_pixels_x.eq(self.num_pixels_x),
            pixel_ag.num_blocks_x.eq(self.num_blocks_x),
            pixel_ag.num_blocks_y.eq(self.num_blocks_y),
        ]

        # Connect value address generators
        for i, v in enumerate(value_ags):
            m.d.comb += [
                v.start_addr.eq(pixel_ag.addr),
                v.depth.eq(self.depth),
                v.num_blocks_y.eq(self.num_blocks_y),
                rr_addr.mux_in[i].eq(v.addr_out),
            ]

        # Connect round robins to LRAM and data output
        for i in range(4):
            m.d.comb += [
                self.lram_addr[i].eq(rr_addr.mux_out[i]),
                rr_data.mux_in[i].eq(self.lram_data[i]),
                self.data_out[i].eq(rr_data.mux_out[i]),
            ]

        # Sequence start signals to PixelAddressGenerator and round robins
        starts = delay(m, self.start, 1)
        m.d.comb += [
            pixel_ag.start.eq(starts[0]),
            rr_addr.start.eq(starts[0]),
            rr_data.start.eq(starts[1]),
        ]

        # cycle_counter counts cycles through reading input data
        max_cycle_counter = Signal(9)
        m.d.comb += max_cycle_counter.eq((self.depth << 6) - 1)
        cycle_counter = Signal(9)

        # Restart counter on start
        with m.If(self.start):
            m.d.sync += cycle_counter.eq(0)
        with m.Else():
            rollover = cycle_counter == max_cycle_counter
            m.d.sync += cycle_counter.eq(Mux(rollover, 0, cycle_counter + 1))
        next_pixel = 0
        for i in range(4):
            start_gen = Signal()
            m.d.comb += start_gen.eq(cycle_counter == i)
            m.d.comb += value_ags[i].start.eq(start_gen)
            next_pixel |= start_gen
        m.d.comb += pixel_ag.next.eq(next_pixel)

        # Generate first and last signals
        m.d.sync += [
            self.first.eq(cycle_counter == 0),
            self.last.eq(cycle_counter == max_cycle_counter),
        ]
