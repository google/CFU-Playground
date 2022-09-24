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
from litex.soc.cores.cpu.vexriscv import core as vexriscv_core
from litex.soc.cores.cpu.serv     import core as serv_core
from shutil import copyfile

import os


def patch_cpu_variant():
    """Monkey patches custom variants into LiteX."""
    vexriscv_core.CPU_VARIANTS.update({
        'fomu':                 'VexRiscv_Fomu',
        'fomu+cfu':             'VexRiscv_FomuCfu',
        'breaker':              'VexRiscv_Breaker',
        'breaker+cfu':          'VexRiscv_BreakerCfu',
        'custom':               'VexRiscv_Custom',
        'custom+cfu':           'VexRiscv_CustomCfu',
        'fpu':                  'VexRiscv_Fpu',
        'fpu+cfu':              'VexRiscv_FpuCfu',
        'hps+cfu':              'VexRiscv_HpsCfu',
        'hpsdelta+cfu':         'VexRiscv_HpsdeltaCfu',
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
    vexriscv_core.GCC_FLAGS.update({
        'fomu':                 '-march=rv32im -mabi=ilp32 -mno-div',
        'fomu+cfu':             '-march=rv32im -mabi=ilp32 -mno-div',
        'breaker':              '-march=rv32im -mabi=ilp32 -mno-div',
        'breaker+cfu':          '-march=rv32im -mabi=ilp32 -mno-div',
        'custom':               '-march=rv32im -mabi=ilp32',
        'custom+cfu':           '-march=rv32im -mabi=ilp32',
        'fpu':                  '-march=rv32imf -mabi=ilp32',
        'fpu+cfu':              '-march=rv32imf -mabi=ilp32',
        'hps+cfu':              '-march=rv32im -mabi=ilp32',
        'hpsdelta+cfu':         '-march=rv32im -mabi=ilp32',
        'dbpl8+cfu':            '-march=rv32im -mabi=ilp32',
        'minimal+cfu':          '-march=rv32i  -mabi=ilp32',
        'slimopt+cfu':          '-march=rv32im -mabi=ilp32',
        'slim+cfu':             '-march=rv32im -mabi=ilp32',
        'slim+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'perf+cfu':             '-march=rv32im -mabi=ilp32',
        'perf+cfu+debug':       '-march=rv32im -mabi=ilp32',
        'slimperf+cfu':         '-march=rv32im -mabi=ilp32',
        'slimperf+cfu+debug':   '-march=rv32im -mabi=ilp32',

        # FIXME
        # This is a workaround for PR #619; vexriscv has changed to
        #   '-march=rv32i2p0_m', and this undoes that for these variants.
        #   If we don't have this workaround, we get a link error.
        'full+cfu':             '-march=rv32im -mabi=ilp32',
        'full+cfu+debug':       '-march=rv32im -mabi=ilp32',
    })

    ########### ADD code to existing add_soc_components() #######
    old_add_soc_components = vexriscv_core.VexRiscv.add_soc_components

    def new_add_soc_components(self, soc, soc_region_cls):
        old_add_soc_components(self, soc, soc_region_cls)

        if 'perf' in self.variant:
            soc.add_config('CPU_PERF_CSRS', 8)

        if ('fomu' in self.variant) or ('breaker' in self.variant):
            soc.add_config('CPU_DIV_UNIMPLEMENTED')

            # Fomu variant has *no* Dcache.
            # This is here to avoid the dcache flush instruction (system.h).
            soc.constants.pop('CONFIG_CPU_HAS_DCACHE', None)

    vexriscv_core.VexRiscv.add_soc_components = new_add_soc_components



################################################################
# This copies a CPU variant on demand 
#  from the soc/vexriscv/ directory
#  to the pythondata_cpu_vexriscv verilog/ directory
#  where the LiteX build expects to find it.
################################################################
def copy_cpu_variant_if_needed(variant):
    if variant in vexriscv_core.CPU_VARIANTS:
        cpu_filename = vexriscv_core.CPU_VARIANTS[variant] + ".v"
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


################################################################
# This builds a CPU variant on demand 
################################################################
def build_cpu_variant_if_needed(variant):
    if variant in vexriscv_core.CPU_VARIANTS or variant in serv_core.CPU_VARIANTS:
        print(f"Variant \"{variant}\" already known.")
        return

    ########### ADD code to existing add_soc_components() #######
    old_add_soc_components = vexriscv_core.VexRiscv.add_soc_components

    def new_add_soc_components(self, soc, soc_region_cls):
        old_add_soc_components(self, soc, soc_region_cls)

        if 'dCacheSize:0' in self.variant:
            # variant has *no* Dcache.
            # This is here to avoid the dcache flush instruction (system.h).
            soc.constants.pop('CONFIG_CPU_HAS_DCACHE', None)
        if 'iCacheSize:0' in self.variant:
            # variant has *no* Icache.
            # This is here to avoid the dcache flush instruction (system.h).
            soc.constants.pop('CONFIG_CPU_HAS_ICACHE', None)

    vexriscv_core.VexRiscv.add_soc_components = new_add_soc_components

    cpu_params = {
        "csrPluginConfig":    "mcycle",
        "bypass":             "true",
        "cfu":                "false",
        "dCacheSize":         "4096",  
        "hardwareDiv":        "false",
        "iCacheSize":         "4096", 
        "mulDiv":             "true", 
        "prediction":         "none", 
        "safe":               "true", 
        "singleCycleShift":   "true", 
        "singleCycleMulDiv":  "true" 
    }

    # Parse variant into param list w/o 'generate' keyword
    params = variant.split("+")
    if params[0] != "generate":
        print("ERROR: Need generate keyword to begin on demand Vexriscv build.")
        exit()
        
    params = params[1:]
    for param in params:
        if "cfu" in param:
            cpu_params[param] = "true"
        else:
            param_name, val = param.split(":")
            # Modify deafult params with user defined val
            if param_name not in cpu_params.keys():
                raise ValueError(param_name + " parameter not recognized.")
            cpu_params[param_name] = val

    gen_args = []
    cpu_filename_base = "VexRiscv"
    for param_name, val in sorted(cpu_params.items()):
        gen_args.append(f"--{param_name}={val}")
        cpu_filename_base = cpu_filename_base + "_" +  param_name + "-" + val

    gen_args.append(f"--outputFile={cpu_filename_base}")
    cpu_filename = cpu_filename_base + ".v"

    cfu_root = os.environ.get('CFU_ROOT')
    custom_dir = os.path.join(cfu_root, "soc", "vexriscv")
    custom_cpu = os.path.join(custom_dir, cpu_filename)
    print("CUSTOM CPU: " + custom_cpu)
    vdir = get_data_mod("cpu", "vexriscv").data_location
    print("VDIR: " + vdir)
    fullpath = os.path.join(vdir, cpu_filename)
    print("FULL PATH: " + fullpath)

    if os.path.exists(custom_cpu):
        print(f"Variant \"{variant}\" already known.")
    else:
        #
        # build it if needed!
        # build it if needed!
        #
        print(f"Generating variant \"{variant}\" in file \"{cpu_filename}\".")
        if not os.path.exists(custom_cpu):
            cmd = 'cd {path} && sbt compile "runMain vexriscv.GenCoreDefault {args}"'.format(path=custom_dir, args=" ".join(gen_args))
            if os.system(cmd) != 0:
                raise OSError('Failed to run sbt')

    #
    # do some patching
    #
    arch  = "rv32im"
    abi   = "ilp32"
    hwDiv = ""
    if cpu_params["mulDiv"] == "false":
        arch  = "rv32i"
        hwDiv = "  -mno-div"
    else: 
        if cpu_params["hardwareDiv"] == "false":
            hwDiv = "  -mno-div"
        
    gcc_flags = f"-march={arch} -mabi={abi} {hwDiv}"



    vexriscv_core.CPU_VARIANTS.update({
        variant:             cpu_filename_base,
    })
    vexriscv_core.GCC_FLAGS.update({
        variant:             gcc_flags,
    })

    #
    # Copy file to where it goes
    #
    copyfile(custom_cpu, fullpath) 
