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

from nmigen import Cat, Signal, Module
from nmigen_cfu import SimpleElaboratable

from .stream import PayloadDefinition, Endpoint


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
        self.input_type = PayloadDefinition.cast(input_type)
        self.output_type = PayloadDefinition.cast(output_type)
        self.input = Endpoint(input_type)
        self.output = Endpoint(output_type)

    def elab(self, m: Module):
        self.control(m)
        self.transform(m, self.input.payload, self.output.payload)

    def control(self, m):
        """Adds flow control to sink and source."""
        raise NotImplementedError(
            "BinaryActor subclass must implement control()")

    def transform(self, m, in_value, out_value):
        """Transforms input to output.

        m: Module
          The module for this elaboratable
        in_value:
          The input payload to be transformed
        out_value:
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
        m.d.comb += self.input.ready.eq(self.output.ready)
        m.d.comb += self.output.valid.eq(self.input.valid)

    def transform(self, m, in_value, out_value):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplemented()


class BinaryPipelineActor(BinaryActor):
    """Base for a pipline actor.

    Performs a calcultion over a fixed number of cycles.

    Does not provide or respect backpressure over its streams.

    Parameters
    ----------

    input_type: The Shape or Layout for the sink

    output_type: The Shape or Layout for the source.

    pipeline_cycles: the number of cycles the pipline takes to calculate
    """

    def __init__(self, input_type, output_type, pipeline_cycles):
        super().__init__(input_type, output_type)
        self.pipeline_cycles = pipeline_cycles

    def delay(self, m, cycles, sig):
        """Delays the given signal by a number of cycles"""
        sr = Signal(cycles)
        m.d.sync += sr.eq(Cat(sig, sr[:-1]))
        return sr[-1]

    def control(self, m: Module):
        m.d.comb += self.input.ready.eq(self.output.ready)
        m.d.comb += self.output.valid.eq(self.delay(m,
                                         self.pipeline_cycles, self.input.valid))

    def transform(self, m, in_value, out_value):
        """Transforms input to output.

        input: self.input_type, in
        output: self.output_type, out
        """
        raise NotImplemented()
