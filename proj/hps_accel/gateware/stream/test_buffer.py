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

from nmigen import unsigned
from nmigen.hdl.rec import Layout
from nmigen.sim.core import Delay, Settle


from nmigen_cfu.util import TestBase

from .buffer import Buffer, ConcatenatingBuffer


class TestBuffer(TestBase):
    """Tests the Buffer class. """

    def create_dut(self):
        return Buffer(unsigned(32))

    def test(self):
        DATA = [
            # Format is: input (valid, payload, ready),
            #            output (valid, payload, ready)
            # Single value, passthrough, output constant ready
            ((0, 0, 1), (0, None, 1)),
            ((1, 22, 1), (1, 22, 1)),
            ((0, 0, 1), (0, None, 1)),
            # Single value, passthrough, output instantaneosly ready
            ((0, 0, 1), (0, None, 0)),
            ((1, 22, 1), (1, 22, 1)),
            ((0, 0, 1), (0, None, 0)),
            # Single value, delay ready one cycle
            ((0, 0, 1), (0, None, 0)),
            ((1, 22, 1), (1, 22, 0)),
            ((0, 0, 1), (1, 22, 1)),
            ((0, 0, 1), (0, None, 1)),
            # Single value, delay ready two cycle
            ((0, 0, 1), (0, None, 0)),
            ((1, 22, 1), (1, 22, 0)),
            ((0, 0, 0), (1, 22, 0)),
            ((0, 0, 1), (1, 22, 1)),
            ((0, 0, 1), (0, None, 1)),
            # Buffer a stream of values
            ((0, 0, 1), (0, None, 0)),
            ((1, 22, 1), (1, 22, 0)),
            ((1, 23, 0), (1, 22, 0)),
            ((1, 23, 0), (1, 22, 0)),
            ((1, 23, 1), (1, 22, 1)),
            ((1, 24, 1), (1, 23, 1)),
            ((1, 25, 1), (1, 24, 1)),
            ((0, 0, 0), (1, 25, 0)),
            ((0, 0, 1), (1, 25, 1)),
            ((0, 0, 1), (0, None, 0)),
        ]

        def process():
            dut = self.dut
            for n, (inputs, outputs) in enumerate(DATA):
                in_valid, in_payload, expected_in_ready = inputs
                expected_out_valid, expected_out_payload, out_ready = outputs
                yield dut.input.valid.eq(in_valid)
                yield dut.input.payload.eq(in_payload)
                yield dut.output.ready.eq(out_ready)
                yield Delay(0.1)
                self.assertEqual((yield dut.input.ready), expected_in_ready)
                self.assertEqual((yield dut.output.valid), expected_out_valid)
                if expected_out_payload is not None:
                    self.assertEqual((yield dut.output.payload),
                                     expected_out_payload)
                yield
        self.run_sim(process, False)


class TestConcatenatingBuffer(TestBase):

    def create_dut(self):
        return ConcatenatingBuffer([('x', unsigned(8)), ('y', unsigned(8))])

    def test(self):
        DATA = [
            # Format is: input x (valid, payload, ready),
            #            input y (valid, payload, ready),
            #            output (valid, payload, ready)
            # Simultaneous inputs, passthrough, output constant ready
            ((0, 0, 1), (0, 0, 1), (0, None, 1)),
            ((1, 0xaa, 1), (1, 0xbb, 1), (1, 0xbbaa, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 1)),
            # Simultaneous inputs, passthrough, output instantaneosly ready
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            ((1, 0xcc, 1), (1, 0xdd, 1), (1, 0xddcc, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # Simultaneous inputs, delay ready one cycle
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            ((1, 0xee, 1), (1, 0xff, 1), (1, 0xffee, 0)),
            ((0, 0, 1), (0, 0, 1), (1, 0xffee, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # Simultaneous inputs, delay ready two cycle
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            ((1, 0x77, 1), (1, 0x88, 1), (1, 0x8877, 0)),
            ((0, 0, 0), (0, 0, 0), (1, 0x8877, 0)),
            ((0, 0, 1), (0, 0, 1), (1, 0x8877, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # Buffer a stream of simultaneous inputs
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            ((1, 0x11, 1), (1, 0x22, 1), (1, 0x2211, 0)),
            ((1, 0x33, 0), (1, 0x44, 0), (1, 0x2211, 0)),
            ((1, 0x33, 0), (1, 0x44, 0), (1, 0x2211, 0)),
            ((1, 0x33, 1), (1, 0x44, 1), (1, 0x2211, 1)),
            ((1, 0x55, 1), (1, 0x66, 1), (1, 0x4433, 1)),
            ((1, 0x77, 1), (1, 0x88, 1), (1, 0x6655, 1)),
            ((0, 0, 0), (0, 0, 0), (1, 0x8877, 0)),
            ((0, 0, 1), (0, 0, 1), (1, 0x8877, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # One input arrives before the other, passthrough same cycle
            ((1, 0xaa, 1), (0, 0, 1), (0, None, 0)),
            ((0, 0, 1), (1, 0xbb, 1), (1, 0xbbaa, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # One input arrives before the other, both buffered
            ((1, 0xaa, 1), (0, 0, 1), (0, None, 0)),
            ((0, 0, 0), (1, 0xbb, 1), (1, 0xbbaa, 0)),
            ((0, 0, 1), (0, 0, 1), (1, 0xbbaa, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
            # One input stream starts before the other
            ((1, 0x11, 1), (0, 0, 1), (0, None, 0)),
            ((1, 0x33, 0), (1, 0x22, 1), (1, 0x2211, 0)),
            ((1, 0x33, 0), (1, 0x44, 0), (1, 0x2211, 0)),
            ((1, 0x33, 1), (1, 0x44, 1), (1, 0x2211, 1)),
            ((1, 0x55, 1), (1, 0x66, 1), (1, 0x4433, 1)),
            ((1, 0x77, 1), (1, 0x88, 1), (1, 0x6655, 1)),
            ((0, 0, 0), (0, 0, 0), (1, 0x8877, 0)),
            ((0, 0, 1), (0, 0, 1), (1, 0x8877, 1)),
            ((0, 0, 1), (0, 0, 1), (0, None, 0)),
        ]

        def process():
            dut = self.dut
            for n, (input_x, input_y, outputs) in enumerate(DATA):
                in_x_valid, in_x_payload, expected_in_x_ready = input_x
                in_y_valid, in_y_payload, expected_in_y_ready = input_y
                expected_out_valid, expected_out_payload, out_ready = outputs
                yield dut.inputs['x'].valid.eq(in_x_valid)
                yield dut.inputs['x'].payload.eq(in_x_payload)
                yield dut.inputs['y'].valid.eq(in_y_valid)
                yield dut.inputs['y'].payload.eq(in_y_payload)
                yield dut.output.ready.eq(out_ready)
                yield Settle()
                self.assertEqual((yield dut.inputs['x'].ready),
                                 expected_in_x_ready)
                self.assertEqual((yield dut.inputs['y'].ready),
                                 expected_in_y_ready)
                self.assertEqual((yield dut.output.valid), expected_out_valid)
                if expected_out_payload is not None:
                    self.assertEqual(
                            hex((yield dut.output.payload.as_value())),
                            hex(expected_out_payload))
                yield
        self.run_sim(process)
