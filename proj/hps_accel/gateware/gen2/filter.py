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

"""Gateware for filter storage."""

from amaranth import Mux, Signal, unsigned

from ..stream import Endpoint
from .constants import Constants
from .mem import SinglePortMemory
from ..util import SequentialMemoryReader, SimpleElaboratable
from .utils import unsigned_upto


FILTER_WRITE_COMMAND = [
    ('store', range(Constants.NUM_FILTER_STORES)),
    ('addr', range(Constants.FILTER_WORDS_PER_STORE)),
    ('data', unsigned(32)),
]


class FilterStore(SimpleElaboratable):
    """Stores words in a single port memory.

    The filter store contains multiple SinglePortMemories, each of which is
    written separately with values in the order required by the SystolicArray.

    Attributes
    ----------

    write_input: Endpoint(FILTER_WRITE_COMMAND), in
        Commands to write to the filter store. Always ready.

    size: Signal(unsigned_upto(depth)), in
        Number of words held in each filter store

    values_out[i]: [Signal(32) * num_memories], out
        Filter values output in the correct manner for a Systolic Array

    start: Signal(), in
        Causes filter output to begin with addr(0), on cycle after next.
    """

    def __init__(self):
        self.write_input = Endpoint(FILTER_WRITE_COMMAND)
        self.size = Signal(unsigned_upto(Constants.FILTER_WORDS_PER_STORE))
        self.values_out = [Signal(32, name=f"out_{i}")
                           for i in range(Constants.NUM_FILTER_STORES)]
        self.start = Signal()

    def elab(self, m):
        # Read_index tracks the address for memory 0
        # self.start starts the address incrementing and reset stops it.
        read_index = Signal(range(Constants.FILTER_WORDS_PER_STORE))
        running = Signal()
        with m.If(running):
            m.d.sync += read_index.eq(Mux(read_index == self.size - 1,
                                          0, read_index + 1))
        with m.If(self.start):
            m.d.sync += running.eq(True)
            m.d.sync += read_index.eq(0)

        # set up each memory
        for i in range(Constants.NUM_FILTER_STORES):
            m.submodules[f"mem{i}"] = mem = SinglePortMemory(
                data_width=32, depth=Constants.FILTER_WORDS_PER_STORE)
            # Handle writes to memory
            inp = self.write_input
            m.d.comb += [
                mem.write_enable.eq(inp.valid & (inp.payload.store == i)),
                mem.write_addr.eq(inp.payload.addr),
                mem.write_data.eq(inp.payload.data),
            ]
            # Do reads continuously
            if i == 0:
                # i == 0 treated separately to avoid verilator warnings
                # (and save a few LUTs and FFs)
                m.d.comb += mem.read_addr.eq(read_index)
            else:
                addr = Signal(range(-i, Constants.FILTER_WORDS_PER_STORE),
                              name=f"addr_{i}")
                m.d.comb += addr.eq(read_index - i)
                m.d.comb += mem.read_addr.eq(Mux(addr >= 0,
                                                 addr, addr + self.size))
            m.d.comb += self.values_out[i].eq(mem.read_data)

        # Always ready to receive more data
        m.d.comb += self.write_input.ready.eq(1)
