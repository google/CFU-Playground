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

from litex_boards.targets.digilent_arty import BaseSoC

from litex.build.generic_platform import *
from litex.build.sim.config import SimConfig

from litex.soc.integration.common import get_mem_data
from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import soc_core_args, soc_core_argdict
from litex.soc.integration.soc import SoCRegion

from litex.tools.litex_sim import SimSoC

from patch_cpu_variant import patch_cpu_variant, copy_cpu_variant_if_needed
from patch_cpu_variant import build_cpu_variant_if_needed

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
    patch_cpu_variant()
    parser = argparse.ArgumentParser(description="LiteX SoC on Arty A7")
    builder_args(parser)
    soc_core_args(parser)
    parser.add_argument("--sim-trace",  action="store_true", help="Whether to enable tracing of simulation")
    parser.add_argument("--sim-trace-start", default=0, help="Start tracing at this time in picoseconds")
    parser.add_argument("--sim-trace-end", default=-1, help="Stop tracing at this time in picoseconds")
    parser.add_argument("--run", action="store_true", help="Whether to run the simulation")
    parser.add_argument("--separate-arena", action="store_true", help="Add arena mem region at 0x60000000")
    parser.add_argument("--cfu-mport", action="store_true", help="Add ports between arena and CFU " \
                        "(implies --separate-arena)")
    parser.add_argument("--bin", help="RISCV binary to run. Required if --run is set.")
    parser.set_defaults(
            csr_csv='csr.csv',
            uart_name='serial',
            uart_baudrate=921600,
            cpu_variant='full+cfu+debug',
            with_etherbone=False)
    args = parser.parse_args()
    bin = None
    if args.run:
        if args.bin:
            bin = get_mem_data(args.bin, "little")
        else:
            print("must provide --bin if using --run")
    
    # cfu_mport implies separate_arena
    if args.cfu_mport:
        args.separate_arena = True

    build_cpu_variant_if_needed(args.cpu_variant)
    copy_cpu_variant_if_needed(args.cpu_variant)
    soc_kwargs = soc_core_argdict(args)
    soc_kwargs["l2_size"] = 8 * 1024
    soc_kwargs["uart_name"] = "sim"
    soc = SimSoC(
        integrated_main_ram_size = 32 * 1024 * 1024, 
        integrated_main_ram_init=bin, 
        sim_debug = True,
        **soc_kwargs)

    if args.separate_arena:
        soc.add_config('SOC_SEPARATE_ARENA')
        soc.add_ram("arena",
            origin = 0x60000000,
            size   = 256 * 1024,
        )
    else:
        # size-zero .arena region (linker script needs it)
        region = SoCRegion(0x60000000, 0, cached=True, linker=True)
        soc.bus.add_region("arena", region)


    if args.cfu_mport:
        #
        # add 4 read-only ports with LSBs fixed to 00, 01, 10, and 11.
        #   and connect them to the CFU
        #
        newport = []
        for i in range(4):
            newport.append(soc.arena.mem.get_port())
            soc.specials += newport[i]

            p_adr_from_cfu = Signal(14)
            p_adr = Cat(Constant(i,2), p_adr_from_cfu)
            p_dat_r = Signal(32)
            soc.comb += [
                p_dat_r.eq(newport[i].dat_r),
                newport[i].adr.eq(p_adr),
            ]

            soc.cpu.cfu_params.update(**{ f"o_port{i}_addr" : p_adr_from_cfu})
            soc.cpu.cfu_params.update(**{ f"i_port{i}_din"  : p_dat_r})

    sim_config = SimConfig()
    sim_config.add_clocker("sys_clk", freq_hz=soc.clk_freq)
    sim_config.add_module("serial2console", "serial")
    soc.add_constant("ROM_BOOT_ADDRESS", 0x40000000)

    builder = Builder(soc, **builder_argdict(args))

    # configure_sim_builder(builder, args.sim_rom_bin)
    builder.build(
        build=args.run,
        run=args.run,
        sim_config=sim_config,
        interactive=False,
        trace=args.sim_trace,
        trace_fst=True,
        trace_start=int(float(args.sim_trace_start)),
        trace_end=int(float(args.sim_trace_end)))


if __name__ == "__main__":
    main()
