#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
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

__package__ = 'nmigen_cfu'

from nmigen import Elaboratable, Module, Mux, Signal, Memory
from nmigen.build import Platform
from nmigen.hdl.ast import Cat
from nmigen.sim import Simulator

import unittest

# This global will be set by unittests to indicate that the test is
# being done in simulation
_IS_SIM_RUN = False


def is_pysim_run():
    return _IS_SIM_RUN


def tree_sum(l):
    """Sums a list of values in a tree rather than sequentially.

    This is helpful to some synthesis tools. Others automatically recognize
    a series of additions and build special, optimized logic.
    """
    l = list(l)
    if len(l) == 1:
        return l[0]
    half = len(l) // 2
    return tree_sum(l[:half]) + tree_sum(l[half:])


def all_words(signal, word_length):
    """Returns a longer signal as several word_length portions"""
    return (signal[i:i + word_length]
            for i in range(0, len(signal), word_length))


def pack_vals(a, b, c, d, offset=0):
    """Packs 4 byte values into a 32-bit word
    offset is subtracted from the values before storing
    """
    return (((a - offset) & 0xff)
            + (((b - offset) & 0xff) << 8)
            + (((c - offset) & 0xff) << 16)
            + (((d - offset) & 0xff) << 24))


class SimpleElaboratable(Elaboratable):
    """Simplified Elaboratable interface
    Widely, but not generally applicable. Suitable for use with
    straight-forward blocks of logic in a single domain.

    Attributes
    ----------

    m: Module
        The resulting module
    platform:
        The platform for this elaboration

    """

    def elab(self, m: Module):
        """Alternate elaborate interface"""
        return NotImplementedError()

    def elaborate(self, platform: Platform):
        self.m = Module()
        self.platform = platform
        self.elab(self.m)
        return self.m


class _DummySyncModule(SimpleElaboratable):
    """A module that does something arbirarty with synchronous logic

    This is used by TestBase to stop nMigen from complaining if our DUT doesn't
    contain any synchronous logic."""

    def elab(self, m):
        state = Signal(1)
        m.d.sync += state.eq(~state)


class TestBase(unittest.TestCase):
    """Base class for testing an nMigen module.

    The module can use sync, comb or both.
    """

    def setUp(self):
        # Ensure IS_SIM_RUN set
        global _IS_SIM_RUN
        _IS_SIM_RUN = True
        # Create DUT and add to simulator
        self.m = Module()
        self.dut = self.create_dut()
        self.m.submodules['dut'] = self.dut
        self.m.submodules['dummy'] = _DummySyncModule()
        self.sim = Simulator(self.m)

    def create_dut(self):
        """Returns an instance of the device under test"""
        raise NotImplementedError

    def add_process(self, process):
        """Add main test process to the simulator"""
        self.sim.add_sync_process(process)

    def add_sim_clocks(self):
        """Add clocks as required by sim.
        """
        self.sim.add_clock(1, domain='sync')

    def run_sim(self, process, write_trace=False):
        self.add_process(process)
        self.add_sim_clocks()
        if write_trace:
            with self.sim.write_vcd("zz.vcd", "zz.gtkw"):
                self.sim.run()
            # Discourage commiting code with tracing active
            self.fail("Simulation tracing active. "
                      "Turn off after debugging complete.")
        else:
            self.sim.run()


class ValueBuffer(SimpleElaboratable):
    """Buffers a signal.

    Parameters:
        inp: A Signal
            The signal to buffer
        capture: Signal(1)
            Input.
            When high, captures input while transparently placing on output.
            When low, output is equal to last captured input.

    Interface:
        output: Signal(like inp)
            Output. The last captured input.
    """

    def __init__(self, inp, capture):
        self.input = inp
        self.capture = capture
        self.output = Signal.like(inp)

    def elab(self, m):
        captured = Signal.like(self.input)
        with m.If(self.capture):
            m.d.sync += captured.eq(self.input)
        m.d.comb += self.output.eq(Mux(self.capture, self.input, captured))


