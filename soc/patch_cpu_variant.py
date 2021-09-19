#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Disable pylint's E1101, which breaks completely on migen
# pylint:disable=E1101

from litex.soc.cores.cpu.vexriscv import core


def patch_cpu_variant():
    """Monkey patches custom variants into LiteX."""
    core.CPU_VARIANTS.update({
        'slim+cfu':             'VexRiscv_SlimCfu',
        'slim+cfu+debug':       'VexRiscv_SlimCfuDebug',
        'perf+cfu':             'VexRiscv_PerfCfu',
        'perf+cfu+debug':       'VexRiscv_PerfCfuDebug',
        'slimperf+cfu':         'VexRiscv_SlimPerfCfu',
        'slimperf+cfu+debug':   'VexRiscv_SlimPerfCfuDebug',
    })
    core.GCC_FLAGS.update({
        'slim+cfu':             '-march=rv32im -mabi=ilp32',
        'slim+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'perf+cfu':             '-march=rv32im -mabi=ilp32',
        'perf+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'slimperf+cfu':         '-march=rv32im -mabi=ilp32',
        'slimperf+cfu+debug':   '-march=rv32im -mabi=ilp32',
    })
    print("general patch:\n", core.CPU_VARIANTS)

    ########### ADD code to existing add_soc_components() #######
    old_add_soc_components = core.VexRiscv.add_soc_components

    def new_add_soc_components(self, soc, soc_region_cls):
        old_add_soc_components(self, soc, soc_region_cls)
        if 'perf' in self.variant:
            soc.add_config('CPU_PERF_CSRS', 8)

    core.VexRiscv.add_soc_components = new_add_soc_components
