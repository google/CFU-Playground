#!/bin/env python
# Copyright 2020 Google LLC
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

from nmigen import *
from nmigen.sim import Simulator, Delay

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
    def elab(self, m):
        """Alternate elaborate interface"""
        return NotImplementedError()

    def elaborate(self, platform):
        self.m = Module()
        self.platform = platform
        self.elab(self.m)
        return self.m


class _TestBase(unittest.TestCase):
    def setUp(self):
        self.m = Module()
        self.dut = self.create_dut()
        self.m.submodules['dut'] = self.dut
        self.sim = Simulator(self.m)

    def create_dut(self):
        """Returns an instance of the device under test"""
        raise NotImplemented()

    def add_process(self, process):
        """Add main test process to the simulator"""
        pass

    def add_sim_clocks(self):
        """Add clocks as required by sim.
        """
        pass

    def run_sim(self, process, write_trace=False):
        self.add_process(process)
        self.add_sim_clocks()
        if write_trace:
            with self.sim.write_vcd("zz.vcd", "zz.gtkw"):
                self.sim.run()
        else:
            self.sim.run()


class CombTest(_TestBase):
    """Base class for unit testing of combinatorial components."""
    def add_process(self, process):
        """Add main test process to the simulator"""
        self.sim.add_process(process)


class SyncTest(_TestBase):
    """Base class for simple testing of clocked components."""
    def add_process(self, process):
        """Add main test process to the simulator"""
        self.sim.add_sync_process(process)

    def add_sim_clocks(self):
        """Adds a 1Hz clock for sync"""
        self.sim.add_clock(1, domain='sync')
