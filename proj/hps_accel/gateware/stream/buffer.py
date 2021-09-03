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
from nmigen.hdl.ast import Cat
from nmigen.hdl.rec import Layout

from .stream import Endpoint


class Buffer(SimpleElaboratable):
    """A single item buffer for streams.

    Passes a stream through from input to output. This occurs
    in this same cycle if the output stream is ready. If the output
    stream is not ready, then the input is stored in a register and
    output when the output is ready.

    Typically, such a buffer might be placed after a single cycle
    pipeline process.

    Parameters
    ----------

    payload_type:
      Type of the payload. Typically a Shape or Layout.


    Attributes
    ----------

    input: Endpoint(payload_type), in
      Inbound stream.

    output: Endpoint(payload_type), out
      Outbound stream.

    reset: Signal()
      Set high to reset this buffer. Set low to enable buffer.
    """

    def __init__(self, payload_type):
        self.input = Endpoint(payload_type)
        self.output = Endpoint(payload_type)
        self.reset = Signal()

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

        # Reset all state
        with m.If(self.reset):
            m.d.sync += buffering.eq(False)
            m.d.sync += buffered_value.eq(0)


class ConcatenatingBuffer(SimpleElaboratable):
    """A buffer which concatenates multiple input streams.

    Passes multiple input streams through to a single output, with their
    payloads concatenated. Given two input streams, the first with payload
    A and the second with payload B, the output stream will have payload BA.

    The output stream only transfers when all inputs are valid. If input values
    arrive at different times, they are stored until a complete valid value
    can be presented at the output.

    Parameters
    ----------

    input_streams: list[(str, Shape)]
      Name and payload shape for each input stream.

    Attributes
    ----------

    inputs: {name: Endpoint}, in
      Inbound streams, keyed on name.

    output: Endpoint, out
      Outbound stream.

    reset: Signal
      Set high to reset this buffer. Set low to enable buffer.
    """

    def __init__(self, input_streams):
        self.field_names = list(name for name, shape in input_streams)
        self.field_shapes = {name: shape for name, shape in input_streams}
        self.inputs = {name: Endpoint(shape) for name, shape in input_streams}
        self.output = Endpoint(Layout(input_streams))
        self.reset = Signal()

    def elab(self, m: Module):
        # One signal for each input stream, indicating whether
        # there is a value being buffered:
        buffering = {name: Signal(name=f'buffering_{name}')
                     for name in self.field_names}
        # A buffer for each input stream:
        buffered_values = \
            {name: Signal(self.field_shapes[name], name=f'buffered_{name}')
             for name in self.field_names}

        # For each field of the concatenated output, present either the
        # buffered value if we have one, or else plumb through the input.
        for name in self.field_names:
            m.d.comb += self.output.payload[name].eq(
                    Mux(buffering[name],
                        buffered_values[name],
                        self.inputs[name].payload))

        # The output is valid if we have either a buffered value or a valid
        # input for every slice in the output.
        valid_or_buffering = (Cat(*[ep.valid for ep in self.inputs.values()]) |
                              Cat(*buffering.values()))
        m.d.comb += self.output.valid.eq(valid_or_buffering.all())

        for name, input in self.inputs.items():
            # We can accept an input if the buffer is not occupied,
            # or if we can output this cycle.
            m.d.comb += input.ready.eq(~buffering[name] |
                                       self.output.is_transferring())

            with m.If(input.valid):
                # Buffer it if the buffer is not occupied and we can't output.
                with m.If(~buffering[name] & ~self.output.is_transferring()):
                    m.d.sync += buffering[name].eq(True)
                    m.d.sync += buffered_values[name].eq(input.payload)
                # Buffer it if the buffer is occupied but we are outputting.
                with m.If(self.output.is_transferring()):
                    m.d.sync += buffered_values[name].eq(input.payload)
            with m.Else():
                with m.If(self.output.is_transferring()):
                    m.d.sync += buffering[name].eq(False)

        # Reset all state
        with m.If(self.reset):
            for b in buffering.values():
                m.d.sync += b.eq(False)
            for bv in buffered_values.values():
                m.d.sync += bv.eq(0)
