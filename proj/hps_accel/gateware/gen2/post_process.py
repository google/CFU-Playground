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

"""Post processing of accumulated values into 8 bit outputs."""

from amaranth import (
    signed, unsigned, Array, Cat, Module, Mux, Record, Signal, ResetInserter
)

from .constants import Constants
from .mem import LoopingAddressGenerator
from .utils import unsigned_upto
from ..stream import connect, Endpoint, BinaryPipelineActor
from ..stream.fifo import StreamFifo
from ..util import SimpleElaboratable

SRDHM_INPUT_LAYOUT = [
    ('a', signed(32)),
    ('b', signed(32)),
]


class SaturatingRoundingDoubleHighMul(BinaryPipelineActor):
    """Performs an SRDHM operation.

    This is approximately a 32x32 mulitiplication where only the high 32
    bits are returned. It actually returns double the value, which is
    possible because both inputs are signed and so the raw result of the
    multiplication is only a 63 bit number.

    Only tested for

    * 'a' in the range +/- (64 * 16 * 128) (i.e 18bits including sign).
      This is the range required for processing 4x4 convs with depths
      up to 64.
    * 'b' in the range 0x4000_0000 to 0x7000_0000 as this appears to be
      the range used the hps model.

    Attributes
    ----------

    input: Endpoint(SRDHM_INPUT_LAYOUT), in
      The calculation to perform.

    output: Endpoint(signed(32)), out
      The result.

    This pipeline neither provides nor respects back pressure.
    """
    PIPELINE_CYCLES = 3

    def __init__(self):
        super().__init__(SRDHM_INPUT_LAYOUT, signed(32), self.PIPELINE_CYCLES)

    def transform(self, m, in_value, out_value):
        # Cycle 0: register inputs
        a = in_value.a
        reg_a = Signal(signed(32))
        reg_b = Signal(signed(32))
        m.d.sync += reg_a.eq(Mux(a >= 0, a, -a))
        m.d.sync += reg_b.eq(in_value.b)

        # Cycle 1: multiply to register
        # both operands are positive, so result always positive
        reg_ab = Signal(signed(63))
        m.d.sync += reg_ab.eq(reg_a * reg_b)

        # Cycle 2: nudge, take high bits and sign
        positive_2 = self.delay(m, 2, a >= 0)  # Whether input positive
        nudged = reg_ab + Mux(positive_2, (1 << 30), (1 << 30) - 1)
        high_bits = Signal(signed(32))
        m.d.comb += high_bits.eq(nudged[31:])
        with_sign = Mux(positive_2, high_bits, -high_bits)
        m.d.sync += out_value.eq(with_sign)


RDBPOT_INPUT_LAYOUT = [
    ('dividend', signed(32)),  # The value to be divided
    ('shift', unsigned(4)),    # The power of two by which to divide by
]


class RoundingDivideByPowerOfTwo(BinaryPipelineActor):
    """Divides its input by a power of two, rounding appropriately.

    Attributes
    ----------

    input: Endpoint(RDBPOT_INPUT_LAYOUT), in
      The calculation to perform.

    output: Endpoint(signed(32)), out
      The result.

    This pipeline neither provides nor respects back pressure.
    """
    PIPELINE_CYCLES = 3

    def __init__(self):
        super().__init__(RDBPOT_INPUT_LAYOUT, signed(32), self.PIPELINE_CYCLES)

    def transform(self, m, in_value, out_value):
        # Cycle 0: register inputs
        dividend = Signal(signed(32))
        shift = Signal(4)
        m.d.sync += dividend.eq(in_value.dividend)
        m.d.sync += shift.eq(in_value.shift)

        # Cycle 1: calculate
        result = Signal(signed(32))
        remainder = Signal(signed(32))
        # Our threshold looks like 010, 0100, 01000 etc for positive values and
        # 011, 0101, 01001 etc for negative values.
        threshold = Signal(signed(32))
        quotient = Signal(signed(32))
        negative = Signal()
        m.d.comb += negative.eq(dividend < 0)
        with m.Switch(shift):
            for n in range(2, 13):
                with m.Case(n):
                    mask = (1 << n) - 1
                    m.d.comb += remainder.eq(dividend & mask)
                    m.d.comb += threshold[1:].eq(1 << (n - 2))
                    m.d.comb += quotient.eq(dividend >> n)
        m.d.comb += threshold[0].eq(negative)
        m.d.sync += result.eq(quotient + Mux(remainder >= threshold, 1, 0))

        # Cycle 2: send output
        m.d.sync += out_value.eq(result)


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


def delay(m, signal, cycles):
    """Delays a signal by a number cycles.

    Parameters:
      m: Module
        The module to work in.
      signal: Signal(?)
        The signal to delay
      cycles: int
        The number of cycles to delay
    """
    name = signal.name
    for i in range(cycles):
        delayed = Signal.like(signal, name=f"{name}_delay_{i}")
        m.d.sync += delayed.eq(signal)
        signal = delayed
    return signal


