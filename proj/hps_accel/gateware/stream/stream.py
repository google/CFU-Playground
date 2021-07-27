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

from migen.fhdl.module import Module
from nmigen import Signal, Shape
from nmigen.hdl.rec import Record, DIR_FANIN, DIR_FANOUT
from util import SimpleElaboratable


class _Endpoint:
    """Abstract base class for Sinks and Sources."""

    def __init__(self, payload_type):
        self.payload_type = payload_type
        self._record = Record([
            ("valid", Shape(), DIR_FANOUT),
            ("ready", Shape(), DIR_FANIN),
            ("last", Shape(), DIR_FANOUT),
            ("payload", payload_type, DIR_FANOUT),
        ], src_loc_at=3)
        self.valid = self._record.valid
        self.ready = self._record.ready
        self.last = self._record.last
        self.payload = self._record.payload

    def is_transferring(self):
        """Returns an expression that is true when a transfer takes place."""
        return (self.valid & self.ready)


class Source(_Endpoint):
    """A stream source.

    Parameters
    ----------

    payload_type: Shape(N) or Layout
      The payload transferred from this Source.

    Attributes:
    -----------

    payload_type: Shape(N) or Layout
    valid: Signal(1), out
    ready: Signal(1), in
    last: Signal(1), out
    payload: Signal(N) or Record, out
    """

    def __init__(self, payload_type):
        super().__init__(payload_type)

    def connect(self, sink):
        """Returns a list of statements that connects this source to a sink.

        Parameters:
          sink: This Sink to which to connect.
        """
        assert isinstance(sink, Sink)
        return self._record.connect(sink._record)


class Sink(_Endpoint):
    """A stream sink

    Parameters
    ----------

    payload: Signal(N) or Record
      The payload transferred to this Sink.

    Attributes:
    -----------

    payload_type: Shape(N) or Layout
    valid: Signal(1), in
    ready: Signal(1), out
    last: Signal(1), in
    payload: Signal(N) or Record, in
    """

    def __init__(self, payload_type):
        super().__init__(payload_type)


def flowcontrol_passthrough(sink, source):
    """Returns statments to pass flow control from a sink to source.

    Useful in cases where a component acts on a stream completely
    combinatorially.
    """
    return [
        sink.ready.eq(source.ready),
        source.valid.eq(sink.valid),
        source.last.eq(sink.last),
    ]


class BinaryCombinatorialActor(SimpleElaboratable):
    """Base for a combinatorial binary actor.

    Performs a combinatorial operation on a sink payload and routes it to a
    source.

    Parameters
    ----------

    input_type: The Shape or Layout for the sink

    output_type: The Shape or Layout for the source.

    Attributes:

    sink: Sink(input_type), in
      Sink for incoming data

    source: Source(source_type), out
      Source for outgoing data
    """

    def __init__(self, input_type, output_type):
        self.input_type = input_type
        self.output_type = output_type
        self.sink = Sink(input_type)
        self.source = Source(output_type)

    def elab(self, m: Module):
        m.d.comb += flowcontrol_passthrough(self.sink, self.source)
        self.transform(m, self.sink.payload, self.source.payload)

    def transform(self, m, input, output):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplemented()
