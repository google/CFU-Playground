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

from nmigen import Signal, signed, unsigned
from nmigen.hdl.rec import Layout
from nmigen_cfu import Cfu, InstructionBase, SimpleElaboratable, all_words

from .constants import Constants
from .filter_store import FilterStore
from .get import GetInstruction
from .input_store import InputStore
from .macc import MultiplyAccumulate
from .post_process import OutputParamsStorage, PostProcessInstruction
from .set import SetInstruction
from ..stream import BinaryCombinatorialActor, ConcatenatingBuffer, \
    Endpoint, FlowRestrictor, connect


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


class ResultAccumulator(SimpleElaboratable):
    """Accumulates a stream of results from the multiply-accumulate operation.

    Attributes
    ----------

    num_results: Endpoint(unsigned(32)), in
      Number of results to accumulate. Each time a new value N is received at
      this endpoint, the accumulator will begin accepting N results into its
      *results* stream.
    results: Endpoint(unsigned(32)), in
      Input from the multiply-accumulate unit. The stream stays paused until
      the accumulator is triggered by receiving a number at the *num_results*
      endpoint.
    accumulated: Endpoint(signed(32)), out
      Accumulated output value. This is the sum of all N results received.
    """

    def __init__(self):
        self.num_results = Endpoint(unsigned(32))
        self.results = Endpoint(signed(32))
        self.accumulated = Endpoint(signed(32))

    def elab(self, m):
        results_counter = Signal.like(self.num_results.payload)
        accumulator = Signal.like(self.accumulated.payload)
        with m.FSM():
            with m.State('IDLE'):
                m.d.comb += self.num_results.ready.eq(1)
                with m.If(self.num_results.is_transferring()):
                    m.d.sync += results_counter.eq(self.num_results.payload)
                    m.next = 'ACCUMULATING'
            with m.State('ACCUMULATING'):
                m.d.comb += self.results.ready.eq(1)
                with m.If(self.results.is_transferring()):
                    m.d.sync += accumulator.eq(accumulator +
                                               self.results.payload)
                    with m.If(results_counter > 1):
                        m.d.sync += results_counter.eq(results_counter - 1)
                    with m.Else():
                        m.d.sync += results_counter.eq(0)
                        m.next = 'DONE'
            with m.State('DONE'):
                m.d.sync += self.accumulated.payload.eq(accumulator)
                m.d.sync += self.accumulated.valid.eq(1)
                m.d.sync += accumulator.eq(0)
                with m.If(self.accumulated.is_transferring()):
                    m.d.sync += self.accumulated.valid.eq(0)
                    m.next = 'IDLE'


