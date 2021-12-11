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

from nmigen_cfu import CfuBase

class Cfu(CfuBase):
    """Gen2 accelerator CFU.
    
    Assumes working with a slimopt+cfu VexRiscV, which rsp_ready is always true.
    """
    def elab(self, m):
        m.d.comb += [
            self.cmd_ready.eq(1),
        ]

        # Assumes response always ready
        # Assumes extra delay in pipeline to allow for this
        m.d.sync += [
            self.rsp_out.eq(self.cmd_in0 + 1),
        ]

def make_cfu():
    return Cfu()