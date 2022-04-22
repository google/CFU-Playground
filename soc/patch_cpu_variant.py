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

from litex import get_data_mod
from litex.soc.cores.cpu.vexriscv import core
from shutil import copyfile

import os


def patch_cpu_variant():
    """Monkey patches custom variants into LiteX."""
    core.CPU_VARIANTS.update({
        'custom':               'VexRiscv_Custom',
        'custom+cfu':           'VexRiscv_CustomCfu',
        'dbpl8+cfu':            'VexRiscv_dbpl8Cfu',
        'minimal+cfu':          'VexRiscv_MinCfu',
        'slim+cfu':             'VexRiscv_SlimCfu',
        'slimopt+cfu':          'VexRiscv_SlimoptCfu',
        'slim+cfu+debug':       'VexRiscv_SlimCfuDebug',
        'perf+cfu':             'VexRiscv_PerfCfu',
        'perf+cfu+debug':       'VexRiscv_PerfCfuDebug',
        'slimperf+cfu':         'VexRiscv_SlimPerfCfu',
        'slimperf+cfu+debug':   'VexRiscv_SlimPerfCfuDebug',
    })
    core.GCC_FLAGS.update({
        'custom':               '-march=rv32im -mabi=ilp32',
        'custom+cfu':           '-march=rv32im -mabi=ilp32',
        'dbpl8+cfu':            '-march=rv32im -mabi=ilp32',
        'minimal+cfu':          '-march=rv32i  -mabi=ilp32',
        'slimopt+cfu':          '-march=rv32im -mabi=ilp32',
        'slim+cfu':             '-march=rv32im -mabi=ilp32',
        'slim+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'perf+cfu':             '-march=rv32im -mabi=ilp32',
        'perf+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'slimperf+cfu':         '-march=rv32im -mabi=ilp32',
        'slimperf+cfu+debug':   '-march=rv32im -mabi=ilp32',
    })

    ########### ADD code to existing add_soc_components() #######
    old_add_soc_components = core.VexRiscv.add_soc_components

    def new_add_soc_components(self, soc, soc_region_cls):
        old_add_soc_components(self, soc, soc_region_cls)
        if 'perf' in self.variant:
            soc.add_config('CPU_PERF_CSRS', 8)

    core.VexRiscv.add_soc_components = new_add_soc_components



################################################################
# This copies a CPU variant on demand 
#  from the soc/vexriscv/ directory
#  to the pythondata_cpu_vexriscv verilog/ directory
#  where the LiteX build expects to find it.
################################################################
def copy_cpu_variant_if_needed(variant):
    if variant in core.CPU_VARIANTS:
        cpu_filename = core.CPU_VARIANTS[variant] + ".v"
        vdir = get_data_mod("cpu", "vexriscv").data_location
        fullpath = os.path.join(vdir, cpu_filename)

        cfu_root = os.environ.get('CFU_ROOT')
        custom_dir = os.path.join(cfu_root, "soc", "vexriscv")
        custom_cpu = os.path.join(custom_dir, cpu_filename)

        # always copy to ensure the most up-to-date version is used
        if os.path.exists(custom_cpu):
            print(f"Found and copied \"{custom_cpu}\".")
            copyfile(custom_cpu, fullpath)
        else:
            if not os.path.exists(fullpath):
                print(f"Couldn't find \"{fullpath}\".")
                print(f"Couldn't find \"{custom_cpu}\".")
    else:
        print(f"Variant \"{variant}\" not known.")
