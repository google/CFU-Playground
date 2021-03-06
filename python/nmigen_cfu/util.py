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
from nmigen.sim import Simulator

import unittest


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
