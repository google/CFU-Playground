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

from amaranth import unsigned
from amaranth.sim.core import Delay

from .gearbox import ByteToWord
from ..util import TestBase


class ByteToWordTest(TestBase):
    """Tests the Buffer class. """

    def create_dut(self):
        return ByteToWord()

    def test(self):
        DATA = [
            # Format is: input (valid, payload, ready),
            #            output (valid, payload, ready)
            ((0, 0, 1), (0, None, 1)),

            # Send 4 bytes, get 1 output
            ((1, 0x01, 1), (0, None, 1)),
            ((1, 0x02, 1), (0, None, 1)),
            ((1, 0x03, 1), (0, None, 1)),
            ((1, 0x04, 1), (0, None, 1)),
            ((0, 0, 1), (1, 0x04030201, 1)),
            ((0, 0, 1), (0, None, 1)),

            # Send 7 bytes, then input stalls
            ((1, 0x11, 1), (0, None, 0)),
            ((1, 0x12, 1), (0, None, 0)),
            ((1, 0x13, 1), (0, None, 0)),
            ((1, 0x14, 1), (0, None, 0)),
            ((1, 0x15, 1), (1, 0x14131211, 0)),
            ((1, 0x16, 1), (1, 0x14131211, 0)),
            ((1, 0x17, 1), (1, 0x14131211, 0)),
            ((1, 0x18, 0), (1, 0x14131211, 0)),
            ((1, 0x18, 0), (1, 0x14131211, 0)),
            ((1, 0x18, 0), (1, 0x14131211, 1)), 
            ((1, 0x18, 1), (0, None, 1)),       
            ((0, 0, 1), (1, 0x18171615, 1)), 

            # Stream through 12 bytes
            ((1, 0x21, 1), (0, None, 1)),
            ((1, 0x22, 1), (0, None, 1)),
            ((1, 0x23, 1), (0, None, 1)),
            ((1, 0x24, 1), (0, None, 1)),
            ((1, 0x25, 1), (1, 0x24232221, 1)),
            ((1, 0x26, 1), (0, None, 1)),
            ((1, 0x27, 1), (0, None, 1)),
            ((1, 0x28, 1), (0, None, 1)),
            ((1, 0x2a, 1), (1, 0x28272625, 1)),
            ((1, 0x2b, 1), (0, None, 1)),
            ((1, 0x2c, 1), (0, None, 1)),
            ((1, 0x2d, 1), (0, None, 1)),
            ((0, 0, 1), (1, 0x2d2c2b2a, 1)),
        ]

        def process():
            dut = self.dut
            for n, (inputs, outputs) in enumerate(DATA):
                in_valid, in_payload, expected_in_ready = inputs
                expected_out_valid, expected_out_payload, out_ready = outputs
                yield dut.input.valid.eq(in_valid)
                yield dut.input.payload.eq(in_payload)
                yield dut.output.ready.eq(out_ready)
                yield Delay(0.5)
                self.assertEqual((yield dut.input.ready), expected_in_ready)
                self.assertEqual((yield dut.output.valid), expected_out_valid)
                if expected_out_payload is not None:
                    self.assertEqual((yield dut.output.payload),
                                     expected_out_payload)
                yield
        self.run_sim(process, False)
