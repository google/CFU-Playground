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
from nmigen import signed, unsigned, Signal, Record, Memory

from .stream import BinaryPipelineActor
from .constants import Constants

OUTPUT_PARAMS = [
    ('bias', signed(16)),
    ('multiplier', signed(32)),
    ('shift', unsigned(4)),
]


class OutputParamsStorage(SimpleElaboratable):
    """Stores output parameters.

    Attributes:

    reset: Signal(), in
      resets the state of the store
    write_enable: Signal(), in
      Indicates write_data isto be written to the store.
    write_data: Record(OUTPUT_PARAMS), in
      The data to be written
    read_enable: Signal(), in
      Indicates data is to be read. It will be available on the next
      cycle. write_enable takes precedence over read_enable.
    read_data: Record(OUTPUT_PARAMS), out
      Data read from store.
    """

    def __init__(self):
        self.reset = Signal()
        self.write_enable = Signal()
        self.write_data = Record(OUTPUT_PARAMS)
        self.read_enable = Signal()
        self.read_data = Record(OUTPUT_PARAMS)

    def elab(self, m):
        memory = Memory(depth=Constants.MAX_CHANNELS, width=len(self.read_data))
        m.submodules.write_port = write_port = memory.write_port()
        m.submodules.read_port = read_port = memory.read_port(
            transparent=False)

        write_index = Signal(range(Constants.MAX_CHANNELS))
        read_index = Signal(range(Constants.MAX_CHANNELS))

        m.d.comb += write_port.en.eq(self.write_enable)
        m.d.comb += write_port.addr.eq(write_index)
        m.d.comb += write_port.data.eq(self.write_data.as_value())
        with m.If(self.write_enable):
            m.d.sync += write_index.eq(write_index +1)

        m.d.comb += read_port.en.eq(~self.write_enable)
        m.d.comb += read_port.addr.eq(read_index)
        m.d.comb += self.read_data.eq(read_port.data)

        with m.If(self.read_enable):
            with m.If(read_index == write_index - 1):
                m.d.sync += read_index.eq(0)
            with m.Else():
                m.d.sync += read_index.eq(read_index + 1)
            
        with m.If(self.reset):
            m.d.sync += write_index.eq(0)
            m.d.sync += read_index.eq(0)
        
class SaturateActivationPipeline(BinaryPipelineActor):
    """Fixes final result into signed(8) range.
    
    Attributes
    ----------

    input: Endpoint(signed(32)), in
      The input accumulator value.
    output: Endpoint(signed(8)), out
      The output 8 bit number.

    offset: signed(16), in
      The output_offset
    max: signed(8), in
      Maximum allowed value
    min: signed(8), in
      Minimum allowed input value
    """

    PIPELINE_CYCLES = 1

    def __init__(self):
        super().__init__(signed(16), signed(8), self.PIPELINE_CYCLES)
        self.offset = Signal(signed(16))
        self.max = Signal(signed(8))
        self.min = Signal(signed(8))

    def transform(self, m, in_value, out_value):
        # Cycle 0: add offset, saturate, register result into out_value
        with_offset = Signal(signed(32))
        m.d.comb += with_offset.eq(in_value + self.offset)
        with m.If(with_offset > self.max):
            m.d.sync += out_value.eq(self.max)
        with m.Elif(with_offset < self.min):
            m.d.sync += out_value.eq(self.min)
        with m.Else():
            m.d.sync += out_value.eq(with_offset)

        


