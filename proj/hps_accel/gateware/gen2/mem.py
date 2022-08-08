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

"""Simple memory wrapper"""

from amaranth import Memory, Mux, Signal, unsigned

from ..stream import Endpoint
from ..util import SimpleElaboratable
from .utils import unsigned_upto


class SinglePortMemory(SimpleElaboratable):
    """A single port r/w RAM.

    Intended to be used such that reads and writes do not conflict. If a
    write occurs at the same time as a read, the write takes precedence,
    and the output data is invalid.

    This is a simple wrapper for the amaranth library Memory, and in future
    may be replaced with an implementation based on FPGA-specific
    primitives.

    Parameters
    ----------

    data_width: int
        Number of bits in each memory word.

    depth: int
        Number of words in the memory. There will be ceil(log2(depth))
        bits in the memories address.

    Attributes
    ----------

    write_addr: Signal(addr_width), in
        The address to which to write data. As noted above, addr_width is
        ceil(log2(depth)).

    write_data: Signal(data_width), in
        The data to be written.

    write_enable: Signal(1), in
        When asserted, write_data is written to write_addr. When not
        asserted data is read.

    read_addr: Signal(addr_width), in
        The address to read from.

    read_data: Signal(word_width), out
        The data corresponding to the read_addr on the previous cycle.
        Only valid if write_enable was not asserted.
    """

    def __init__(self, data_width, depth):
        self._data_width = data_width
        self._depth = depth
        addr_width = (depth - 1).bit_length()

        self.write_addr = Signal(addr_width)
        self.write_data = Signal(data_width)
        self.write_enable = Signal()
        self.read_addr = Signal(addr_width)
        self.read_data = Signal(data_width)

    def elab(self, m):
        memory = Memory(width=self._data_width, depth=self._depth)
        m.submodules.rp = rp = memory.read_port(transparent=False)
        m.submodules.wp = wp = memory.write_port()

        m.d.comb += [
            wp.en.eq(self.write_enable),
            rp.en.eq(~self.write_enable),
            wp.addr.eq(self.write_addr),
            wp.data.eq(self.write_data),
            rp.addr.eq(self.read_addr),
            self.read_data.eq(rp.data)
        ]


class LoopingCounter(SimpleElaboratable):
    """Loops over values from 0 to (count-1).

    Parameters
    ----------

    max_count: int
        Maximum value of the count attribute.


    Attributes
    ----------

    count: Signal(max=max_count), in
        Number of items to count.

    reset: Signal(), in
        Pulse to cause value to go back to zero on next cycle.

    value: Signal(max=max_count-1), out
        Current value of count.

    next: Signal(), in
        Causes count to increment on next cycle

    last: Signal(), out
        High when counter is about to loop
    """

    def __init__(self, max_count):
        self._max_count = max_count

        self.count = Signal(max_count.bit_length())
        self.reset = Signal()
        self.value = Signal((max_count - 1).bit_length())
        self.next = Signal()
        self.last = Signal()

    def elab(self, m):

        with m.If(self.reset):
            m.d.sync += self.value.eq(0)

        with m.Else():
            value_p1 = Signal.like(self.count)
            next_value = Signal.like(self.value)
            m.d.comb += [
                value_p1.eq(self.value + 1),
                self.last.eq(value_p1 == self.count),
                next_value.eq(Mux(self.last, 0, value_p1)),
            ]
            with m.If(self.next):
                m.d.sync += self.value.eq(next_value)


LDR_PARAMS_LAYOUT = [
    ('count', unsigned(16)),
    ('repeats', unsigned(4)),
]


class LoopingAddressGenerator(SimpleElaboratable):
    """Generates addresses from a memory.

    Loops from address zero for a given count, with configurable
    number of repeats.

    Parameters
    ----------

    depth: int
        Number of words in the memory being addressed. Maximum
        value for count attribute also determines addr_width.

    max_repeats: int
        Maximum value for repeats.

    Attributes
    ----------

    params: Endpoint(LDR_PARAMS_LAYOUT)), in
        Sets the maximum count of addresses and number of repeats
        required. Always ready to receive a value. When new parameters
        are set, the output reset to first value in memory.

    next: Signal(), in
        Indicates next value should be presented on next cycle.

    addr: Signal(addr_width), out
        Output read address.
    """

    def __init__(self, *, depth, max_repeats):
        self._depth = depth
        self._max_repeats = max_repeats

        self.params_input = Endpoint(LDR_PARAMS_LAYOUT)
        self.next = Signal()

        addr_width = (depth - 1).bit_length()
        self.addr = Signal(addr_width)

    def elab(self, m):
        # Define parameters
        repeats = Signal(unsigned_upto(self._max_repeats))
        count = Signal(unsigned_upto(self._depth))

        # Accept new parameters
        m.d.comb += self.params_input.ready.eq(1)
        with m.If(self.params_input.valid):
            m.d.sync += [
                repeats.eq(self.params_input.payload.repeats),
                count.eq(self.params_input.payload.count),
            ]

        # Count repeats
        m.submodules.rc = repeat_counter = LoopingCounter(self._max_repeats)
        m.d.comb += [
            repeat_counter.count.eq(repeats),
            repeat_counter.reset.eq(self.params_input.valid),
            repeat_counter.next.eq(self.next),
        ]

        # Count addresses
        m.submodules.ac = addr_counter = LoopingCounter(self._depth)
        m.d.comb += [
            addr_counter.count.eq(count),
            addr_counter.reset.eq(self.params_input.valid),
            addr_counter.next.eq(self.next & repeat_counter.last),
            self.addr.eq(addr_counter.value),
        ]
