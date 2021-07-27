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

from nmigen import Signal, Shape
from nmigen.hdl.dsl import Module
from nmigen.hdl.rec import Layout, DIR_FANOUT
from nmigen.sim.core import Delay

from .stream import Source, Sink

from nmigen_cfu.util import SimpleElaboratable, TestBase


TEST_PAYLOAD_LAYOUT = Layout([
    ("one", Shape(32), DIR_FANOUT),
    ("two", Shape(32), DIR_FANOUT),
])


class DataProducer(SimpleElaboratable):
    """Producer for test purposes."""

    def __init__(self):
        self.next = Signal()
        self.source = Source(TEST_PAYLOAD_LAYOUT)
        self.payload = self.source.payload

    def elab(self, m):
        # Assert valid if new value available
        # Deassert on transfer
        data_waiting_to_send = Signal()

        with m.If(self.next):
            m.d.sync += data_waiting_to_send.eq(1)

        with m.If(self.source.is_transferring()):
            m.d.sync += data_waiting_to_send.eq(0)

        m.d.comb += self.source.valid.eq(self.next | data_waiting_to_send)
        

class DataConsumer(SimpleElaboratable):
    """Consumer for test purposes."""

    def __init__(self):
        self.ready = Signal()
        self.transferred = Signal()
        self.sink = Sink(TEST_PAYLOAD_LAYOUT)
        self.payload = self.sink.payload
        self.one_out = Signal(32)
        self.two_out = Signal(32)

    def elab(self, m):
        m.d.comb += [
            self.sink.ready.eq(self.ready),
            self.transferred.eq(self.sink.is_transferring()),
        ]
        with m.If(self.transferred):
            m.d.sync += [
                self.one_out.eq(self.payload.one),
                self.two_out.eq(self.payload.two),
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
        m.d.comb += self.producer.source.connect(self.consumer.sink)
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
                yield self.producer.payload.one.eq(one_in)
                yield self.producer.payload.two.eq(two_in)
                yield self.consumer.ready.eq(ready)
                yield Delay(0.1)
                transferred, one_out, two_out = outputs
                self.assertEqual((yield self.consumer.transferred), transferred, f"cycle={n}")
                self.assertEqual((yield self.consumer.one_out), one_out, f"cycle={n}")
                self.assertEqual((yield self.consumer.two_out), two_out, f"cycle={n}")
                yield
        self.run_sim(process, False)