POST_PROCESS_PARAMS = [
    ('bias', signed(18)),
    ('multiplier', signed(32)),
    ('shift', unsigned(4)),
]

POST_PROCESS_PARAMS_WIDTH = len(Record(POST_PROCESS_PARAMS))


class PostProcessPipeline(SimpleElaboratable):
    """Converts an accumulator into an 8-bit value

    Attributes
    ----------

    input: Endpoint(signed(32)), in
      The accumulated value to convert

    params: Endpoint(POST_PROCESS_PARAMS), in
      Parameters assumed always ready and then read on input

    output: Endpoint(signed(8)), out
      The 8-bit quantized version of the accumulator

    offset: signed(9), in
       The output offset

    activation_min: signed(8), out
        The minimum output value

    activation_max: signed(8), out
        The maximum output value
    """

    PIPELINE_CYCLES = (
        SaturatingRoundingDoubleHighMul.PIPELINE_CYCLES +
        RoundingDivideByPowerOfTwo.PIPELINE_CYCLES +
        SaturateActivationPipeline.PIPELINE_CYCLES
    )

    def __init__(self):
        self.input = Endpoint(signed(32))
        self.params = Endpoint(POST_PROCESS_PARAMS)
        self.output = Endpoint(signed(8))
        self.offset = Signal(signed(9))
        self.activation_min = Signal(signed(8))
        self.activation_max = Signal(signed(8))

    def elab(self, m: Module):
        # Input always ready
        m.d.comb += self.input.ready.eq(1)

        # Pipelines
        m.submodules.srdhm = srdhm = SaturatingRoundingDoubleHighMul()
        m.submodules.rdbpot = rdbpot = RoundingDivideByPowerOfTwo()
        m.submodules.sap = sap = SaturateActivationPipeline()

        # On incoming valid, put data into pipeline and get next set of
        # POST_PROCESS_PARAMS
        m.d.comb += [
            srdhm.input.valid.eq(self.input.valid),
            self.params.ready.eq(self.input.valid),
            srdhm.input.payload.a.eq(
                self.input.payload +
                self.params.payload.bias),
            srdhm.input.payload.b.eq(self.params.payload.multiplier),
        ]

        # Connect the output of srdhm to rdbpot, along with the shift parameter
        delayed_shift = delay(m, self.params.payload.shift,
                              SaturatingRoundingDoubleHighMul.PIPELINE_CYCLES)
        m.d.comb += [
            srdhm.output.ready.eq(rdbpot.input.ready),
            rdbpot.input.valid.eq(srdhm.output.valid),
            rdbpot.input.payload.dividend.eq(srdhm.output.payload),
            rdbpot.input.payload.shift.eq(delayed_shift),
        ]

        # Connect final stage - the saturate activation pipeline
        m.d.comb += connect(rdbpot.output, sap.input)
        m.d.comb += [
            sap.offset.eq(self.offset),
            sap.min.eq(self.activation_min),
            sap.max.eq(self.activation_max),
        ]
        # Connect final state to output
        m.d.comb += connect(sap.output, self.output)


# Post Process size parameters
POST_PROCESS_SIZES = [
    ('depth', unsigned_upto(Constants.MAX_CHANNEL_DEPTH)),
    ('repeats', unsigned_upto(Constants.SYS_ARRAY_HEIGHT)),
]


class ParamWriter(SimpleElaboratable):
    """Writes post processing parameters to a memory.

    To write a new set of parameters, first reset the writer.

    Parameters
    ----------

    max_depth: int
        The maximum depth required for writes. Determines addr_width.

    Attributes
    ----------

    reset: Signal(), in
        Initiates a reset, resets write position to start of memory

    input_data: Endpoint(POST_PROCESS_PARAMS), out
        Stream of data to write to memory.

    mem_we: Signal(), out
        Memory write enable

    mem_addr: Signal(addr_width), out
        Address sent to memory.

    mem_data: Signal(POST_PROCESS_PARAMS_WIDTH)), out
        Data sent to memory
    """

    def __init__(self, max_depth=Constants.MAX_CHANNEL_DEPTH):
        self.reset = Signal()
        self.input_data = Endpoint(POST_PROCESS_PARAMS)
        self.mem_we = Signal()
        self.mem_addr = Signal(range(max_depth))
        self.mem_data = Signal(POST_PROCESS_PARAMS_WIDTH)

    def elab(self, m):
        with m.If(self.reset):
            m.d.sync += self.mem_addr.eq(0)

        m.d.comb += self.input_data.ready.eq(~self.reset)
        m.d.comb += self.mem_data.eq(self.input_data.payload)
        m.d.comb += self.mem_we.eq(self.input_data.is_transferring())

        # Increment memory address on incoming data
        with m.If(self.input_data.is_transferring()):
            m.d.sync += self.mem_addr.eq(self.mem_addr + 1)


