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


from nmigen import Signal, Mux
from nmigen_cfu import SimpleElaboratable

from .registerfile import Xetter


class ParamStoreSetter(Xetter):
    """Stores into a ParamStore.

    Parameters
    ----------
    width:
        bits in each word of memory
    depth:
        Maximum number of items stored in memory

    Public Interface
    ----------------
    w_en: Signal output
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

    def __init__(self, width, depth):
        super().__init__()
        self.w_en = Signal()
        self.w_addr = Signal(range(depth))
        self.w_data = Signal(width)
        self.restart = Signal()
        self.count = Signal.like(self.w_addr)

    def elab(self, m):
        m.d.comb += [
            self.done.eq(True),
            self.w_addr.eq(self.count)
        ]
        with m.If(self.start):
            m.d.comb += [
                self.w_en.eq(1),
                self.w_data.eq(self.in0),
            ]
            m.d.sync += self.count.eq(self.count + 1)


class CircularIncrementer(SimpleElaboratable):
    """Does circular increments of a memory address counter.

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
