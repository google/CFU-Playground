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

from amaranth import Cat, Memory, Module, Signal
from amaranth_cfu.util import SimpleElaboratable


class WideReadMemory(SimpleElaboratable):
    """A memory that may be read 128 bits per cycle.

    Writes to the memory are with 32 bit words, while read accesses read
    four words concurrently.

    Only a read or a write may take place on any cycle. In the event of
    simultaneous writes and reads, the write takes precedence.

    Parameters
    ----------
    depth: int
      The number of words. Must be a positive multiple of four.

    Attributes
    ----------
    write_addr: Signal(range(depth)), in
      The address to which to write
    write_data: Signal(32), in
      The data to write
    write_enable: Signal(), in
      Write enable when set then data is written to the memory.
    read_addr: Signal(range(depth / 4)), in
      The address to read four words from. Lower two bits of words address
      are not present since all four words are retrieved.
    read_data: Signal(128), out
      The four 32 bit words read from memory. Data is available the cycle
      after the read_addr is placed on the bus
    """

    def __init__(self, depth):
        self._depth = depth
        self.write_addr = Signal(range(depth))
        self.write_data = Signal(32)
        self.write_enable = Signal()
        self.read_addr = Signal(range(depth // 4))
        self.read_data = Signal(128)

    def elab(self, m: Module):
        rp_data = []
        for i in range(4):
            mem = Memory(depth=self._depth // 4, width=32)
            # Set up read port
            m.submodules[f'rp_{i}'] = rp = mem.read_port(transparent=False)
            rp_data.append(rp.data)
            m.d.comb += rp.addr.eq(self.read_addr)
            m.d.comb += rp.en.eq(~self.write_enable)

            # Set up write port
            m.submodules[f'wp_{i}'] = wp = mem.write_port()
            m.d.comb += wp.addr.eq(self.write_addr[2:])
            m.d.comb += wp.data.eq(self.write_data)
            m.d.comb += wp.en.eq(self.write_enable &
                                 (i == self.write_addr[:2]))

        # Assemble all of the read port outputs into one, 128bit wide signal
        m.d.comb += self.read_data.eq(Cat(rp_data))
