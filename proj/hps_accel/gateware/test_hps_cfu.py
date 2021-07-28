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

from nmigen_cfu import CfuTestBase, InstructionTestBase
from util import pack_vals

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
PING = Constants.INS_PING
VERIFY = Constants.REG_VERIFY


class BasicTest(CfuTestBase):
    """Tests some simple cases"""

    def create_dut(self):
        return make_cfu()

    def test(self):
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


class MultiplyAccumulateTest(CfuTestBase):
    """Tests Multiply-Accumulate functionality"""

    def create_dut(self):
        return make_cfu()

    def check(self, offset, input, filter):
        expected = sum((offset + i) * f for (i, f) in zip(input, filter))
        P = pack_vals
        return [
            ((SET, Constants.REG_INPUT_OFFSET, offset, 0), 0),
            ((SET, Constants.REG_MACC_INPUT_0, P(*input[0:4]), 0), 0),
            ((SET, Constants.REG_MACC_INPUT_1, P(*input[4:8]), 0), 0),
            ((SET, Constants.REG_MACC_INPUT_2, P(*input[8:12]), 0), 0),
            ((SET, Constants.REG_MACC_INPUT_3, P(*input[12:16]), 0), 0),
            ((SET, Constants.REG_MACC_FILTER_0, P(*filter[0:4]), 0), 0),
            ((SET, Constants.REG_MACC_FILTER_1, P(*filter[4:8]), 0), 0),
            ((SET, Constants.REG_MACC_FILTER_2, P(*filter[8:12]), 0), 0),
            ((SET, Constants.REG_MACC_FILTER_3, P(*filter[12:16]), 0), 0),
            ((PING, 0, 0, 0), 0),  # wait 2 cycles for result
            ((PING, 0, 0, 0), 0),
            ((GET, Constants.REG_MACC_OUT, 0, 0), expected),
        ]

    def test(self):
        def op_generator():
            yield from self.check(0, [0] * 16, [0] * 16)
            yield from self.check(12, range(16), range(16))
            seed(1234)
            for _ in range(10):
                yield from self.check(randint(-128, 128),
                                      [randint(-128, 127) for _ in range(16)],
                                      [randint(-128, 127) for _ in range(16)])
        self.run_ops(op_generator())
