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

from .stream import StreamDefinition, Stream


class BinaryActor(SimpleElaboratable):
    """A binary actor is an object that transforms stream packets.

    It has one input stream and one output stream. Each packet received
    at the input has a corresponding packet sent from the output.

    Parameters
    ----------

    input_type: Defines input stream

    output_type: Defines output stream

    Attributes
    ----------

    sink: Sink(input_type), in
      Sink for incoming data

    source: Source(source_type), out
      Source for outgoing data
    """

    def __init__(self, input_type, output_type):
        self.input_type = StreamDefinition.cast(input_type, ignores_valid=True)
        self.output_type = StreamDefinition.cast(
            output_type, ignores_ready=True)
        self.input = Stream(input_type)
        self.output = Stream(output_type)

    def elab(self, m: Module):
        self.control(m)
        self.transform(m, self.input.payload, self.output.payload)

    def control(self, m):
        """Adds flow control to sink and source."""
        raise NotImplementedError(
            "BinaryActor subclass must implement control()")

    def transform(self, m, input, output):
        """Transforms input to output.

        m: Module
          The module for this elaboratable
        input:
          The input payload to be transformed
        output:
          The transformed value
        """
        raise NotImplementedError(
            "BinaryActor subclass must implement transform()")


class BinaryCombinatorialActor(BinaryActor):
    """Base for a combinatorial binary actor.

    Performs a combinatorial operation on a input payload to transform
    it to an output.

    Parameters
    ----------

    input_type: The Shape or Layout for the sink

    output_type: The Shape or Layout for the source.
    """

    def __init__(self, input_type, output_type):
        super().__init__(input_type, output_type)

    def control(self, m: Module):
        m.d.comb += [
            self.sink.ready.eq(self.source.ready),
            self.source.valid.eq(self.sink.valid),
            self.source.last.eq(self.sink.last),
        ]

    def transform(self, m, input, output):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplemented()
