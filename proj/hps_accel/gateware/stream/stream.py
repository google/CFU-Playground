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

from nmigen import Shape
from nmigen.hdl.rec import Record, DIR_FANIN, DIR_FANOUT


class _Endpoint:
    """Abstract base class for Sinks and Sources."""

    def __init__(self, payload_type, name, src_loc_at):
        self.payload_type = payload_type
        self._record = Record([
            ("valid", Shape(), DIR_FANOUT),
            ("ready", Shape(), DIR_FANIN),
            ("last", Shape(), DIR_FANOUT),
            ("payload", payload_type, DIR_FANOUT),
        ], src_loc_at=2+src_loc_at, name=name)
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
    name: str
      Base for signal names.

    Attributes:
    -----------

    payload_type: Shape(N) or Layout
    valid: Signal(1), out
    ready: Signal(1), in
    last: Signal(1), out
    payload: Signal(N) or Record, out
    """

    def __init__(self, payload_type, name=None, src_loc_at=0):
        super().__init__(payload_type, name, src_loc_at)

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
    name: str
      Base for signal names.

    Attributes:
    -----------

    payload_type: Shape(N) or Layout
    valid: Signal(1), in
    ready: Signal(1), out
    last: Signal(1), in
    payload: Signal(N) or Record, in
    """

    def __init__(self, payload_type, name=None, src_loc_at=0):
        super().__init__(payload_type, name, src_loc_at)


def glue_sources(source_in: Source, source_out: Source):
    """Combinatorially glues two sources together.

    source_in is combinatorially glued to source_out. This is useful when
    exposing a submodule's Source as part of the interface of the current
    module.

    The two sources must have identical payload types.

    Parameters:
      source_in:
        The source that forms part of the submodule's interface.
      source_out:
        The source that forms part of the current module's interface.

    Result:
      A sequence of statements that connects the two sources.
    """
    # Checking to catch simple mistakes
    assert isinstance(source_in, Source)
    assert isinstance(source_out, Source)
    assert source_in.payload_type == source_out.payload_type

    return [
        source_in.ready.eq(source_out.ready),
        source_out.valid.eq(source_in.valid),
        source_out.last.eq(source_in.last),
        source_out.payload.eq(source_in.payload),
    ]


def glue_sinks(sink_in: Sink, sink_out: Sink):
    """Combinatorially glues two sinks together.

    sink_in is combinatorially glued to sink_out. This is useful when
    exposing a submodule's Sink as part of the interface of the current
    module.

    The two sinks must have identical payload types.

    Parameters:
      sink_in:
        The sink that forms part of the current module's interface.
      sink_out:
        The sink that forms part of the submodule's interface.

    Result:
      A sequence of statements that connects the two sinks.
    """
    # Checking to catch simple mistakes
    assert isinstance(sink_in, Sink)
    assert isinstance(sink_out, Sink)
    assert sink_in.payload_type == sink_out.payload_type

    return [
        sink_in.ready.eq(sink_out.ready),
        sink_out.valid.eq(sink_in.valid),
        sink_out.last.eq(sink_in.last),
        sink_out.payload.eq(sink_in.payload),
    ]