class ReadingProducer(SimpleElaboratable):
    """Reads post-process parameters from memory to a stream.

    Each value read is repeated a given number of times.

    Respects back pressure. This is not as efficient as a component
    that produces on each cycle without back pressure, but is
    conceptually simpler.

    Attributes
    ----------

    sizes: Record(POST_PROCESS_SIZES), in
        Depth and repeat count for producing values.

    reset: Signal(1), in
        Initiates a reset, beginning reads from memory
        with new repeat and depth count.

    output_data: Endpoint(POST_PROCESS_PARAMS), out
        Stream of data read from memory

    mem_addr: Signal(addr_width), out
        Address sent to memory.

    mem_data: Signal(POST_PROCESS_PARAMS_WIDTH)), in
        Data received from memory
    """

    def __init__(self):
        self.sizes = Record(POST_PROCESS_SIZES)
        self.reset = Signal()
        self.output_data = Endpoint(POST_PROCESS_PARAMS)
        self.mem_addr = Signal(range(Constants.MAX_CHANNEL_DEPTH))
        self.mem_data = Signal(POST_PROCESS_PARAMS_WIDTH)

    def elab(self, m):
        # Address generator
        m.submodules.addr_gen = addr_gen = LoopingAddressGenerator(
            depth=Constants.MAX_CHANNEL_DEPTH,
            max_repeats=Constants.SYS_ARRAY_HEIGHT)
        m.d.comb += [
            addr_gen.params_input.payload.count.eq(self.sizes.depth),
            addr_gen.params_input.payload.repeats.eq(self.sizes.repeats),
            addr_gen.params_input.valid.eq(self.reset),
            self.mem_addr.eq(addr_gen.addr),
        ]

        # FIFO with reset
        m.submodules.fifo = fifo = ResetInserter(self.reset)(
            StreamFifo(type=POST_PROCESS_PARAMS, depth=3))

        # Generate new addresses while FIFO does not have data (i.e FIFO needs
        # to be primed) or FIFO is outputting data
        with m.If(~self.reset):
            with m.If(~fifo.output.valid):
                m.d.comb += addr_gen.next.eq(1)
            with m.If(fifo.output.is_transferring()):
                m.d.comb += addr_gen.next.eq(1)

        # A cycle after address is generated take data from memory and
        # put in FIFO
        m.d.comb += fifo.input.payload.eq(self.mem_data)
        with m.If(fifo.input.is_transferring()):
            m.d.sync += fifo.input.valid.eq(0)
        with m.If(addr_gen.next):
            m.d.sync += fifo.input.valid.eq(1)

        # Output data is from Fifo
        m.d.comb += [
            self.output_data.payload.eq(fifo.output.payload),
            self.output_data.valid.eq(fifo.output.valid),
            fifo.output.ready.eq(self.output_data.ready),
        ]


class AccumulatorReader(SimpleElaboratable):
    """Reads accumulators, in turn as values become available.

    In normal mode, reads all 8 accumulators. In half_mode, reads
    just accumulators 0, 1, 4 and 5.

    Parameters
    ----------

    accumulator_shape: Shape
        Defaults to signed(32)

    Attributes
    ----------

    accumulator: [Signal(accumulator_shape)] * 8, in
      The value to select.

    accumulator_new: [Signal()] * 8, in
      Strobes when new value available in accumulator.

    half_mode: Signal(), in
      When True, reads only half of the accumulators

    output: Endpoint(accumulator_shape), in
      The accumulated values to convert. Values not read before new values
      are available are lost.
    """

    def __init__(self, accumulator_shape=signed(32)):
        self.accumulator = [Signal(accumulator_shape,
                                   name=f"acc_{i}") for i in range(8)]
        self.accumulator_new = [Signal(name=f"acc_new_{i}") for i in range(8)]
        self.half_mode = Signal()
        self.output = Endpoint(accumulator_shape)

    def elab(self, m):
        # Unset valid on transfer (may be overrridden below)
        with m.If(self.output.ready):
            m.d.sync += self.output.valid.eq(0)

        # Set flag to remember that value is available
        flags = Array(Signal(name=f"flag_{i}") for i in range(8))
        for i in range(8):
            with m.If(self.accumulator_new[i]):
                m.d.sync += flags[i].eq(1)

        # Calculate index of value to output
        index = Signal(range(8))
        next_index = Signal(range(8))
        with m.If(self.half_mode):
            # counts: 0, 1, 4, 5, 0 ...
            m.d.comb += next_index[1].eq(0)
            m.d.comb += Cat(next_index[0], next_index[2]
                            ).eq(Cat(index[0], index[2]) + 1)
        with m.Else():
            m.d.comb += next_index.eq(index + 1)

        # If value available this cycle, or previously
        # - output new value
        # - unset flag
        # - increment index
        with m.If(Array(self.accumulator_new)[index] | flags[index]):
            m.d.sync += [
                self.output.payload.eq(Array(self.accumulator)[index]),
                self.output.valid.eq(1),
                flags[index].eq(0),
                index.eq(next_index),
            ]


