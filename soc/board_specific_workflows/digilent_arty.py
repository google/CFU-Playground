#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
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

import general
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder
from litex.build.xilinx import vivado


class DigilentArtySoCWorkflow(general.GeneralSoCWorkflow):
    """Specializes the general workflow for the Digilent Arty."""
    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """Runs the general make_soc with a l2_size parameter,"""
        """   and jtagbone disabled.                          """
        return super().make_soc(l2_size=8 * 1024, with_jtagbone = False, **kwargs)

    def build_soc(self, soc: litex_soc.LiteXSoC, **kwargs) -> builder.Builder:
        """Specializes build_soc to add Vivado args if needed."""
        if isinstance(soc.platform.toolchain, vivado.XilinxVivadoToolchain):
            kwargs.update(vivado.vivado_build_argdict(self.args))
        return super().build_soc(soc, **kwargs)
