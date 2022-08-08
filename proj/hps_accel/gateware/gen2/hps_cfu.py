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

from amaranth import Cat, Mux, Record, Signal, signed, unsigned

from .accelerator import AcceleratorCore, ACCELERATOR_CONFIGURATION_LAYOUT
from ..cfu import Cfu, InstructionBase
from .constants import Constants
from .filter import FILTER_WRITE_COMMAND
from .post_process import POST_PROCESS_PARAMS
from ..stream import connect, Endpoint
from ..stream.fifo import StreamFifo


class PingInstruction(InstructionBase):
    """An instruction used to verify simple CFU functionality.

    Adds the two arguments and stores the result. The previously stored value
    is returned.
    """

    def elab(self, m):
        stored_value = Signal(32)
        with m.If(self.start):
            m.d.sync += [
                stored_value.eq(self.in0 + self.in1),
                self.output.eq(stored_value),
                self.done.eq(1),
            ]
        with m.Else():
            m.d.sync += self.done.eq(0)


class GetInstruction(InstructionBase):
    """Handles sending values from CFU to CPU.

    Attributes
    ----------

    reg_fifo_items_value: Signal(32), in
        The value to return for the fifo item count register.
    reg_verify_value: Signal(32), in
        The value to return for the verify register.

    output_words: Endpoint(unsigned(32)), in
        Stream of output words from accelerator.
    """

    def __init__(self):
        super().__init__()
        self.reg_fifo_items_value = Signal(32)
        self.reg_verify_value = Signal(32)
        self.output_words = Endpoint(unsigned(32))

    def elab(self, m):
        m.d.sync += self.done.eq(0)

        def get_output():
            m.d.comb += self.output_words.ready.eq(1)
            with m.If(self.output_words.is_transferring()):
                m.d.sync += self.output.eq(self.output_words.payload)
                m.d.sync += self.done.eq(1)
                m.next = "WAIT_START"
            with m.Else():
                m.next = "WAIT_OUTPUT"

        with m.FSM():
            with m.State("WAIT_START"):
                with m.If(self.start):
                    with m.If(self.funct7 == Constants.REG_VERIFY):
                        m.d.sync += self.output.eq(self.reg_verify_value)
                        m.d.sync += self.done.eq(1)
                    with m.Elif(self.funct7 == Constants.REG_FIFO_ITEMS):
                        m.d.sync += self.output.eq(self.reg_fifo_items_value)
                        m.d.sync += self.done.eq(1)
                    with m.Elif(self.funct7 == Constants.REG_OUTPUT_WORD):
                        get_output()
            with m.State("WAIT_OUTPUT"):
                get_output()


class SetInstruction(InstructionBase):
    """Handles sending values from CPU to CFU

    Attributes
    ----------

    reg_verify_value: Signal(32), out
       The value last set into the verify register

    accelerator_start: Signal(), out
       Toggles when start register written

    accelerator_reset: Signal(), out
       Toggles when reset register written

    config: Record(ACCELERATOR_CONFIGURATION_LAYOUT), out
       Configuration values for accelerator core, as received
       from set instructions.

    filter_output: Endpoint(FILTER_WRITE_COMMAND), out
        Write command for filter store

    post_process_params: Endpoint(POST_PROCESS_PARAMS), out
        Stream of data to write to post_process memory.
    """

    def __init__(self):
        super().__init__()
        self.reg_verify_value = Signal(32)
        self.accelerator_start = Signal()
        self.accelerator_reset = Signal()
        self.config = Record(ACCELERATOR_CONFIGURATION_LAYOUT)
        self.filter_output = Endpoint(FILTER_WRITE_COMMAND)
        self.post_process_params = Endpoint(POST_PROCESS_PARAMS)

    def elab(self, m):
        # Default toggles to off
        m.d.sync += self.accelerator_start.eq(0)
        m.d.sync += self.accelerator_reset.eq(0)
        m.d.sync += self.filter_output.valid.eq(0)
        m.d.sync += self.post_process_params.valid.eq(0)

        # All sets take exactly one cycle
        m.d.sync += self.done.eq(0)

        # Perform action
        with m.If(self.start):
            with m.Switch(self.funct7):
                with m.Case(Constants.REG_VERIFY):
                    m.d.sync += self.reg_verify_value.eq(self.in0)
                with m.Case(Constants.REG_ACCELERATOR_START):
                    m.d.sync += self.accelerator_start.eq(1)
                with m.Case(Constants.REG_ACCELERATOR_RESET):
                    m.d.sync += self.accelerator_reset.eq(1)
                with m.Case(Constants.REG_FILTER_WRITE):
                    m.d.sync += [
                        self.filter_output.payload.store.eq(self.in0[16:]),
                        self.filter_output.payload.addr.eq(self.in0[:16]),
                        self.filter_output.payload.data.eq(self.in1),
                        self.filter_output.valid.eq(1),
                    ]
                with m.Case(Constants.REG_MODE):
                    m.d.sync += self.config.mode.eq(self.in0)
                with m.Case(Constants.REG_INPUT_OFFSET):
                    m.d.sync += self.config.input_offset.eq(self.in0s)
                with m.Case(Constants.REG_NUM_FILTER_WORDS):
                    m.d.sync += self.config.num_filter_words.eq(self.in0)
                with m.Case(Constants.REG_OUTPUT_OFFSET):
                    m.d.sync += self.config.output_offset.eq(self.in0s)
                with m.Case(Constants.REG_OUTPUT_ACTIVATION_MIN):
                    m.d.sync += self.config.output_activation_min.eq(self.in0s)
                with m.Case(Constants.REG_OUTPUT_ACTIVATION_MAX):
                    m.d.sync += self.config.output_activation_max.eq(self.in0s)
                with m.Case(Constants.REG_INPUT_BASE_ADDR):
                    m.d.sync += self.config.input_base_addr.eq(self.in0)
                with m.Case(Constants.REG_NUM_PIXELS_X):
                    m.d.sync += self.config.num_pixels_x.eq(self.in0)
                with m.Case(Constants.REG_PIXEL_ADVANCE_X):
                    m.d.sync += self.config.pixel_advance_x.eq(self.in0)
                with m.Case(Constants.REG_PIXEL_ADVANCE_Y):
                    m.d.sync += self.config.pixel_advance_y.eq(self.in0)
                with m.Case(Constants.REG_INPUT_CHANNEL_DEPTH):
                    m.d.sync += self.config.input_channel_depth.eq(self.in0)
                with m.Case(Constants.REG_OUTPUT_CHANNEL_DEPTH):
                    m.d.sync += self.config.output_channel_depth.eq(self.in0)
                with m.Case(Constants.REG_NUM_OUTPUT_VALUES):
                    m.d.sync += self.config.num_output_values.eq(self.in0)
                with m.Case(Constants.REG_POST_PROCESS_BIAS):
                    m.d.sync += self.post_process_params.payload.bias.eq(
                        self.in0s)
                with m.Case(Constants.REG_POST_PROCESS_SHIFT):
                    m.d.sync += self.post_process_params.payload.shift.eq(
                        self.in0)
                with m.Case(Constants.REG_POST_PROCESS_MULTIPLIER):
                    m.d.sync += [
                        self.post_process_params.payload.multiplier.eq(
                            self.in0s),
                        self.post_process_params.valid.eq(1),
                    ]
            m.d.sync += self.done.eq(1)


