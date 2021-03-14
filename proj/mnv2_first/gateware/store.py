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

from nmigen import Array, Signal, Mux

from nmigen_cfu import SimpleElaboratable

from .registerfile import Xetter


class StoreSetter(Xetter):
    """Stores in0 into a Store.

    Parameters
    ----------
    bits_width:
        bits in each word of memory
    num_memories:
        number of memories in the store. data will be striped over the memories.
        Assumed to be a power of two.
    depth:
        Maximum number of items stored in each memory.

    Public Interface
    ----------------
    w_en: Signal(1)[num_memories] output
        Memory write enable
    w_addr: Signal(range(depth)) output
        Memory address to which to write
    w_data: Signal(width) output
        Data to write
    restart: Signal input
        Signal to drop all parameters from memory and restart all counters.
    count: Signal(range(depth)) output
        How many items the memory currently holds
    """

    def __init__(self, bits_width, num_memories, depth):
        super().__init__()
        assert 0 == ((num_memories - 1) &
                     num_memories), "Num memories (f{num_memories}) not a power of two"
        self.num_memories_bits = (num_memories - 1).bit_length()
        self.w_en = Array(Signal() for _ in range(num_memories))
        self.w_addr = Signal(range(depth))
        self.w_data = Signal(bits_width)
        self.restart = Signal()
        self.count = Signal(range(depth * num_memories))

    def connect_write_port(self, dual_port_memories):
        """Connects the write port of a list of dual port memories to this.

        Returns a list of statements that perform the connection.
        """
        assert len(dual_port_memories) == len(
            self.w_en), f"Memory length does not match: {dual_port_memories}, {len(self.w_en)}"
        statement_list = []
        for w_en, dp in zip(self.w_en, dual_port_memories):
            statement_list.extend([
                dp.w_en.eq(w_en),
                dp.w_addr.eq(self.w_addr),
                dp.w_data.eq(self.w_data),
            ])
        return statement_list

    def elab(self, m):
        m.d.comb += [
            self.done.eq(True),
            self.w_addr.eq(self.count[self.num_memories_bits:])
        ]
        with m.If(self.restart):
            m.d.sync += self.count.eq(0)
        with m.Elif(self.start):
            m.d.comb += [
                self.w_en[self.count[:self.num_memories_bits]].eq(1),
                self.w_data.eq(self.in0),
            ]
            m.d.sync += self.count.eq(self.count + 1)


class CircularIncrementer(SimpleElaboratable):
    """Does circular increments of a memory address counter over a single memory
    range.

    Parameters
    ----------
    depth:
        Maximum number of items stored in memory

    Public Interface
    ----------------
    restart: Signal input
        Signal to reset address to zero
    next: Signal input
        Produce next piece of data (available next cycle).
    limit: Signal(range(depth))) input
        Number of items stored in memory
    r_addr: Signal(range(depth)) output
        Next address
    """

    def __init__(self, depth):
        self.depth = depth
        self.restart = Signal()
        self.next = Signal()
        self.limit = Signal(range(depth))
        self.r_addr = Signal(range(depth))

    def elab(self, m):
        # Current r_addr is the address being presented to memory this cycle
        # By default current address is last address, but this can be
        # modied by the reatart or next signals
        last_addr = Signal.like(self.r_addr)
        m.d.sync += last_addr.eq(self.r_addr)
        m.d.comb += self.r_addr.eq(last_addr)

        # Respond to inputs
        with m.If(self.restart):
            m.d.comb += self.r_addr.eq(0)
        with m.Elif(self.next):
            m.d.comb += self.r_addr.eq(Mux(last_addr >=
                                           self.limit - 1, 0, last_addr + 1))


class FilterValueGetter(Xetter):
    """Gets next word from 4-way filter value store.

    This is a temporary getter. The full accelerator will use filter values internally.

    Parameters
    ----------
    num_memories:
        number of memories in the store. data will be striped over the memories.
        Assumed to be a power of two
    depth:
        Maximum number of items stored in each memory

    Public Interface
    ----------------
    r_addr: Signal(range(depth/num_memories)) output
        Current read pointer
    r_bank: Signal(range(num_memories)) output
        Which of the memories to get from
    restart: Signal() input
    """

    def __init__(self, num_memories, depth):
        super().__init__()
        assert 0 == ((num_memories - 1) &
                     num_memories), "Num memories (f{num_memories}) not a power of two"
        self.num_memories = num_memories
        self.r_addr = Signal(range(depth))
        self.r_bank = Signal(range(num_memories))
        self.limit = Signal(range(self.num_memories * depth))
        self.restart = Signal()

    def connect_read_port(self, dual_port_memories):
        """Connect read ports of a list of dual port memories to self.

        Returns a list of statements that perform the connection.
        """
        result = [dp.r_addr.eq(self.r_addr) for dp in dual_port_memories]
        r_datas = Array(dp.r_data for dp in dual_port_memories)
        result.append(self.output.eq(r_datas[self.r_bank]))
        return result

    def elab(self, m):
        num_memories_bits = (self.num_memories - 1).bit_length()
        count = Signal.like(self.limit)
        count_at_limit = count == (self.limit - 1)
        m.d.comb += [
            self.done.eq(True),
            self.r_addr.eq(count[num_memories_bits:]),
            self.r_bank.eq(count[:num_memories_bits]),
        ]
        with m.If(self.restart):
            m.d.sync += count.eq(0)
        with m.Elif(self.start):
            m.d.sync += count.eq(Mux(count_at_limit, 0, count + 1))