class HpsCfu(Cfu):

    def __init__(self, filter_store_depth=Constants.MAX_FILTER_WORDS):
        super().__init__()
        self.filter_store_depth = filter_store_depth

    def connect_verify_register(self, m, set, get):
        set_stream = set.output_streams[Constants.REG_VERIFY]
        get_stream = get.input_streams[Constants.REG_VERIFY]
        m.submodules["add_one"] = add_one = AddOneActor()
        m.d.comb += connect(set_stream, add_one.input)
        m.d.comb += connect(add_one.output, get_stream)

    def connect_macc(self, m, set, input_store, filter_store, macc):
        m.d.comb += macc.offset.eq(set.values[Constants.REG_INPUT_OFFSET])

        # Connect the input store to a FlowRestrictor, which will let through
        # N values at a time when signalled.
        input_flow_restrictor = FlowRestrictor(128)
        m.submodules['input_flow_restrictor'] = input_flow_restrictor
        m.d.comb += connect(input_store.data_output,
                            input_flow_restrictor.input)
        next = set.output_streams[Constants.REG_FILTER_INPUT_NEXT]
        m.d.comb += input_flow_restrictor.release.payload.eq(next.payload)
        m.d.comb += input_flow_restrictor.release.valid.eq(next.valid)
        # TODO(dcallagh): can we connect this properly somehow?
        m.d.comb += next.ready.eq(1)

        # Same for the filter store.
        filter_flow_restrictor = FlowRestrictor(128)
        m.submodules['filter_flow_restrictor'] = filter_flow_restrictor
        m.d.comb += connect(filter_store.data_output,
                            filter_flow_restrictor.input)
        next = set.output_streams[Constants.REG_FILTER_INPUT_NEXT]
        m.d.comb += filter_flow_restrictor.release.payload.eq(next.payload)
        m.d.comb += filter_flow_restrictor.release.valid.eq(next.valid)
        # TODO(dcallagh): can we connect this properly somehow?
        m.d.comb += next.ready.eq(1)

        # Join both streams into a single stream holding all operands.
        # Then connect that to the macc.
        operands_buffer = ConcatenatingBuffer([
            ('inputs', unsigned(128)),
            ('filters', unsigned(128)),
        ])
        m.submodules['operands_buffer'] = operands_buffer
        m.d.comb += [
            connect(input_flow_restrictor.output,
                    operands_buffer.inputs['inputs']),
            connect(filter_flow_restrictor.output,
                    operands_buffer.inputs['filters']),
            connect(operands_buffer.output, macc.operands),
        ]

    def connect_result_accumulator(self, m, set, macc, result_accumulator, get):
        # Connect the macc result stream to the accumulator.
        m.d.comb += connect(macc.result, result_accumulator.results)

        # Signal it to accumulate N results at a time when they are released
        # from the stores.
        next = set.output_streams[Constants.REG_FILTER_INPUT_NEXT]
        m.d.comb += result_accumulator.num_results.payload.eq(next.payload)
        m.d.comb += result_accumulator.num_results.valid.eq(next.valid)

        # Send the accumulator results to the output register.
        out_stream = get.input_streams[Constants.REG_MACC_OUT]
        m.d.comb += connect(result_accumulator.accumulated, out_stream)

    def connect_input_store(self, m, set, get, input_store):
        m.d.comb += connect(set.output_streams[Constants.REG_INPUT_NUM_WORDS],
                            input_store.num_words_input)
        m.d.comb += connect(set.output_streams[Constants.REG_SET_INPUT],
                            input_store.data_input)

    def connect_filter_store(self, m, set, get, filter_store):
        m.d.comb += connect(set.output_streams[Constants.REG_FILTER_NUM_WORDS],
                            filter_store.num_words_input)
        m.d.comb += connect(set.output_streams[Constants.REG_SET_FILTER],
                            filter_store.data_input)

    def connect_op_store(self, m, op_store, set):
        m.d.comb += [
            op_store.write_data.bias.eq(set.values[Constants.REG_OUTPUT_BIAS]),
            op_store.write_data.multiplier.eq(
                set.values[Constants.REG_OUTPUT_MULTIPLIER]),
            op_store.write_data.shift.eq(
                -set.values[Constants.REG_OUTPUT_SHIFT]),
        ]
        # write strobe fires one cycle before new value is ready to be
        # read, so we use m.d.sync to delay write_enable by one cycle
        m.d.sync += op_store.write_enable.eq(
            set.write_strobes[Constants.REG_OUTPUT_SHIFT])
        m.d.comb += op_store.reset.eq(
            set.write_strobes[Constants.REG_OUTPUT_PARAMS_RESET])

    def connect_post_process(self, m, pp, get, set, op_store):
        m.d.comb += [
            pp.offset.eq(set.values[Constants.REG_OUTPUT_OFFSET]),
            pp.activation_min.eq(set.values[Constants.REG_OUTPUT_MIN]),
            pp.activation_max.eq(set.values[Constants.REG_OUTPUT_MAX]),
            pp.read_data.eq(op_store.read_data),
            op_store.read_enable.eq(pp.read_enable),
            connect(pp.result, get.input_streams[Constants.REG_OUTPUT_WORD])
        ]

    def elab_instructions(self, m):
        m.submodules['set'] = set = SetInstruction()
        m.submodules['get'] = get = GetInstruction()

        self.connect_verify_register(m, set, get)

        m.submodules['input_store'] = input_store = InputStore()
        self.connect_input_store(m, set, get, input_store)

        filter_store = FilterStore(depth=self.filter_store_depth)
        m.submodules['filter_store'] = filter_store
        self.connect_filter_store(m, set, get, filter_store)

        m.submodules['macc'] = macc = MultiplyAccumulate(16)
        m.d.comb += macc.enable.eq(1)
        self.connect_macc(m, set, input_store, filter_store, macc)

        result_accumulator = ResultAccumulator()
        m.submodules['result_accumulator'] = result_accumulator
        self.connect_result_accumulator(m, set, macc, result_accumulator, get)

        m.submodules['op_store'] = op_store = OutputParamsStorage()
        self.connect_op_store(m, op_store, set)
        m.submodules['pp'] = pp = PostProcessInstruction()
        self.connect_post_process(m, pp, get, set, op_store)

        m.submodules['ping'] = ping = PingInstruction()
        return {
            Constants.INS_GET: get,
            Constants.INS_SET: set,
            Constants.INS_POST_PROCESS: pp,
            Constants.INS_PING: ping,
        }


def make_cfu(**kwargs):
    return HpsCfu(**kwargs)
