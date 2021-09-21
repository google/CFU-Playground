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

from nmigen_cfu import CfuTestBase, InstructionTestBase, pack_vals

from .constants import Constants
from .hps_cfu import PingInstruction, make_cfu


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
        for i in range(0, len(input), 16):
            # Turn the crank
            yield ((SET, Constants.REG_FILTER_INPUT_NEXT, 1, 0), 0)
            expected = sum((offset + i) * f for (i, f) in
                           zip(input[i:i + 16], filter[i:i + 16]))
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

    def test_simple_input_store(self):
        """Tests simple input use case"""
        def op_generator():
            yield ((SET, Constants.REG_INPUT_NUM_WORDS, 20, 0), 0)
            for n in range(100, 120):
                yield ((SET, Constants.REG_SET_INPUT, n, 0), 0)
            for n in range(100, 120, 4):
                yield ((SET, Constants.REG_FILTER_INPUT_NEXT, 1, 0), 0)
                yield ((PING, 0, 0, 0), 0)  # wait for regs to update
                yield ((GET, Constants.REG_INPUT_0, 0, 0), n + 0)
                yield ((GET, Constants.REG_INPUT_1, 0, 0), n + 1)
                yield ((GET, Constants.REG_INPUT_2, 0, 0), n + 2)
                yield ((GET, Constants.REG_INPUT_3, 0, 0), n + 3)

        self.run_ops(op_generator(), False)

    def test_simple_filter_store(self):
        """Tests simple filter store use case"""
        def op_generator():
            yield ((SET, Constants.REG_FILTER_NUM_WORDS, 20, 0), 0)
            for n in range(100, 120):
                yield ((SET, Constants.REG_SET_FILTER, n, 0), 0)
            for n in range(100, 120, 4):
                yield ((SET, Constants.REG_FILTER_INPUT_NEXT, 1, 0), 0)
                yield ((PING, 0, 0, 0), 0)  # wait for regs to update
                yield ((GET, Constants.REG_FILTER_0, 0, 0), n + 0)
                yield ((GET, Constants.REG_FILTER_1, 0, 0), n + 1)
                yield ((GET, Constants.REG_FILTER_2, 0, 0), n + 2)
                yield ((GET, Constants.REG_FILTER_3, 0, 0), n + 3)
        self.run_ops(op_generator(), False)

    def test_PP_SRDHM(self):
        """Tests PP srdhm function"""
        def op_generator():
            yield ((PP, Constants.PP_SRDHM, -111628, 1342177280), -69767)
            yield ((PP, Constants.PP_SRDHM, -96429, 1975242245), -88695)
            yield ((PP, Constants.PP_SRDHM, 87873, 1815044516), 74270)
        self.run_ops(op_generator(), False)

    def test_PP_RDBPOT(self):
        """Tests PP rdbpot function"""
        def op_generator():
            yield ((PP, Constants.PP_RDBPOT, -1714553096, -7), -13394946)
            yield ((PP, Constants.PP_RDBPOT, -327118692, -3), -40889837)
            yield ((PP, Constants.PP_RDBPOT, 584167932, -6), 9127624)
        self.run_ops(op_generator(), False)

    def set_output_params_store(self, params):
        for bias, multiplier, shift in params:
            yield ((SET, Constants.REG_OUTPUT_BIAS, bias, 0), 0)
            yield ((SET,
                    Constants.REG_OUTPUT_MULTIPLIER, multiplier, 0), 0)
            yield ((SET, Constants.REG_OUTPUT_SHIFT, shift, 0), 0)

    def check_post_process(self, data):
        for inp, expected in data:
            yield((PP, Constants.PP_POST_PROCESS, inp, 0), expected)

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
            yield from self.check_post_process([
                (-15150, -128),
                (-432, -125),
                (37233, -105),
                (-294, -123),
                (-14403, -128),
                (95, -124),
                (37889, -104),
                (-566, -124),
            ])

            # Reset store and do this again
            yield ((SET, Constants.REG_OUTPUT_PARAMS_RESET, 0, 0), 0)
            yield from self.set_output_params_store([
                (1994, 1384690194, -8),
                (1467, 1177612918, -8),
                (1198, 1352351843, -8),
                (-3353, 1708212360, -9),
            ])
            yield from self.check_post_process([
                (3908, -113),
                (153, -125),
                (2981, -118),
                (-9758, -128),
                (3721, -114),
                (-145, -125),
                (2912, -118),
                (-9791, -128),
            ])

        self.run_ops(op_generator(), False)
