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


class FilterStore(SimpleElaboratable):
    """Stores filter values one word at a time and outputs four words at a time.

    Designed for use in this sequence:
    (1) Set value of num_words
    (2) Set num_words words of filter values
    (3) Read outputs until done
    (4) Go back to step (1)

    Will not accept input until num_words is set. Will not produce
    output until num_words of input have been accepted. Will not
    accept more than num_words of input. Setting num_words will
    place FilterStore back in a mode where it is accepting input.

    Parameters
    ----------

    depth: int
      Maximum capacity of the filter store, in 32-bit words.
      The num_words signal's value must not exceed this depth.

    Attributes
    ----------

    data_input: Endpoint(unsigned(32)), in
      Words written to data_input are set into the filter store.

    next: Signal(), in
      Causes the next four words to be displayed at the data_output stream.

    num_words_input: Endpoint(unsigned(32)), in
      Number of words in input. When set, resets internal state.

    data_output: Endpoint(unsigned(128)), out
      The four words of output. Does not respect backpressure.
      TODO(dcallagh): make it respect backpressure.
    """

    def __init__(self, depth=Constants.MAX_FILTER_WORDS):
        self.depth = depth
        self.data_input = Endpoint(unsigned(32))
        self.next = Signal()
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
                m.d.sync += index.eq(0)
                m.next = "READING"

    def handle_reading(self, m, memory, num_words, index):
        """Handle stepping through memory on read."""
        m.d.comb += [
            memory.read_addr.eq(index[2:]),
            self.data_output.payload.eq(memory.read_data),
        ]
        with m.If(self.next):
            m.d.sync += self.data_output.valid.eq(1)
        with m.If(~self.next & self.data_output.is_transferring()):
            m.d.sync += self.data_output.valid.eq(0)
        with m.If(self.data_output.is_transferring()):
            m.d.sync += [index.eq(Mux(index == num_words - 4, 0, index + 4))]

    def elab(self, m: Module):
        num_words = Signal(range(self.depth + 1))
        index = Signal(range(self.depth))
        reset = Signal()
        m.d.comb += reset.eq(self.num_words_input.valid)
        memory = WideReadMemory(depth=self.depth)
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
                self.handle_reading(m, memory, num_words, index)
                with m.If(reset):
                    m.next = "RESET"
