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


from nmigen_cfu import SimpleElaboratable, InstructionBase
from nmigen import signed, unsigned, Memory, Module, Mux, Record, Signal

from .stream import BinaryPipelineActor
from .constants import Constants
from .stream import connect, Endpoint, BinaryPipelineActor


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
    ('dividend', signed(32)),
    ('shift', unsigned(4))
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
        threshold = Signal(signed(32))
        quotient = Signal(signed(32))
        rounding = Signal()
        with m.Switch(shift):
            for n in range(3, 12):
                with m.Case(n):
                    mask = (1 << n) - 1
                    m.d.comb += remainder.eq(dividend & mask)
                    m.d.comb += threshold.eq((mask >> 1) +
                                             Mux(dividend < 0, 1, 0))
                    m.d.comb += quotient.eq(dividend >> n)
        m.d.sync += result.eq(quotient + Mux(remainder > threshold, 1, 0))

        # Cycle 2: send output
        m.d.sync += out_value.eq(result)


OUTPUT_PARAMS = [
    ('bias', signed(16)),
    ('multiplier', signed(32)),
    ('shift', unsigned(4)),
]


class OutputParamsStorage(SimpleElaboratable):
    """Stores output parameters.

    Interface is not very well defined in the case of simultaneous reads
    and writes. The intention is that reads and writes woule happen
    separately.

    Attributes:

    reset: Signal(), in
      resets the state of the store
    write_enable: Signal(), in
      Indicates write_data isto be written to the store.
    write_data: Record(OUTPUT_PARAMS), in
      The data to be written
    read_enable: Signal(), in
      Indicates next data is to be read. It will be available on the
      next cycle. write_enable takes precedence over read_enable.
    read_data: Record(OUTPUT_PARAMS), out
      Data being read from store.
    """

    def __init__(self):
        self.reset = Signal()
        self.write_enable = Signal()
        self.write_data = Record(OUTPUT_PARAMS)
        self.read_enable = Signal()
        self.read_data = Record(OUTPUT_PARAMS)

    def elab(self, m):
        memory = Memory(
            depth=Constants.MAX_CHANNELS,
            width=len(self.read_data))
        m.submodules.write_port = write_port = memory.write_port()
        m.submodules.read_port = read_port = memory.read_port(
            transparent=False)

        write_index = Signal(range(Constants.MAX_CHANNELS))
        read_index = Signal(range(Constants.MAX_CHANNELS))

        m.d.comb += write_port.en.eq(self.write_enable)
        m.d.comb += write_port.addr.eq(write_index)
        m.d.comb += write_port.data.eq(self.write_data.as_value())
        with m.If(self.write_enable):
            m.d.sync += write_index.eq(write_index + 1)

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


