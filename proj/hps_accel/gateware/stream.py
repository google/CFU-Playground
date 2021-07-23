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

__doc__ = """A Stream abstraction
====================

Streams allows data to be transferred from one component to another.

A stream of data consists of a series of packets transferred from a Source
to a Sink. Each packet contains one Payload. A stream of packets may optionally
be organized into Frames.

Source and Sink operate in the same clock domain. They communicate with these
signals:

- payload: The data to be transferred. This may be a simple Signal or else a
           Record.
- valid: Set by source to indicate that a valid payload is being presented.
- ready: Set by sink to indicate that it is ready to accept a packet.
- last: Indicates the end of a frame.

A transfer takes place when both of the valid and ready signals are asserted on
the same clock cycle. This handshake allows for a simple flow control - Sources
are able to request that Sinks wait for data, and Sinks are able to request for
Sources to temporarily stop producing data.

There are cases where a Source or a Sink may not be able to wait for a
valid-ready handshake. For example, a video phy sink may require valid data be
presented at every clock cycle in order to generate a signal for a monitor. If
a Source or Sink cannot wait for a transfer, it should be make the behavior
clear in its interface documentation.

The use of frames - and hence the "last" signal, is optional and must be agreed
between Source and Sink.

This implementation was heavily influenced by the discussion at
https://github.com/nmigen/nmigen/issues/317, and especially the existing design
of LiteX streams.

Major differences from LiteX Streams:

-  "Parameters" are omitted. The value of parameters as a general mechanism is
   unclear.
-  "first" is omitted. A "first" signal can be derived from the "last" signal.
-  Source and Sink are distinct types. They share a common superclass for
   implementation purposes, but this is not exposed in the API.

"""


class _Endpoint:
    """Abstract base class for Sinks and Sources."""

    def __init__(self, payload_type):
        self.payload_type = payload_type
        self._record = Record([
            ("valid", Shape(), DIR_FANOUT),
            ("ready", Shape(), DIR_FANIN),
            ("last", Shape(), DIR_FANOUT),
            ("payload", payload_type, DIR_FANOUT),
        ])
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
