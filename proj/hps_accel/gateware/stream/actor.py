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

from migen import Module
from util import SimpleElaboratable

from .stream import Sink, Source, flowcontrol_passthrough


class BinaryActor(SimpleElaboratable):
    """A binary actor is an object that transforms stream packets.

    It has one sink and one source. Each packet received at the sink
    has a corresponding packet sent from the source.

    Parameters
    ----------

    input_type: The Shape or Layout for the sink

    output_type: The Shape or Layout for the source.

    Attributes
    ----------

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
        self.control(m)
        self.transform(m, self.sink.payload, self.source.payload)

    def control(self, m):
        """Adds flow control to sink and source."""
        raise NotImplementedError(
            "BinaryActor subclass must implement control()")

    def transform(self, m, input, output):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplementedError(
            "BinaryActor subclass must implement transform()")


class BinaryCombinatorialActor(BinaryActor):
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
        super().__init__(input_type, output_type)

    def control(self, m: Module):
        m.d.comb += flowcontrol_passthrough(self.sink, self.source)

    def transform(self, m, input, output):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplemented()
