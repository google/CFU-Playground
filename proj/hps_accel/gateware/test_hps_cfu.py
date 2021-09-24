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

from random import seed, randint

from nmigen.sim import Settle
from nmigen_cfu import CfuTestBase, InstructionTestBase, pack_vals
from nmigen_cfu.util import TestBase

from .constants import Constants
from .hps_cfu import PingInstruction, ResultAccumulator, make_cfu


class PingInstructionTest(InstructionTestBase):
    def create_dut(self):
        return PingInstruction()

    def test(self):
        # each ping returns the sum of the previous ping's inputs
        self.verify([
            (1, 2, 0),
            (12, 4, 3),
            (0, 0, 16),
        ])


class ResultAccumulatorTest(TestBase):

    def create_dut(self):
        return ResultAccumulator()

    def test_it(self):
        def process():
            # After reset, the accumulator does not accept new results.
            for _ in range(10):
                self.assertEqual((yield self.dut.results.ready), 0)
                self.assertEqual((yield self.dut.accumulated.valid), 0)
                self.assertEqual((yield self.dut.num_results.ready), 1)
                yield
            # Tell it to accumulate 5 results.
            yield self.dut.num_results.payload.eq(5)
            yield self.dut.num_results.valid.eq(1)
            yield
            yield Settle()
            yield self.dut.num_results.valid.eq(0)
            self.assertEqual((yield self.dut.num_results.ready), 0)
            results = [11, 12, 13, 14, 15]
            for result in results:
                self.assertEqual((yield self.dut.results.ready), 1)
                yield self.dut.results.payload.eq(result)
                yield self.dut.results.valid.eq(1)
                yield
            yield self.dut.results.valid.eq(0)
            yield Settle()
            # After the fifth result, it should not accept any more.
            self.assertEqual((yield self.dut.results.ready), 0)
            # The accumulated value should be sent out after 2 cycles delay.
            yield self.dut.accumulated.ready.eq(1)
            yield
            yield
            self.assertEqual((yield self.dut.accumulated.valid), 1)
            expected = sum(results)
            self.assertEqual((yield self.dut.accumulated.payload), expected)
            # It should be ready to be told to accumulate more results
            # after 1 more cycle delay.
            yield
            self.assertEqual((yield self.dut.num_results.ready), 1)
        self.run_sim(process)


GET = Constants.INS_GET
SET = Constants.INS_SET
PP = Constants.INS_POST_PROCESS
PING = Constants.INS_PING
VERIFY = Constants.REG_VERIFY


