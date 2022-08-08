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

from amaranth import Cat, Mux, Signal

from .ram_mux import RamMux
from ..util import SimpleElaboratable
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
        pixel_row_begin_addr = Signal(18)
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


class ValueAddressGenerator(SimpleElaboratable):
    """Generates addresses of values of even pixels.

    Produces first the start address of a pixel, then addresses on the next
    three rows, thus identifying the 4 words that form the 16 values of the
    pixel.

    The values of odd pixels are at the same address but offset by two bytes.

    Attributes
    ----------

    reset: Signal, in
        Stops the address generator.

    start: Signal, in
        Begin generating addresses from the start_addr.

    start_addr: Signal(18), in
        Address of start of first pixel, from an EvenPixelAddressGenerator.

    first: Signal, out
        Indicates that first address in cycle is being produced.

    last: Signal, out
        Indicates that the last address is being produced and a new start
        address is required on the following cycle.

    addr_out: Signal(14), out
        Current output address
    """

    # Bytes per row
    INCREMENT_Y = 322

    def __init__(self):
        self.reset = Signal()
        self.start = Signal()
        self.start_addr = Signal(18)
        self.first = Signal()
        self.last = Signal()
        self.addr_out = Signal(18)

    def elab(self, m):
        running = Signal()
        count = Signal(2)
        with m.If(running):
            m.d.sync += count.eq(count + 1)  # Allow rollover

        next_row = Signal(18)
        m.d.comb += self.addr_out.eq(Mux(count == 0,
                                         self.start_addr, next_row))
        m.d.sync += next_row.eq(self.addr_out + self.INCREMENT_Y)
        m.d.comb += self.first.eq(running & (count == 0))
        m.d.comb += self.last.eq(running & (count == 3))

        with m.If(self.start):
            m.d.sync += running.eq(True)
            m.d.sync += count.eq(0)
        with m.If(self.reset):
            m.d.sync += running.eq(False)
            m.d.sync += count.eq(0)


class ValueReader(SimpleElaboratable):
    """Given an address, reads values from a RamMux.

    Reads six bytes, returning the values as two, 32 bit words.

    Attributes
    ----------

    addr: Signal(18), in
        Address from which to read two values. Expected to be an even number

    ram_mux_phase: Signal(range(4)), out
        The phase provided to the RamMux

    ram_mux_addr: [Signal(14)] * 4, out
        Addresses to send to the RAM Mux

    ram_mux_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.

    data_out: [Signal(32)] * 2, out
        Data for each of two output pixels. The second word is delayed by one
        cycle to match expected timing of the SystolicArray.
    """

    def __init__(self):
        self.addr = Signal(18)
        self.ram_mux_phase = Signal(range(4))
        self.ram_mux_addr = [Signal(14, name=f"rm_addr{i}") for i in range(4)]
        self.ram_mux_data = [Signal(32, name=f"rm_data{i}") for i in range(4)]
        self.data_out = [Signal(32, name=f"data_out{i}") for i in range(2)]

    def elab(self, m):
        # This code covers 8 cases, determined by bits 1, 2 and 3 of self.addr.
        # First, bit 2 and 3 are used to select the appropriate ram_mux phase
        # and addresses in order to read the two words containing the required
        # data via channels 0 and 3 of the RAM Mux. Once the two words have been
        # retrieved, six bytes are selected from those two words based on the
        # value of bit 1 of self.addr.

        # Uses just two of the mux channels - 0 and 3
        # For convenience, tie the unused addresses to zero
        m.d.comb += self.ram_mux_addr[1].eq(0)
        m.d.comb += self.ram_mux_addr[2].eq(0)

        # Calculate block addresses of the two words - second word may cross 16
        # byte block boundary
        block = Signal(14)
        m.d.comb += block.eq(self.addr[4:])
        m.d.comb += self.ram_mux_addr[0].eq(block)
        m.d.comb += self.ram_mux_addr[3].eq(
            Mux(self.ram_mux_phase == 3, block + 1, block))

        # Use phase to select the two required words to channels 0 & 3
        m.d.comb += self.ram_mux_phase.eq(self.addr[2:4])

        # Select correct three half words when data is available, on cycle after
        # address received.
        byte_sel = Signal(1)
        m.d.sync += byte_sel.eq(self.addr[1])
        d0 = self.ram_mux_data[0]
        d3 = self.ram_mux_data[3]
        dmix = Signal(32)
        m.d.comb += dmix.eq(Cat(d0[16:], d3[:16]))
        with m.If(byte_sel == 0):
            m.d.comb += self.data_out[0].eq(d0)
            m.d.sync += self.data_out[1].eq(dmix)
        with m.Else():
            m.d.comb += self.data_out[0].eq(dmix)
            m.d.sync += self.data_out[1].eq(d3)


class Mode0InputFetcher(SimpleElaboratable):
    """Fetches input vectors for Mode0 Conv2D.

    Attributes
    ----------

    reset: Signal, in
        Pulsed to stop producing values. This ensures that invalid first
        and last signals are not produced.

    start: Signal, in
        Pulsed to begin producing data. There is a delay of 2 cycles between
        the start signal and the first valid data being produced.

    base_addr: Signal(18), in
        A base byte address, added to all results

    ram_mux_phase: Signal(range(4)), out
        The phase provided to the RamMux

    ram_mux_addr: [Signal(14)] * 4, out
        Addresses to send to the RAM Mux

    ram_mux_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.

    data_out: [Signal(32)] * 2, out
        Data for each of two pixels.

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
        self.ram_mux_phase = Signal(range(4))
        self.ram_mux_addr = [Signal(14, name=f"rm_addr{i}") for i in range(4)]
        self.ram_mux_data = [Signal(32, name=f"rm_data{i}") for i in range(4)]
        self.data_out = [Signal(32, name=f"data_out{i}") for i in range(4)]
        self.first = Signal()
        self.last = Signal()

    def elab(self, m):
        # Generate pixel addresses
        m.submodules["pixel_ag"] = pixel_ag = EvenPixelAddressGenerator()
        m.d.comb += pixel_ag.base_addr.eq(self.base_addr),
        m.d.comb += pixel_ag.start.eq(self.start),

        # Generate value addresses from each pixel
        m.submodules["value_ag"] = value_ag = ValueAddressGenerator()
        m.d.comb += value_ag.reset.eq(self.reset),
        m.d.comb += value_ag.start.eq(self.start),
        m.d.comb += value_ag.start_addr.eq(pixel_ag.addr)
        m.d.comb += pixel_ag.next.eq(value_ag.last)

        # Read values from given address
        m.submodules["reader"] = reader = ValueReader()
        m.d.comb += reader.addr.eq(value_ag.addr_out)
        m.d.comb += self.ram_mux_phase.eq(reader.ram_mux_phase)
        for i in range(4):
            m.d.comb += self.ram_mux_addr[i].eq(reader.ram_mux_addr[i])
            m.d.comb += reader.ram_mux_data[i].eq(self.ram_mux_data[i])
        m.d.comb += self.data_out[0].eq(reader.data_out[0])
        m.d.comb += self.data_out[1].eq(reader.data_out[1])
        m.d.comb += self.data_out[2].eq(0)
        m.d.comb += self.data_out[3].eq(0)

        # Delay first and last by one cycle to match data output
        m.d.sync += self.first.eq(value_ag.first)
        m.d.sync += self.last.eq(value_ag.last)
