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

from nmigen import Memory, Signal
from nmigen_cfu.util import SimpleElaboratable


class SinglePortMemory(SimpleElaboratable):
    """A single port r/w RAM.

    Intended to be used such that reads and writes do not conflict. If a
    write occurs at the same time as a read, the write takes precedence,
    and the output data is invalid.

    This is a simple wrapper for the nmigen library Memory, and in future
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