class DualPortMemory(SimpleElaboratable):
    """A Dual port memory wrapper

    Parameters
    ----------
    depth:
        Maximum number of items stored in memory
    width:
        bits in each word of memory

    Public Interface
    ----------------
    w_en: Signal input
        Memory write enable
    w_addr: Signal(range(depth)) input
        Memory address to which to write
    w_data: Signal(width) input
        Data to write
    r_addr: Signal(range(depth)) input
        Address from which to read - data put on r_data at next cycle
    r_data: Signal(width) output
        Read data
    """

    def __init__(self, *, width, depth, is_sim):
        self.width = width
        self.depth = depth
        self.is_sim = is_sim
        self.w_en = Signal()
        self.w_addr = Signal(range(depth))
        self.w_data = Signal(width)
        self.r_addr = Signal(range(depth))
        self.r_data = Signal(width)

    def elab(self, m):
        mem = Memory(width=self.width, depth=self.depth, simulate=self.is_sim)
        m.submodules['wp'] = wp = mem.write_port()
        m.submodules['rp'] = rp = mem.read_port(transparent=False)
        m.d.comb += [
            wp.en.eq(self.w_en),
            wp.addr.eq(self.w_addr),
            wp.data.eq(self.w_data),
            rp.en.eq(1),
            rp.addr.eq(self.r_addr),
            self.r_data.eq(rp.data),
        ]


def increment_to_limit(value, limit):
    """Builds a statement that performs circular increments.

    Parameters
    ----------
    value: Signal(n)
        The value to be incremented
    limit: Signal(n)
        The maximum allowed value
    """
    return value.eq(Mux(value == limit - 1, 0, value + 1))


class SequentialMemoryReader(SimpleElaboratable):
    """A sequentially reading wrapper for a memory.
    Buffers inputs in such a way that the next input can be obtained next
    cycle, even though reads to the memory take a cycle.

    Parameters
    ----------
    max_depth:
        Maximum number of items stored in memory
    width:
        bits in each word of memory

    Public Interface
    ----------------
    limit: Signal(range(max_depth)) input
        The number of items to read
    mem_addr: Signal(range(max_depth)) output
        The address to send to the memory read port
    mem_data: Signal(32) input
        The data from memory
    data: Signal(32) output
        The current piece of data
    next: Signal() input
        Indicates the current piece of data has been read, and want
        the next word, please
    restart: Signal() input
        Indicates that reader should be reset to address zero. Data
        is ready at next cycle.
    """

    def __init__(self, *, width, max_depth):
        self.width = width
        self.max_depth = max_depth
        self.limit = Signal(range(max_depth))
        self.mem_addr = Signal(range(max_depth))
        self.mem_data = Signal(32)
        self.data = Signal(32)
        self.next = Signal()
        self.restart = Signal()

    def elab(self, m):
        # Track previous restart, next
        was_restart = Signal()
        m.d.sync += was_restart.eq(self.restart)
        was_next = Signal()
        m.d.sync += was_next.eq(self.next)

        # Decide address to be output (determines data available next cycle)
        last_mem_addr = Signal.like(self.limit)
        m.d.sync += last_mem_addr.eq(self.mem_addr)
        incremented_addr = Signal.like(self.limit)
        m.d.comb += incremented_addr.eq(Mux(last_mem_addr ==
                                            self.limit - 1, 0, last_mem_addr + 1))
        with m.If(self.restart):
            m.d.comb += self.mem_addr.eq(0)
        with m.Elif(was_next | was_restart):
            m.d.comb += self.mem_addr.eq(incremented_addr)
        with m.Else():
            m.d.comb += self.mem_addr.eq(last_mem_addr)

        # Decide data to be output
        last_data = Signal.like(self.data)
        m.d.sync += last_data.eq(self.data)
        with m.If(was_restart | was_next):
            m.d.comb += self.data.eq(self.mem_data)
        with m.Else():
            m.d.comb += self.data.eq(last_data)
