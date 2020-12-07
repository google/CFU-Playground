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

import unittest

import util


class Cfu(util.SimpleElaboratable):
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
            self.clock,
        ]

    def elab(self, m):
        # All instructions complete in single cycle, so we can respond immediately
        m.d.comb += [
            self.rsp_valid.eq(self.cmd_valid),
            self.cmd_ready.eq(self.rsp_ready),
            self.rsp_payload_response_ok.eq(1),
        ]

        with m.Switch(self.cmd_payload_function_id):
            with m.Case(0):
                # pass inputs_0
                m.d.comb += self.rsp_payload_outputs_0.eq(self.cmd_payload_inputs_0)

            with m.Case(1):
                # pass inputs_1
                m.d.comb += self.rsp_payload_outputs_0.eq(self.cmd_payload_inputs_1)

            with m.Case(2):
                # pass inputs_0
                m.d.comb += self.rsp_payload_outputs_0.eq(self.cmd_payload_inputs_0)


class Cfu_Test(util.CombTest):
    def create_dut(self):
        return Cfu()

    def test_cfu(self):
        DATA = [
                # pass inputs_0
                ((0, 0, 0), (0,)),
                ((0, 0x01020304, 0x01020304), (0x01020304,)),
                ((0, 0x01010101, 0xffffffff), (0x01010101,)),
                # pass inputs_1
                ((1, 0x01020304, 0xffffffff), (0xffffffff,)),
                ((1, 0x0102ff00, 0xf0ffff5f), (0xf0ffff5f,)),
                # pass inputs_0
                ((2, 0x01020304, 0xffffffff), (0x01020304,)),
                ((2, 0xffffffff, 0xffffffff), (0xffffffff,)),
                ((2, 0x10203040, 0xffffffff), (0x10203040,)),
        ]
        def process():
            for n, (inputs, outputs) in enumerate(DATA):
                func, i0, i1 = inputs
                yield self.dut.cmd_payload_function_id.eq(func)
                yield self.dut.cmd_payload_inputs_0.eq(i0)
                yield self.dut.cmd_payload_inputs_1.eq(i1)
                yield Delay(1)
                o, = outputs
                self.assertEqual(o, (yield self.dut.rsp_payload_outputs_0))
        self.run_sim(process, True)

if __name__ == '__main__':
    unittest.main()

