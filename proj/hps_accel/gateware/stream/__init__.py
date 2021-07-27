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

from .stream import BinaryCombinatorialActor, Sink, Source, flowcontrol_passthrough
