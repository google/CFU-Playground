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

from amaranth import Array, Signal, Mux, Cat

from amaranth_cfu import SimpleElaboratable, is_pysim_run, DualPortMemory, SequentialMemoryReader

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
        Memory write enable.
    w_addr: Signal(range(depth)) output
        Memory address to which to write
    w_data: Signal(width) output
        Data to write
    restart: Signal input
        Signal to drop all parameters from memory and restart all counters.
    count: Signal(range(depth*num_memories+1)) output
        How many items the memory currently holds
    updated: Signal() output
        Indicates that store has been updated with a new value or restarted
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
        self.count = Signal(range(depth * num_memories + 1))
        self.updated = Signal()

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
            self.w_addr.eq(self.count[self.num_memories_bits:]),
            self.updated.eq(Cat(self.w_en).any() | self.restart),
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


class FilterValueFetcher(SimpleElaboratable):
    """Fetches next single word from a 4-way filter value store.

    Parameters
    ----------
    max_depth:
        Maximum number of items stored in each memory

    Public Interface
    ----------------
    limit: Signal(range(depth)) input
        Number of entries currently contained in the filter store, divided by 4
    mem_addr: Signal(range(depth/num_memories))[4] output
        Current read pointer for each memory
    mem_data: Signal(range(depth/num_memories))[4] input
        Current value being read from each memory
    data: Signal(32)[4] output
        Four words being fetched
    next: Signal() input
        Indicates that fetched value has been read.
    updated: Signal() input
        Indicates that memory store has been updated, and processing should start at start
    restart: Signal() input
        Soft reset signal to restart all processing
    """

    def __init__(self, max_depth):
        super().__init__()
        self.max_depth = max_depth
        self.limit = Signal(range(max_depth * 4))
        self.mem_addrs = [
            Signal(
                range(max_depth),
                name=f"mem_addr_{n}") for n in range(4)]
        self.mem_datas = [Signal(32, name=f"mem_data_{n}") for n in range(4)]
        self.data = Signal(32)
        self.next = Signal()
        self.updated = Signal()
        self.restart = Signal()

        self.smrs = [
            SequentialMemoryReader(
                width=32,
                max_depth=max_depth) for _ in range(4)]

    def connect_read_ports(self, dual_port_memories):
        """Helper method to connect a list of dual port memories to self.

        Returns a list of statements that perform the connection.
        """
        result = []
        for mem_addr, mem_data, dpm in zip(
                self.mem_addrs, self.mem_datas, dual_port_memories):
            result += [
                dpm.r_addr.eq(mem_addr),
                mem_data.eq(dpm.r_data),
            ]
        return result

    def elab(self, m):
        was_updated = Signal()
        m.d.sync += was_updated.eq(self.updated)
        # Connect sequential memory readers
        smr_datas = Array([Signal(32, name=f"smr_data_{n}") for n in range(4)])
        smr_nexts = Array([Signal(name=f"smr_next_{n}") for n in range(4)])
        for n, (smr, mem_addr, mem_data, smr_data, smr_next) in enumerate(
                zip(self.smrs, self.mem_addrs, self.mem_datas, smr_datas, smr_nexts)):
            m.submodules[f"smr_{n}"] = smr
            m.d.comb += [
                smr.limit.eq(self.limit >> 2),
                mem_addr.eq(smr.mem_addr),
                smr.mem_data.eq(mem_data),
                smr_data.eq(smr.data),
                smr.next.eq(smr_next),
                smr.restart.eq(was_updated),
            ]

        curr_bank = Signal(2)
        m.d.comb += self.data.eq(smr_datas[curr_bank])

        with m.If(self.restart):
            m.d.sync += curr_bank.eq(0)
        with m.Elif(self.next):
            m.d.comb += smr_nexts[curr_bank].eq(1)
            m.d.sync += curr_bank.eq(curr_bank + 1)


