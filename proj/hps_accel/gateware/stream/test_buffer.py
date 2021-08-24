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
from nmigen.sim.core import Delay


from nmigen_cfu.util import TestBase

from .buffer import Buffer


class TestBuffer(TestBase):
    """Tests for basic Sink and Source functionality.

    There's really not much functionality to test so this test mostly functions
    as a proof of concept of the API.
    """

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
                print(f"{n} {inputs}, {outputs}")
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