class StreamLimiter(SimpleElaboratable):
    """Allows only a certain number of elements to apss through stream.

    Counts a given number of items, then signals that it is done.

    Parameters
    ----------

    payload_type:
        The type carried by the stream

    Attributes
    ----------

    stream_in: Endpoint(payload_type), in
        The incoming stream. Will always be ready after start and
        until done.
    stream_out: Endpoint(payload_type), out
        The outgoing stream. Does not respect back pressure.

    num_allowed: Signal(18), in
        The number of items allowed to pass.

    start: Signal(), in
        Pulse high to allow items beginning next cycle.

    running: Signal(), out
        Indicates that items are being allowed to pass

    finished: Signal(), out
        Indicates that last item has been handled.
    """

    def __init__(self, payload_type=signed(32)):
        self.stream_in = Endpoint(payload_type)
        self.stream_out = Endpoint(payload_type)
        self.num_allowed = Signal(18)
        self.start = Signal()
        self.running = Signal()
        self.finished = Signal()

    def elab(self, m):
        m.d.sync += self.finished.eq(0)
        m.d.comb += [
            self.stream_in.ready.eq(self.running),
            self.stream_out.valid.eq(self.stream_in.is_transferring()),
            self.stream_out.payload.eq(self.stream_in.payload),
        ]
        counter = Signal.like(self.num_allowed)
        with m.If(self.start):
            m.d.sync += counter.eq(self.num_allowed)
        with m.If(self.stream_in.is_transferring()):
            m.d.sync += counter.eq(counter - 1)
            with m.If(counter == 1):
                m.d.sync += self.finished.eq(1)
        m.d.comb += self.running.eq(counter != 0)


class OutputWordAssembler(SimpleElaboratable):
    """Assembles output values into words.

    The output from the post process pipeline consists of interleaved values
    from four separate output pixels. This component reassembles the values
    into words, one per output channel.

    Output words are interleaved in the same order as the bytes were.

    TODO: add a reset signal to ensure output always synchronized
    TODO: add an error signal to catch output buffer overflow

    Parameters
    ----------

    num_pixels: int
        The maximum depth required for writes. Determines addr_width.

    Attributes
    ----------

    half_mode: Signal, in
      In normal mode, buffers data over four pixels. In half mode only buffers
      data over two pixels.

    input: Endpoint(signed(8)), in
      The 8-bit quantized versions of the accumulator. Always ready.

    output: Endpoint(unsigned(32)), out
      The assembled 32 bit words. Assumes always ready.
    """

    def __init__(self, num_pixels=Constants.SYS_ARRAY_HEIGHT):
        self._num_pixels = num_pixels
        self.half_mode = Signal()
        self.input = Endpoint(signed(8))
        self.output = Endpoint(unsigned(32))

    def elab(self, m):
        # number of bytes received already
        byte_count = Signal(range(4))
        # output channel for next byte received
        pixel_index = Signal(range(self._num_pixels))
        # shift registers to buffer 3 incoming values
        shift_registers = Array(
            [Signal(24, name=f"sr_{i}") for i in range(self._num_pixels)])

        last_pixel_index = Signal.like(pixel_index)
        m.d.sync += last_pixel_index.eq(Mux(self.half_mode,
                                            self._num_pixels // 2 - 1,
                                            self._num_pixels - 1))
        next_pixel_index = Signal.like(pixel_index)
        m.d.comb += next_pixel_index.eq(Mux(pixel_index == last_pixel_index,
                                            0, pixel_index + 1))

        m.d.comb += self.input.ready.eq(1)
        with m.If(self.input.is_transferring()):
            sr = shift_registers[pixel_index]
            with m.If(byte_count == 3):
                # Output current value and shift register
                m.d.comb += self.output.valid.eq(1)
                payload = Cat(sr, self.input.payload)
                m.d.comb += self.output.payload.eq(payload)
            with m.Else():
                # Save input to shift register
                m.d.sync += sr[-8:].eq(self.input.payload)
                m.d.sync += sr[:-8].eq(sr[8:])

            # Increment pixel index
            m.d.sync += pixel_index.eq(next_pixel_index)
            with m.If(pixel_index == last_pixel_index):
                m.d.sync += pixel_index.eq(0)
                m.d.sync += byte_count.eq(byte_count + 1)  # allow rollover
