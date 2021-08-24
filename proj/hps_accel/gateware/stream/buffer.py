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

from nmigen_cfu.util import SimpleElaboratable
from nmigen import Value, Module, Signal, Mux

from .stream import Endpoint


class Buffer(SimpleElaboratable):
    """A single item buffer for streams.

    Passes a stream through from input to output. This occurs
    in this same cycle if the output stream is ready. If the output
    stream is not ready, then the input is stored in a register and
    output when the output is ready.

    Typically, such a buffer might be placed after a single cycle
    pipeline process.
    """

    def __init__(self, payload_type):
        self.input = Endpoint(payload_type)
        self.output = Endpoint(payload_type)

    def elab(self, m: Module):
        buffering = Signal()  # True if there is a value being buffered
        buffered_value = Signal.like(Value.cast(self.input.payload))

        # Pipe valid and ready back and forth
        m.d.comb += [
            self.input.ready.eq(~buffering | self.output.ready),
            self.output.valid.eq(buffering | self.input.valid),
            self.output.payload.eq(
                Mux(buffering, buffered_value, self.input.payload))
        ]

        # Buffer when have incoming value but cannot output just now
        with m.If(~buffering & ~self.output.ready & self.input.valid):
            m.d.sync += buffering.eq(True)
            m.d.sync += buffered_value.eq(self.input.payload)

        # Handle cases when transfering out from buffer
        with m.If(buffering & self.output.ready):
            with m.If(self.input.valid):
                m.d.sync += buffered_value.eq(self.input.payload)
            with m.Else():
                m.d.sync += buffering.eq(False)
