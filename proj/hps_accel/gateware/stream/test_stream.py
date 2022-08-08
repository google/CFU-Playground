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

from amaranth import Signal, Shape
from amaranth.hdl.dsl import Module
from amaranth.hdl.rec import Layout, Record
from amaranth.sim.core import Delay

from .stream import Endpoint, connect
from ..util import SimpleElaboratable, TestBase


TEST_PAYLOAD_LAYOUT = Layout([
    ("one", Shape(32)),
    ("two", Shape(32)),
])


class DataProducer(SimpleElaboratable):
    """Producer for test purposes."""

    def __init__(self):
        self.next = Signal()
        self.test_data = Record(TEST_PAYLOAD_LAYOUT)
        self.output = Endpoint(TEST_PAYLOAD_LAYOUT)

    def elab(self, m):
        # Assert valid if new test_data available
        # Deassert on transfer
        data_waiting_to_send = Signal()
        m.d.comb += self.output.payload.eq(self.test_data)

        with m.If(self.next):
            m.d.sync += data_waiting_to_send.eq(1)

        with m.If(self.output.is_transferring()):
            m.d.sync += data_waiting_to_send.eq(0)

        m.d.comb += self.output.valid.eq(self.next | data_waiting_to_send)
        

class DataConsumer(SimpleElaboratable):
    """Consumer for test purposes."""

    def __init__(self):
        self.ready = Signal()
        self.transferred = Signal()
        self.input = Endpoint(TEST_PAYLOAD_LAYOUT)
        self.one_out = Signal(32)
        self.two_out = Signal(32)

    def elab(self, m):
        m.d.comb += [
            self.input.ready.eq(self.ready),
            self.transferred.eq(self.input.is_transferring()),
        ]
        with m.If(self.transferred):
            m.d.sync += [
                self.one_out.eq(self.input.payload.one),
                self.two_out.eq(self.input.payload.two),
            ]


class TestSinkSource(TestBase):
    """Tests for basic Sink and Source functionality.

    There's really not much functionality to test so this test mostly functions
    as a proof of concept of the API.
    """

    def create_dut(self):
        m = Module()
        m.submodules["producer"] = self.producer = DataProducer()
        m.submodules["consumer"] = self.consumer = DataConsumer()
        m.d.comb += connect(self.producer.output, self.consumer.input)
        return m

    def test(self):
        DATA = [
            # Format is: (next, one_in, two_in, ready) (transfered, one_out, two_out)
            ((0, 0, 0, 0), (0, 0, 0)),
            ((1, 10, 20, 0), (0, 0, 0)),
            ((0, 10, 20, 1), (1, 0, 0)),
            ((0, 0, 0, 0), (0, 10, 20)),
            ((1, 30, 40, 0), (0, 10, 20)),
            ((1, 40, 50, 1), (1, 10, 20)),
            ((0, 0, 0, 0), (0, 40, 50)),
        ]

        def process():
            for n, (inputs, outputs) in enumerate(DATA):
                next, one_in, two_in, ready = inputs
                yield self.producer.next.eq(next)
                yield self.producer.test_data.one.eq(one_in)
                yield self.producer.test_data.two.eq(two_in)
                yield self.consumer.ready.eq(ready)
                yield Delay(0.1)
                transferred, one_out, two_out = outputs
                self.assertEqual((yield self.consumer.transferred), transferred, f"cycle={n}")
                self.assertEqual((yield self.consumer.one_out), one_out, f"cycle={n}")
                self.assertEqual((yield self.consumer.two_out), two_out, f"cycle={n}")
                yield
        self.run_sim(process, False)
