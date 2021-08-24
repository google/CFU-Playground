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

from nmigen import Cat, Signal, unsigned
from nmigen_cfu import Cfu, InstructionBase
from util import all_words

from .constants import Constants
from .filter_store import FilterStore
from .get import GetInstruction
from .input_store import InputStore
from .macc import MultiplyAccumulate
from .set import SetInstruction
from .stream import BinaryCombinatorialActor


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


class AddOneActor(BinaryCombinatorialActor):
    """A binary actor that adds one to a stream of integers.

    Used to implement the verification register.
    """

    def __init__(self):
        super().__init__(unsigned(32), unsigned(32))

    def transform(self, m, input, output):
        m.d.comb += output.eq(input + 1)


class HpsCfu(Cfu):

    def __init__(self, filter_store_depth=Constants.MAX_FILTER_WORDS):
        super().__init__()
        self.filter_store_depth = filter_store_depth

    def connect_verify_register(self, m, set, get):
        set_source = set.sources[Constants.REG_VERIFY]
        get_sink = get.sinks[Constants.REG_VERIFY]
        m.submodules["add_one"] = add_one = AddOneActor()
        m.d.comb += [
            set_source.connect(add_one.sink),
            add_one.source.connect(get_sink)
        ]

    def connect_macc(self, m, set, macc, get):
        m.d.comb += macc.offset.eq(set.values[Constants.REG_INPUT_OFFSET])

        inputs = Cat(set.values[Constants.REG_MACC_INPUT_0],
                     set.values[Constants.REG_MACC_INPUT_1],
                     set.values[Constants.REG_MACC_INPUT_2],
                     set.values[Constants.REG_MACC_INPUT_3])
        for n, val in enumerate(all_words(inputs, 8)):
            m.d.comb += macc.inputs[n].eq(val)
        filters = Cat(set.values[Constants.REG_MACC_FILTER_0],
                      set.values[Constants.REG_MACC_FILTER_1],
                      set.values[Constants.REG_MACC_FILTER_2],
                      set.values[Constants.REG_MACC_FILTER_3])
        for n, val in enumerate(all_words(filters, 8)):
            m.d.comb += macc.filters[n].eq(val)

        result_sink = get.sinks[Constants.REG_MACC_OUT]
        m.d.comb += [
            result_sink.valid.eq(1),
            result_sink.payload.eq(macc.result),
        ]

    def connect_input_store(self, m, set, get, input_store):
        next = get.read_strobes[Constants.REG_INPUT_3]
        m.d.comb += [
            set.sources[Constants.REG_INPUT_NUM_WORDS].connect(
                input_store.num_words),
            set.sources[Constants.REG_SET_INPUT].connect(input_store.input),
            input_store.output[0].connect(get.sinks[Constants.REG_INPUT_0]),
            input_store.output[1].connect(get.sinks[Constants.REG_INPUT_1]),
            input_store.output[2].connect(get.sinks[Constants.REG_INPUT_2]),
            input_store.output[3].connect(get.sinks[Constants.REG_INPUT_3]),
            input_store.next.eq(next),
            get.invalidates[Constants.REG_INPUT_0].eq(next),
            get.invalidates[Constants.REG_INPUT_1].eq(next),
            get.invalidates[Constants.REG_INPUT_2].eq(next),
            get.invalidates[Constants.REG_INPUT_3].eq(next),
        ]

    def connect_filter_store(self, m, set, get, filter_store):
        next = get.read_strobes[Constants.REG_FILTER_3]
        m.d.comb += [
            set.sources[Constants.REG_FILTER_NUM_WORDS].connect(
                filter_store.num_words),
            set.sources[Constants.REG_SET_FILTER].connect(filter_store.input),
            filter_store.output[0].connect(get.sinks[Constants.REG_FILTER_0]),
            filter_store.output[1].connect(get.sinks[Constants.REG_FILTER_1]),
            filter_store.output[2].connect(get.sinks[Constants.REG_FILTER_2]),
            filter_store.output[3].connect(get.sinks[Constants.REG_FILTER_3]),
            filter_store.next.eq(next),
            get.invalidates[Constants.REG_FILTER_0].eq(next),
            get.invalidates[Constants.REG_FILTER_1].eq(next),
            get.invalidates[Constants.REG_FILTER_2].eq(next),
            get.invalidates[Constants.REG_FILTER_3].eq(next),
        ]

    def elab_instructions(self, m):
        m.submodules['set'] = set = SetInstruction()
        m.submodules['get'] = get = GetInstruction()

        self.connect_verify_register(m, set, get)

        m.submodules['macc'] = macc = MultiplyAccumulate(16)
        m.d.comb += macc.enable.eq(1)
        self.connect_macc(m, set, macc, get)

        m.submodules['input_store'] = input_store = InputStore()
        self.connect_input_store(m, set, get, input_store)

        filter_store = FilterStore(depth=self.filter_store_depth)
        m.submodules['filter_store'] = filter_store
        self.connect_filter_store(m, set, get, filter_store)

        m.submodules['ping'] = ping = PingInstruction()
        return {
            Constants.INS_GET: get,
            Constants.INS_SET: set,
            Constants.INS_PING: ping,
        }


def make_cfu(**kwargs):
    return HpsCfu(**kwargs)