class HpsCfuTest(CfuTestBase):
    """Tests the whole CFU"""

    def create_dut(self):
        return make_cfu(filter_store_depth=100)

    def test_simple(self):
        """Tests some simple cases"""
        DATA = [
            # verify that can use ping
            ((PING, 0, 1, 2), 0),
            ((PING, 0, 0, 0), 3),
            # test verify register
            ((SET, VERIFY, 0, 0), 0),
            ((GET, VERIFY, 0, 0), 1),
            ((SET, VERIFY, 10, 0), 0),
            ((GET, VERIFY, 0, 0), 11),
            ((GET, VERIFY, 0, 0), 11),
            ((PING, 0, 0, 0), 0),
            ((GET, VERIFY, 0, 0), 11),
        ]
        self.run_ops(DATA)

    def prepare_macc(self, offset, input, filter):
        # Fill input store
        yield ((SET, Constants.REG_INPUT_NUM_WORDS, len(input) // 4, 0), 0)
        for i in range(0, len(input), 4):
            packed = pack_vals(*input[i:i + 4])
            yield ((SET, Constants.REG_SET_INPUT, packed, 0), 0)

        # Fill filter store
        yield ((SET, Constants.REG_FILTER_NUM_WORDS, len(filter) // 4, 0), 0)
        for i in range(0, len(filter), 4):
            packed = pack_vals(*filter[i:i + 4])
            yield ((SET, Constants.REG_SET_FILTER, packed, 0), 0)

        # Set input offset
        yield ((SET, Constants.REG_INPUT_OFFSET, offset, 0), 0)

    def check_macc(self, offset, input, filter):
        yield ((SET, Constants.REG_FILTER_INPUT_NEXT, len(input) // 16, 0), 0)
        expected = sum((offset + i) * f for (i, f) in zip(input, filter))
        yield ((GET, Constants.REG_MACC_OUT, 0, 0), expected)

    def test_multiply_accumulate_one_iteration(self):
        def op_generator():
            yield from self.prepare_macc(12, range(16), range(16))
            yield from self.check_macc(12, range(16), range(16))
        self.run_ops(op_generator(), False)

    def test_multiply_accumulate(self):
        """Tests Multiply-Accumulate functionality"""
        def op_generator():
            seed(1234)
            offset = randint(-128, 127)
            input = [randint(-128, 127) for _ in range(160)]
            filter = [randint(-128, 127) for _ in range(160)]
            yield from self.prepare_macc(offset, input, filter)
            yield from self.check_macc(offset, input, filter)
        self.run_ops(op_generator())

    def test_multiply_accumulate_with_store_reset(self):
        def op_generator():
            seed(4321)
            offset = randint(-128, 127)
            # Let it run through the stores once first
            input = [randint(-128, 127) for _ in range(160)]
            filter = [randint(-128, 127) for _ in range(160)]
            yield from self.prepare_macc(offset, input, filter)
            yield from self.check_macc(offset, input, filter)
            # Reset the input store with new values, leave the filter store
            input = [randint(-128, 127) for _ in range(160)]
            yield ((SET, Constants.REG_INPUT_NUM_WORDS, len(input) // 4, 0), 0)
            for i in range(0, len(input), 4):
                packed = pack_vals(*input[i:i + 4])
                yield ((SET, Constants.REG_SET_INPUT, packed, 0), 0)
            # Let it run through once more with new input values
            yield from self.check_macc(offset, input, filter)
        self.run_ops(op_generator())

    def set_output_params_store(self, params):
        for bias, multiplier, shift in params:
            yield ((SET, Constants.REG_OUTPUT_BIAS, bias, 0), 0)
            yield ((SET,
                    Constants.REG_OUTPUT_MULTIPLIER, multiplier, 0), 0)
            yield ((SET, Constants.REG_OUTPUT_SHIFT, shift, 0), 0)

    def check_post_process(self, inputs, expected_outputs):
        for input_ in inputs:
            yield((PP, Constants.PP_POST_PROCESS, input_, 0), 0)
        for expected in expected_outputs:
            yield ((GET, Constants.REG_OUTPUT_WORD, 0, 0), expected)

    def test_PP_POST_PROCESS(self):
        """Tests PP post process function"""
        def op_generator():
            # Set offset and activation min/max
            yield ((SET, Constants.REG_OUTPUT_OFFSET, -128, 0), 0)
            yield ((SET, Constants.REG_OUTPUT_MIN, -128, 0), 0)
            yield ((SET, Constants.REG_OUTPUT_MAX, 127, 0), 0)

            # Set Bias, Multipliers and shifts into store
            yield from self.set_output_params_store([
                (2598, 1170510491, -8),
                (2193, 2082838296, -9),
                (-18945, 1368877765, -9),
                (1851, 1661334583, -8),
            ])

            # Check some input and output values - should use all params twice
            yield from self.check_post_process(
                [-15150, -432, 37233, -294,
                 -14403, 95, 37889, -566],
                [pack_vals(-128, -125, -105, -123),
                 pack_vals(-128, -124, -104, -124)])

            # Reset store and do this again
            yield ((SET, Constants.REG_OUTPUT_PARAMS_RESET, 0, 0), 0)
            yield from self.set_output_params_store([
                (1994, 1384690194, -8),
                (1467, 1177612918, -8),
                (1198, 1352351843, -8),
                (-3353, 1708212360, -9),
            ])
            yield from self.check_post_process([
                3908, 153, 2981, -9758,
                3721, -145, 2912, -9791, ],
                [pack_vals(-113, -125, -118, -128),
                 pack_vals(-114, -125, -118, -128)])

        self.run_ops(op_generator(), False)
