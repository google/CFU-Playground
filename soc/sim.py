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
#pylint:disable=E1101

from migen import *

from litex_boards.targets.arty import BaseSoC

from litex.build.generic_platform import *
from litex.build.sim.config import SimConfig

from litex.soc.integration.common import get_mem_data
from litex.soc.integration.builder import *
from litex.soc.integration.soc_sdram import *

from litex.tools.litex_sim import SimSoC

import argparse
import os


def configure_sim_builder(builder: Builder, sim_rom_bin):
    required_packages = {"libcompiler_rt", "libbase"}
    # Remove unwanted packages that we don't need. Of most importance to remove
    # is the "bios" package, which is LiteX's BIOS, since we're using our own.
    # builder.software_packages = [
    #     (name, dir) for (name, dir) in builder.software_packages if name in required_packages ]
    # bios_dir = f"{builder.output_dir}/software/bios"
    # os.makedirs(bios_dir, exist_ok=True)
    # with open(f"{bios_dir}/Makefile", "w") as f:
    #     f.write(f"all:\n\tcp {sim_rom_bin} bios.bin")
    # # "bios" gets loaded automatically by the builder.
    # builder.add_software_package("bios", bios_dir)


def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Arty A7")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--cfu", required=True, help="Specify file containing CFU Verilog module")
    parser.add_argument("--sim-trace",  action="store_true", help="Whether to enable tracing of simulation")
    parser.add_argument("--sim-trace-start", default=0, help="Start tracing at this time in picoseconds")
    parser.add_argument("--sim-trace-end", default=-1, help="Stop tracing at this time in picoseconds")
    parser.add_argument("--run", action="store_true", help="Whether to run the simulation")
    parser.add_argument("--bin", help="RISCV binary to run. Required if --run is set.")
    parser.set_defaults(
            csr_csv='csr.csv',
            uart_name='serial',
            uart_baudrate=921600,
            cpu_variant='full+debug',    # don't specify 'cfu' here
            with_etherbone=False)
    args = parser.parse_args()
    bin = None
    if args.run:
        if args.bin:
            bin = get_mem_data(args.bin, "little")
        else:
            print("must provide --bin if using --run")
    
    soc_kwargs = soc_sdram_argdict(args)
    soc_kwargs["l2_size"] = 8 * 1024
    soc_kwargs["uart_name"] = "sim"
    soc = SimSoC(
        integrated_main_ram_size = 32 * 1024 * 1024, 
        integrated_main_ram_init=bin, 
        sim_debug = True,
        **soc_kwargs)
    sim_config = SimConfig()
    sim_config.add_clocker("sys_clk", freq_hz=soc.clk_freq)
    sim_config.add_module("serial2console", "serial")
    soc.add_constant("ROM_BOOT_ADDRESS", 0x40000000)

    # get the CFU version, plus the CFU itself and a wrapper 
    # ...since we're using stock litex, it doesn't know about the Cfu variants, so we need to use "external_variant"
    if args.cfu:
        assert 'full' in args.cpu_variant
        var = "FullCfuDebug" if ('debug' in args.cpu_variant) else "FullCfu"
        vexriscv = "../third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv"
        soc.cpu.use_external_variant(f"{vexriscv}/verilog/VexRiscv_{var}.v")
        soc.platform.add_source(args.cfu)
        soc.platform.add_source(f"{vexriscv}/verilog/wrapVexRiscv_{var}.v")

    builder = Builder(soc, **builder_argdict(args))

    # configure_sim_builder(builder, args.sim_rom_bin)
    builder.build(
        build=args.run,
        run=args.run,
        sim_config=sim_config,
        trace=args.sim_trace,
        trace_fst=True,
        trace_start=int(float(args.sim_trace_start)),
        trace_end=int(float(args.sim_trace_end)))


if __name__ == "__main__":
    main()
