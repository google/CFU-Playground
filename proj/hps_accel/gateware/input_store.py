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
from nmigen import unsigned, Signal, Module, Array, Mux

from .constants import Constants
from .stream import Endpoint, connect
from .sp_mem import MemoryParameters, SinglePortMemory


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

    data-input: Endpoint(unsigned(32)), in
      Words written to input are set into the input store.

    next: Signal(), in
      Causes the next four words to be displayed at the output.

    num_words_input: Endpoint(unsigned(32)), in
      Number of words in input. When set, resets internal storage.

    output_data: list of 4 Endpoint(unsigned(32)), out
      The four words of output.

    """

    def __init__(self):
        self.data_input = Endpoint(unsigned(32))
        self.next = Signal()
        self.num_words_input = Endpoint(unsigned(32))
        self.data_output = [Endpoint(unsigned(32), name=f"output_{i}")
                            for i in range(4)]

    def create_memories(self, m, index, read_required):
        """Builds memories with data outputs connected to this module's
         outputs.
         """
        params = MemoryParameters(width=32, depth=Constants.MAX_INPUT_WORDS // 4)
        memories = Array([SinglePortMemory(params=params) for _ in range(4)])
        for n, memory in enumerate(memories):
            m.submodules[f"mem_{n}"] = memory
            # On read_required read the next set of addresses
            addr_stream = memory.read_addr_input
            m.d.comb += addr_stream.payload.eq(index[2:])
            read_waiting = Signal()  # waiting for addr to transfer
            m.d.comb += addr_stream.valid.eq(read_required | read_waiting)
            with m.If(read_required):
                m.d.sync += read_waiting.eq(1)
            with m.If(addr_stream.is_transferring()):
                m.d.sync += read_waiting.eq(0)
            # Connect each memory output to module output
            m.d.comb += connect(memory.read_data_output, self.data_output[n])
        return memories

    def handle_writing(self, m, memories, num_words, index, read_required):
        """Receives values into memory, 1 word at a time."""
        # Connect data_input to correct memory, based on write_index
        target_mem = memories[index[:2]]
        m.d.comb += [
            self.data_input.ready.eq(target_mem.write_input.ready),
            target_mem.write_input.valid.eq(self.data_input.valid),
        ]
        for mem in memories:
            write_cmd = mem.write_input.payload
            m.d.comb += write_cmd.data.eq(self.data_input.payload)
            m.d.comb += write_cmd.addr.eq(index[2:])

        # On data transferred OK, increment index, check if finished
        with m.If(self.data_input.is_transferring()):
            m.d.sync += index.eq(index + 1)
            with m.If(index == num_words - 1):
                m.d.sync += index.eq(0)
                m.d.sync += read_required.eq(1)
                m.next = "READING"

    def handle_reading(self, m, num_words, index, read_required):
        """Handle stepping through memory on read."""
        m.d.sync += read_required.eq(self.next)
        with m.If(self.next):
            m.d.sync += [index.eq(Mux(index == num_words - 4, 0, index + 4))]

    def elab(self, m: Module):
        num_words = Signal(range(Constants.MAX_INPUT_WORDS + 1))
        index = Signal(Constants.MAX_INPUT_WORDS)
        reset = Signal()
        read_required = Signal()
        m.d.comb += reset.eq(self.num_words_input.valid)
        memories = self.create_memories(m, index, read_required)

        with m.FSM(reset="RESET"):
            with m.State("RESET"):
                m.d.sync += num_words.eq(0)
                m.d.sync += index.eq(0)
                m.d.sync += read_required.eq(0)
                # TODO: reset memories
                m.next = "NUM_WORDS"
            with m.State("NUM_WORDS"):
                m.d.comb += self.num_words_input.ready.eq(1)
                with m.If(self.num_words_input.is_transferring()):
                    m.d.sync += num_words.eq(self.num_words_input.payload)
                    m.next = "WRITING"
            with m.State("WRITING"):
                self.handle_writing(
                    m, memories, num_words, index, read_required)
                with m.If(reset):
                    m.next = "RESET"
            with m.State("READING"):
                self.handle_reading(m, num_words, index, read_required)
                with m.If(reset):
                    m.next = "RESET"