class PoolInstruction(InstructionBase):
    """Handles 8-bit Max Pool operation.

    Returns one word, where each byte is the maximum of the current two and
    previous two inputs.
    """

    def elab(self, m):
        def max_(word0, word1):
            result = [Signal(8, name=f"result{i}") for i in range(4)]
            bytes0 = [word0[i:i + 8] for i in range(0, 32, 8)]
            bytes1 = [word1[i:i + 8] for i in range(0, 32, 8)]
            for r, b0, b1 in zip(result, bytes0, bytes1):
                sb0 = Signal(signed(8))
                m.d.comb += sb0.eq(b0)
                sb1 = Signal(signed(8))
                m.d.comb += sb1.eq(b1)
                m.d.comb += r.eq(Mux(sb1 > sb0, b1, b0))
            return Cat(*result)

        last2 = Signal(32)
        m.d.sync += self.done.eq(0)
        with m.If(self.start):
            this2 = Signal(32)
            m.d.comb += this2.eq(max_(self.in0, self.in1))
            m.d.sync += self.output.eq(max_(this2, last2))
            m.d.sync += last2.eq(this2)
            m.d.sync += self.done.eq(1)


class HpsCfu(Cfu):
    """Gen2 accelerator CFU.
    """
    def __init__(self, specialize_nx=False):
        """Constructor

        Args:
           specialize_nx: generate code for the Crosslink/NX-17.
        """
        super().__init__()
        self._specialize_nx = specialize_nx

    def elab_instructions(self, m):
        m.submodules['ping'] = ping = PingInstruction()
        m.submodules['set'] = set_ = SetInstruction()
        m.submodules['get'] = get = GetInstruction()
        m.submodules['pool'] = pool = PoolInstruction()
        m.submodules['core'] = core = AcceleratorCore(self._specialize_nx)
        m.submodules['fifo'] = fifo = StreamFifo(
            depth=Constants.OUTPUT_FIFO_DEPTH, type=unsigned(32))

        # Connect set_ and get instructions to accelerator core and FIFO
        m.d.comb += [
            core.start.eq(set_.accelerator_start),
            core.reset.eq(set_.accelerator_reset),
            core.config.eq(set_.config),
            get.reg_fifo_items_value.eq(fifo.r_level),
        ]
        m.d.comb += connect(set_.filter_output, core.write_filter_input)
        m.d.comb += connect(set_.post_process_params, core.post_process_params)
        m.d.comb += connect(core.output, fifo.input)
        m.d.comb += connect(fifo.output, get.output_words)

        # Connect accelerator LRAMs
        for i in range(4):
            m.d.comb += [
                self.lram_addr[i].eq(core.lram_addr[i]),
                core.lram_data[i].eq(self.lram_data[i]),
            ]

        # Connect verify functionality
        m.d.comb += get.reg_verify_value.eq(set_.reg_verify_value + 1)

        return {
            Constants.INS_GET: get,
            Constants.INS_SET: set_,
            Constants.INS_POOL: pool,
            Constants.INS_PING: ping,
        }


def make_cfu(specialize_nx):
    """Returns the gen2 CFU design.

    Args:
        specialize_nx: generate code for the Crosslink/NX-17.
    """
    return HpsCfu(specialize_nx)
