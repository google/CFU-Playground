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

from .hps_cfu import PingInstruction, make_cfu
from .constants import Constants

from nmigen_cfu import CfuTestBase, InstructionTestBase


class PingInstructionTest(InstructionTestBase):
    def create_dut(self):
        return PingInstruction()

    def test(self):
        self.verify([
            (1, 2, 0),
            (12, 4, 3),
            (0, 0, 16),
        ])


class HpsCfuTest(CfuTestBase):
    def create_dut(self):
        return make_cfu()

    def test(self):
        PING = Constants.INS_PING
        DATA = [
            # verify that can use ping
            ((PING, 1, 2), 0),
            ((PING, 0, 0), 3),
        ]
        return self.run_ops(DATA)