class PostProcessPipeline(SimpleElaboratable):
    """Converts an accumulator into an 8-bit value

    Attributes
    ----------

    input: Endpoint(signed(32)), in
      The accumulated value to convert
    output: Endpoint(signed(8)), out
      The 8-bit quantized version of the accumulator

    offset: signed(9), in
       The output offset
    activation_min: signed(8), out
        The minimum output value
    activation_max: signed(8), out
        The maximum output value

    read_data: Record(OUTPUT_PARAMS), in
      Data read from OutputStorageParams
    read_enable: Signal(), out
      Tells OutputStorageParams to read next
    """

    PIPELINE_CYCLES = (
        SaturatingRoundingDoubleHighMul.PIPELINE_CYCLES +
        RoundingDivideByPowerOfTwo.PIPELINE_CYCLES +
        SaturateActivationPipeline.PIPELINE_CYCLES
    )

    def __init__(self):
        self.input = Endpoint(signed(32))
        self.output = Endpoint(signed(8))
        self.offset = Signal(signed(9))
        self.activation_min = Signal(signed(8))
        self.activation_max = Signal(signed(8))
        self.read_data = Record(OUTPUT_PARAMS)
        self.read_enable = Signal()

    def elab(self, m: Module):
        # Input always ready
        m.d.comb += self.input.ready.eq(1)

        # Pipelines
        m.submodules.srdhm = srdhm = SaturatingRoundingDoubleHighMul()
        m.submodules.rdbpot = rdbpot = RoundingDivideByPowerOfTwo()
        m.submodules.sap = sap = SaturateActivationPipeline()

        # On incoming valid, put data into pipeline and get next set of
        # OUTPUT_PARAMS
        m.d.comb += [
            srdhm.input.valid.eq(self.input.valid),
            srdhm.input.payload.a.eq(self.input.payload + self.read_data.bias),
            srdhm.input.payload.b.eq(self.read_data.multiplier),
            self.read_enable.eq(self.input.valid),
        ]

        # Connect the output of srdhm to rdbpot, along with the shift
        delayed_shift = delay(m, self.read_data.shift,
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


class PostProcessInstruction(InstructionBase):
    """An instruction used to perform post procesing tasks.

    Attributes
    ----------

    offset: signed(9), in
       The output offset
    activation_min: signed(8), out
        The minimum output value
    activation_max: signed(8), out
        The maximum output value

    read_data: Record(OUTPUT_PARAMS), in
      Data read from OutputStorageParams
    read_enable: Signal(), out
      Tells OutputStorageParams to read next
    """

    def __init__(self):
        super().__init__()
        self.offset = Signal(signed(9))
        self.activation_min = Signal(signed(8))
        self.activation_max = Signal(signed(8))
        self.read_data = Record(OUTPUT_PARAMS)
        self.read_enable = Signal()

    def elab(self, m: Module):
        m.submodules.srdhm = srdhm = SaturatingRoundingDoubleHighMul()
        m.d.comb += srdhm.output.ready.eq(1)
        m.submodules.rdbpot = rdbpot = RoundingDivideByPowerOfTwo()
        m.d.comb += rdbpot.output.ready.eq(1)

        # Connect the post process pipeline
        m.submodules.ppp = ppp = PostProcessPipeline()
        m.d.comb += ppp.output.ready.eq(1)
        m.d.comb += [
            ppp.offset.eq(self.offset),
            ppp.activation_min.eq(self.activation_min),
            ppp.activation_max.eq(self.activation_max),
            ppp.read_data.eq(self.read_data),
            self.read_enable.eq(ppp.read_enable),
        ]

        m.d.sync += self.done.eq(0)
        with m.FSM(reset="WAIT_START"):
            with m.State("WAIT_START"):
                with m.If(self.start):
                    with m.Switch(self.funct7):
                        with m.Case(Constants.PP_SRDHM):
                            m.d.comb += [
                                srdhm.input.payload.a.eq(self.in0s),
                                srdhm.input.payload.b.eq(self.in1s),
                                srdhm.input.valid.eq(1),
                            ]
                            m.next = "SRDHM_RUN"
                        with m.Case(Constants.PP_RDBPOT):
                            m.d.comb += [
                                rdbpot.input.payload.dividend.eq(self.in0s),
                                rdbpot.input.payload.shift.eq(-self.in1s),
                                rdbpot.input.valid.eq(1),
                            ]
                            m.next = "RDBPOT_RUN"
                        with m.Case(Constants.PP_POST_PROCESS):
                            m.d.comb += [
                                ppp.input.payload.eq(self.in0s),
                                ppp.input.valid.eq(1),
                            ]
                            m.next = "POST_PROCESS_RUN"
                        with m.Default():
                            m.d.sync += self.done.eq(1)
            with m.State("SRDHM_RUN"):
                with m.If(srdhm.output.valid):
                    m.d.sync += self.output.eq(srdhm.output.payload)
                    m.d.sync += self.done.eq(1)
                    m.next = "WAIT_START"
            with m.State("RDBPOT_RUN"):
                with m.If(rdbpot.output.valid):
                    m.d.sync += self.output.eq(rdbpot.output.payload)
                    m.d.sync += self.done.eq(1)
                    m.next = "WAIT_START"
            with m.State("POST_PROCESS_RUN"):
                with m.If(ppp.output.valid):
                    m.d.sync += self.output.eq(ppp.output.payload)
                    m.d.sync += self.done.eq(1)
                    m.next = "WAIT_START"
