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


from amaranth import signed, unsigned, Cat, Signal, Module
from amaranth.hdl.dsl import FSM

from .stream import Endpoint
from ..util import SimpleElaboratable


class ByteToWord(SimpleElaboratable):
    """Converts a stream of bytes to a stream of words.

    Attributes:
    ----------

    input: Endpoint(signed(8)), in
      Incoming stream of bytes
    output: Endpoint(unsigned(32)), out
      Outgoing stream of words
    """

    def __init__(self):
        self.input = Endpoint(signed(8))
        self.output = Endpoint(unsigned(32))

    def elab(self, m: Module):

        # Registers accumulate incoming values
        registers = [Signal(8, name="register{i}") for i in range(3)]
        waiting_to_send = Signal()

        # Handle accumulating values
        with m.FSM(reset="BYTE_0"):
            with m.State("BYTE_0"):
                m.d.comb += self.input.ready.eq(1)
                m.d.sync += registers[0].eq(self.input.payload)
                with m.If(self.input.is_transferring()):
                    m.next = "BYTE_1"
            with m.State("BYTE_1"):
                m.d.comb += self.input.ready.eq(1)
                m.d.sync += registers[1].eq(self.input.payload)
                with m.If(self.input.is_transferring()):
                    m.next = "BYTE_2"
            with m.State("BYTE_2"):
                m.d.comb += self.input.ready.eq(1)
                m.d.sync += registers[2].eq(self.input.payload)
                with m.If(self.input.is_transferring()):
                    m.next = "BYTE_3"
            with m.State("BYTE_3"):
                m.d.comb += self.input.ready.eq(~waiting_to_send)
                with m.If(self.input.is_transferring()):
                    m.d.sync += waiting_to_send.eq(1)
                    m.d.sync += self.output.payload.eq(
                        Cat(registers[0], registers[1], registers[2], self.input.payload))
                    m.next = "BYTE_0"

        # Handle output whenever ready
        m.d.comb += self.output.valid.eq(waiting_to_send)
        with m.If(self.output.is_transferring()):
            m.d.sync += waiting_to_send.eq(0)
