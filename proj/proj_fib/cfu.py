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
from nmigen.sim import Simulator, Delay, Settle
from nmigen.build import Platform

import unittest

import util


class Cfu(Elaboratable):
    """Custom function unit interface.

    Parameters
    ----------
    -

    Attributes
    ----------
        input               io_bus_cmd_valid,
        output              io_bus_cmd_ready,
        input      [2:0]    io_bus_cmd_payload_function_id,
        input      [31:0]   io_bus_cmd_payload_inputs_0,
        input      [31:0]   io_bus_cmd_payload_inputs_1,
        output              io_bus_rsp_valid,
        input               io_bus_rsp_ready,
        output              io_bus_rsp_payload_response_ok,
        output     [31:0]   io_bus_rsp_payload_outputs_0,
        input clk
    """
    def __init__(self):
        self.cmd_valid = Signal(name='io_bus_cmd_valid')
        self.cmd_ready = Signal(name='io_bus_cmd_ready')
        self.cmd_payload_function_id = Signal(3,
                name='io_bus_cmd_payload_function_id')
        self.cmd_payload_inputs_0 = Signal(32,
                name='io_bus_cmd_payload_inputs_0')
        self.cmd_payload_inputs_1 = Signal(32,
                name='io_bus_cmd_payload_inputs_1' )
        self.rsp_valid = Signal(
                name='io_bus_rsp_valid')
        self.rsp_ready = Signal(
                name='io_bus_rsp_ready')
        self.rsp_payload_response_ok = Signal(
                name='io_bus_rsp_payload_response_ok')
        self.rsp_payload_outputs_0 = Signal(32,
                name = 'io_bus_rsp_payload_outputs_0')
        # how do I ensure that this is the clock used by the 'sync' domain?
        self.clock = Signal(name = 'clk')
        self.ports = [
            self.cmd_valid,
            self.cmd_ready,
            self.cmd_payload_function_id,
            self.cmd_payload_inputs_0,
            self.cmd_payload_inputs_1,
            self.rsp_valid,
            self.rsp_ready,
            self.rsp_payload_response_ok,
            self.rsp_payload_outputs_0,
            # self.clock,
        ]
        self.working = Signal(name = 'working', reset=False)
        self.start = Signal(name = 'start')
        self.valid = Signal(name = 'valid')
        self.count = Signal(unsigned(32), name = 'count', reset=0)
        self.s1 = Signal(unsigned(32), name = 's1', reset=0)
        self.s2 = Signal(unsigned(32), name = 's2', reset=0)

    def elaborate(self, platform : Platform):
        m = Module()
        m.d.sync.clk = self.clock

        m.d.comb += [
            self.start.eq(self.cmd_valid & self.cmd_ready),
            self.valid.eq( (self.count == 0) & self.working),
            self.rsp_valid.eq(self.valid),
            self.cmd_ready.eq(~self.working),
            self.rsp_payload_response_ok.eq(True),
            self.rsp_payload_outputs_0.eq(self.s2),
        ]

        with m.If(self.start):
            m.d.sync += [
                self.s1.eq(1),
                self.s2.eq(1),
                self.working.eq(True),
                self.count.eq(self.cmd_payload_inputs_0),
            ]
        with m.Elif(self.count > 0):
            m.d.sync += [
                self.s1.eq(self.s2),
                self.s2.eq(self.s1+self.s2),
                self.count.eq(self.count-1),
            ]
        with m.Elif(self.valid & self.rsp_ready):
            m.d.sync += [
                self.working.eq(False),
            ]

        return m


class Cfu_Test(util.SyncTest):
    def create_dut(self):
        return Cfu()

    def test_cfu(self):
        DATA = [
                ((0, 0, 0), (1,)),
                ((0, 0x4, 0x4), (8,)),
                ((0, 0x8, 0x4), (55,)),
                ((0, 0x14, 0x4), (17711,)),
        ]
        def process():
            yield self.dut.rsp_ready.eq(True)
            yield self.dut.cmd_valid.eq(False)
            for n, (inputs, outputs) in enumerate(DATA):
                # send new inputs
                func, i0, i1 = inputs
                yield self.dut.cmd_valid.eq(True)
                yield self.dut.cmd_payload_function_id.eq(func)
                yield self.dut.cmd_payload_inputs_0.eq(i0)
                yield self.dut.cmd_payload_inputs_1.eq(i1)
                yield
                yield self.dut.cmd_valid.eq(False)
                # loop until result is ready
                while (False == (yield self.dut.rsp_valid)):
                    yield
                o, = outputs
                got = (yield self.dut.rsp_payload_outputs_0)
                print("got ",got)
                self.assertEqual(o, got)
        self.run_sim(process, True)

if __name__ == '__main__':
    unittest.main()

