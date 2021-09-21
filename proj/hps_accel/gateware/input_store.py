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
from nmigen import unsigned, Signal, Module, Mux

from .constants import Constants
from .mem import WideReadMemory
from .stream import Endpoint, connect


class InputStore(SimpleElaboratable):
    """Stores input one word at a time and outputs four words at a time.

    Designed for use in this sequence:
    (1) Set value of num_words
    (2) Set num_words words of input
    (3) Read outputs until done
    (4) Go back to step (1)

    Will not accept input until num_words is set. Will not produce
    output until num_words of input have been accepted. Will not
    accept more than num_words of input. Setting num_words will
    place InputStore back in a mode where it is accepting input.

    Attributes
    ----------

    data_input: Endpoint(unsigned(32)), in
      Words written to input are set into the input store.

    num_words_input: Endpoint(unsigned(32)), in
      Number of words in input. When set, resets internal state.

    data_output: Endpoint(unsigned(128)), out
      The four words of output.
    """

    def __init__(self):
        self.data_input = Endpoint(unsigned(32))
        self.num_words_input = Endpoint(unsigned(32))
        self.data_output = Endpoint(unsigned(128))

    def handle_writing(self, m, memory, num_words, index):
        """Receives values into memory, 1 word at a time."""
        # Connect data_input to memory
        m.d.comb += [
            memory.write_addr.eq(index),
            memory.write_data.eq(self.data_input.payload),
            memory.write_enable.eq(1),
        ]

        # On data transferred OK, increment index, check if finished
        m.d.comb += self.data_input.ready.eq(1)
        with m.If(self.data_input.is_transferring()):
            m.d.sync += index.eq(index + 1)
            with m.If(index == num_words - 1):
                m.d.sync += index.eq(num_words - 4)
                m.next = "READING"

    def handle_reading(self, m, memory, num_words, index, reset):
        """Handle stepping through memory on read."""
        m.d.comb += memory.read_addr.eq(index[2:])

        read_port_valid = Signal()
        read_started = Signal()

        with m.If(~self.data_output.valid | self.data_output.is_transferring()):
            m.d.sync += self.data_output.payload.eq(memory.read_data)
            m.d.sync += self.data_output.valid.eq(read_port_valid)
            m.d.sync += read_port_valid.eq(0)

        with m.If(~read_port_valid & ~read_started):
            m.d.sync += index.eq(Mux(index == num_words - 4, 0, index + 4))
            m.d.sync += read_started.eq(1)
        with m.Else():
            m.d.sync += read_started.eq(0)

        with m.If(read_started):
            # Read port is valid next cycle if we started a new read this cycle
            m.d.sync += read_port_valid.eq(1)

        with m.If(reset):
            m.d.sync += read_port_valid.eq(0)
            m.d.sync += read_started.eq(0)

    def elab(self, m: Module):
        num_words = Signal(range(Constants.MAX_INPUT_WORDS + 1))
        index = Signal(range(Constants.MAX_INPUT_WORDS))
        reset = Signal()
        m.d.comb += reset.eq(self.num_words_input.valid)
        memory = WideReadMemory(depth=Constants.MAX_INPUT_WORDS)
        m.submodules['memory'] = memory

        with m.FSM(reset="RESET"):
            with m.State("RESET"):
                m.d.sync += num_words.eq(0)
                m.d.sync += index.eq(0)
                m.d.sync += self.data_output.valid.eq(0)
                m.next = "NUM_WORDS"
            with m.State("NUM_WORDS"):
                m.d.comb += self.num_words_input.ready.eq(1)
                with m.If(self.num_words_input.is_transferring()):
                    m.d.sync += num_words.eq(self.num_words_input.payload)
                    m.next = "WRITING"
            with m.State("WRITING"):
                self.handle_writing(m, memory, num_words, index)
                with m.If(reset):
                    m.next = "RESET"
            with m.State("READING"):
                self.handle_reading(m, memory, num_words, index, reset)
                with m.If(reset):
                    m.next = "RESET"