class NextWordGetter(Xetter):
    """Gets the next word from a store.

    Public Interface
    ----------------
    data: Signal(32) input
        The current value to be fetched
    next: Signal() output
        Indicates that fetched value has been read.
    ready: Signal() input
        Signal from the store that data is valid. The read only completes when ready is true.
    """

    def __init__(self):
        super().__init__()
        self.data = Signal(32)
        self.next = Signal()
        self.ready = Signal()

    def elab(self, m):
        waiting = Signal()
        with m.If(self.ready & (waiting | self.start)):
            m.d.comb += [
                self.output.eq(self.data),
                self.next.eq(1),
                self.done.eq(1),
            ]
            m.d.sync += waiting.eq(0)
        with m.Elif(self.start & ~self.ready):
            m.d.sync += waiting.eq(1)


class InputStore(SimpleElaboratable):
    """Stores one "pixel" of input values for processing.

    This store is double-buffered so that processing may continue
    on one buffer while data is being loaded onto the other.

    All channels for a single pixel of data are written once, then
    read many times. Reads are performed circularly over the input
    data.

    Attributes
    ----------
    max_depth: int
        maximum allowed input depth.
        Assumed to be power of two.

    Public Interface
    ----------------
    restart: Signal() input
        Resets component to known state to begin processing.
    input_depth: Signal(range(max_depth * 4 // 2)) input
        Number of words per input pixel

    w_data: Signal(32) input
        Data to store
    w_en: Signal() input
        Hold high to store data - w_ready must also be high for data
        to be considered stored.
    w_ready: Signal() output
        Indicates that store is read to receive data.

    r_ready: Signal() output
        Indicates that data has been stored and reading is allowed
    r_data: Signal(32) output
        Four words of data
    r_next: Signal() input
        Data being read this cycle, so advance data pointer by one word next cycle
    r_finished: Signal() input
        Last data read this cycle, so move to next buffer on next cycle
    """

    def __init__(self, max_depth):
        super().__init__()
        self.max_depth = max_depth
        self.restart = Signal()
        self.input_depth = Signal(range(max_depth * 4 // 2))
        self.w_data = Signal(32)
        self.w_en = Signal()
        self.w_ready = Signal()
        self.r_ready = Signal()
        self.r_data = Signal(32)  # TODO: increase to 2 and 4 words
        self.r_next = Signal()
        self.r_finished = Signal()

    def _elab_read(self, m, dps, r_full):
        r_curr_buf = Signal()
        # Address within current buffer
        r_addr = Signal.like(self.input_depth)

        # Create and connect sequential memory readers
        smrs = [
            SequentialMemoryReader(
                max_depth=self.max_depth // 2,
                width=32) for _ in range(4)]
        for (n, dp, smr) in zip(range(4), dps, smrs):
            m.submodules[f"smr_{n}"] = smr
            m.d.comb += [
                dp.r_addr.eq(Cat(smr.mem_addr, r_curr_buf)),
                smr.mem_data.eq(dp.r_data),
                smr.limit.eq((self.input_depth + 3 - n) >> 2),
            ]

        smr_nexts = Array(smr.next for smr in smrs)

        # Ready if current buffer is full
        full = Signal()
        m.d.comb += full.eq(r_full[r_curr_buf])
        last_full = Signal()
        m.d.sync += last_full.eq(full)
        with m.If(full & ~last_full):
            m.d.sync += self.r_ready.eq(1)
            m.d.comb += [smr.restart.eq(1) for smr in smrs]

        # Increment address
        with m.If(self.r_next & self.r_ready):
            with m.If(r_addr == self.input_depth - 1):
                m.d.sync += r_addr.eq(0)
            with m.Else():
                m.d.sync += r_addr.eq(r_addr + 1)
            m.d.comb += smr_nexts[r_addr[:2]].eq(1)

        # Get data
        smr_datas = Array(smr.data for smr in smrs)
        m.d.comb += self.r_data.eq(smr_datas[r_addr[:2]])

        # On finished (overrides r_next)
        with m.If(self.r_finished):
            m.d.sync += [
                r_addr.eq(0),
                r_full[r_curr_buf].eq(0),
                last_full.eq(0),
                self.r_ready.eq(0),
                r_curr_buf.eq(~r_curr_buf),
            ]

        # On restart, reset addresses and Sequential Memory readers, go to not
        # ready
        with m.If(self.restart):
            m.d.sync += [
                r_addr.eq(0),
                last_full.eq(0),
                self.r_ready.eq(0),
                r_curr_buf.eq(0),
            ]

    def _elab_write(self, m, dps, r_full):
        w_curr_buf = Signal()
        # Address within current buffer
        w_addr = Signal.like(self.input_depth)

        # Connect to memory write port
        for n, dp in enumerate(dps):
            m.d.comb += [
                dp.w_addr.eq(Cat(w_addr[2:], w_curr_buf)),
                dp.w_data.eq(self.w_data),
                dp.w_en.eq(self.w_en & self.w_ready & (n == w_addr[:2])),
            ]
        # Ready to write current buffer if reading is not allowed
        m.d.comb += self.w_ready.eq(~r_full[w_curr_buf])

        # Write address increment
        with m.If(self.w_en & self.w_ready):
            with m.If(w_addr == self.input_depth - 1):
                # at end of buffer - mark buffer ready for reading and go to
                # next
                m.d.sync += [
                    w_addr.eq(0),
                    r_full[w_curr_buf].eq(1),
                    w_curr_buf.eq(~w_curr_buf),
                ]
            with m.Else():
                m.d.sync += w_addr.eq(w_addr + 1)

        with m.If(self.restart):
            m.d.sync += [
                w_addr.eq(0),
                w_curr_buf.eq(0),
            ]

    def elab(self, m):
        # Create the four memories
        dps = [
            DualPortMemory(
                depth=self.max_depth,
                width=32,
                is_sim=is_pysim_run()) for _ in range(4)]
        for n, dp in enumerate(dps):
            m.submodules[f"dp_{n}"] = dp

        # Tracks which buffers are "full" and ready for reading
        r_full = Array([Signal(name="r_full_0"), Signal(name="r_full_1")])
        with m.If(self.restart):
            m.d.sync += [
                r_full[0].eq(0),
                r_full[1].eq(0),
            ]

        # Track reading and writing
        self._elab_write(m, dps, r_full)
        self._elab_read(m, dps, r_full)


class InputStoreSetter(Xetter):
    """Puts a word into the input store.

    Public Interface
    ----------------
    w_data: Signal(32) input
        Data to send to input value store
    w_en: Signal() output
        Indicate ready to write data
    w_ready: Signal() input
        Indicates input store is ready to receive data
    """

    def __init__(self):
        super().__init__()
        self.w_data = Signal(32)
        self.w_en = Signal()
        self.w_ready = Signal()

    def connect(self, input_store):
        """Connect to self to input_store.

        Returns a list of statements that performs the connection.
        """
        return [
            input_store.w_data.eq(self.w_data),
            input_store.w_en.eq(self.w_en),
            self.w_ready.eq(input_store.w_ready),
        ]

    def elab(self, m):
        buffer = Signal(32)
        waiting = Signal()

        with m.If(self.start & self.w_ready):
            m.d.comb += [
                self.done.eq(1),
                self.w_en.eq(1),
                self.w_data.eq(self.in0)
            ]
        with m.Elif(self.start & ~self.w_ready):
            m.d.sync += [
                waiting.eq(1),
                buffer.eq(self.in0),
            ]
        with m.Elif(waiting & ~self.w_ready):
            m.d.comb += [
                self.done.eq(1),
                self.w_en.eq(1),
                self.w_data.eq(self.in0)
            ]
            m.d.sync += waiting.eq(1)
