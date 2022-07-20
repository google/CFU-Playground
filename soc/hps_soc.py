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

from hps_proto2_platform import Platform
from litex.soc.cores.clock import S7PLL
from litex.soc.integration.common import get_mem_data
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import Builder, builder_args, builder_argdict
from litex.soc.integration.soc import LiteXSoC, SoCRegion
from litex.soc.cores.led import LedChaser

from litex import get_data_mod

from litex.build.lattice.radiant import radiant_build_args, radiant_build_argdict
from litex.build.lattice.oxide import oxide_args, oxide_argdict

from litespi.modules import GD25LQ128D
from litespi.opcodes import SpiNorFlashOpCodes as Codes
from litespi.phy.generic import LiteSPIPHY
from litespi import LiteSPI

from migen import Instance, Record, ClockSignal, ResetSignal, \
                  ClockDomainsRenamer, ClockDomain

from patch import Patch
# from cam_control import CameraControl

from patch_cpu_variant import patch_cpu_variant, copy_cpu_variant_if_needed

import argparse
import os

KB = 1024
MB = 1024 * KB

UART_SPEED = 115200
RAM_SIZE = 320 * KB

SOC_DIR = os.path.dirname(os.path.realpath(__file__))


class HpsSoC(LiteXSoC):
    # Memory layout
    csr_origin = 0xf0000000
    spiflash_region = SoCRegion(0x20000000, 16*MB, cached=True)
    # The start of the SPI Flash contains the FPGA gateware. Our ROM is after
    # that.
    rom_offset = 2*MB
    sram_origin = 0x40000000
    arena_origin = 0x60000000
    vexriscv_region = SoCRegion(origin=0xf00f0000, size=0x100)

    mem_map = {
        "sram": sram_origin,
        "arena": arena_origin,
        "csr":  csr_origin,
    }

    cpu_type = "vexriscv"

    def __init__(self, platform, debug, variant=None,
                 cpu_cfu=None, execute_from_lram=False,
                 separate_arena=False,
                 with_led_chaser=False,
                 integrated_rom_init=[],
                 build_bios=False,
                 cfu_mport=False,
                 dynamic_clock_control=False):
        LiteXSoC.__init__(self,
                          platform=platform,
                          sys_clk_freq=platform.sys_clk_freq,
                          csr_data_width=32)
        if variant == None:
            variant = "full+debug" if debug else "full"

        # Clock, Controller, CPU
        self.submodules.crg = platform.create_crg()
        self.add_controller("ctrl")
        if execute_from_lram:
            reset_address = 0x00000000
        else:
            reset_address = self.spiflash_region.origin + self.rom_offset
        self.add_cpu(self.cpu_type,
                     variant=variant,
                     reset_address=reset_address,
                     cfu=cpu_cfu)

        # RAM
        if separate_arena:
            ram_size = 64*KB
            arena_size = RAM_SIZE - ram_size
        elif execute_from_lram:
            # Leave one LRAM free for ROM
            ram_size = RAM_SIZE - 64*KB
            arena_size = 0
        else:
            ram_size = RAM_SIZE
            arena_size = 0
        self.setup_ram(size=ram_size)
        self.setup_arena(size=arena_size)

        # Dynamic clock control between CPU and CFU
        if dynamic_clock_control:
            # Add dynamic clock control logic
            from clock_control import CfuCpuClockCtrl
            self.submodules.cfu_cpu_clk_ctl = ClockDomainsRenamer("osc")(CfuCpuClockCtrl())
            cfu_cen = self.cfu_cpu_clk_ctl.cfu_cen
            cpu_cen = self.cfu_cpu_clk_ctl.cpu_cen
            ctl_cfu_bus = self.cfu_cpu_clk_ctl.cfu_bus
            cpu_cfu_bus = self.cpu.cfu_bus

            self.comb += [
                # Connect dynamic clock control bus to CPU <-> CFU BUS
                ctl_cfu_bus.rsp.valid.eq(cpu_cfu_bus.rsp.valid),
                ctl_cfu_bus.rsp.ready.eq(cpu_cfu_bus.rsp.ready),
                ctl_cfu_bus.cmd.valid.eq(cpu_cfu_bus.cmd.valid),
                ctl_cfu_bus.cmd.ready.eq(cpu_cfu_bus.cmd.ready),

                # Connect system clock to dynamic clock enable
                self.crg.sys_clk_enable.eq(cpu_cen),
            ]

            # Create separate clock for CFU
            clko = ClockSignal("cfu")
            self.clock_domains.cd_cfu = ClockDomain("cfu")
            self.specials += Instance(
                "DCC",
                i_CLKI=ClockSignal("osc"),
                o_CLKO=clko,
                i_CE=cfu_cen,
            )

            # Connect separate clock to CFU, keep reset from oscillator clock domain
            self.cpu.cfu_params.update(i_clk=clko)
            self.cpu.cfu_params.update(i_reset=ResetSignal("osc"))

            # Connect clock enable signals to RAM and Arena
            self.comb += [self.lram.a_clkens[i].eq(cpu_cen) for i in range(len(self.lram.a_clkens))]
            if separate_arena:
                self.comb += [self.arena.a_clkens[i].eq(cpu_cen) for i in range(len(self.arena.a_clkens))]
                if cfu_mport:
                    self.comb += [self.arena.b_clkens[i].eq(cfu_cen) for i in range(len(self.arena.b_clkens))]
        else:
            # If dynamic clock control is disabled, assert all memory clock enable signals
            self.comb += [self.lram.a_clkens[i].eq(1) for i in range(len(self.lram.a_clkens))]
            if separate_arena:
                self.comb += [self.arena.a_clkens[i].eq(1) for i in range(len(self.arena.a_clkens))]
                if cfu_mport:
                    self.comb += [self.arena.b_clkens[i].eq(1) for i in range(len(self.arena.b_clkens))]

        # Connect CFU directly to Arena LRAM memory
        if cfu_mport:
            self.connect_cfu_to_lram()

        # SPI Flash
        self.setup_litespi_flash()

        # ROM (either part of SPI Flash, or embedded)
        if execute_from_lram:
            self.setup_rom_in_lram()
            if integrated_rom_init:
                assert len(integrated_rom_init) <= 64 * KB / 4
                self.integrated_rom_initialized = True
                self.rom.add_init(integrated_rom_init)
        else:
            self.setup_rom_in_flash()

        # "LEDS" - Just one LED on JTAG port
        if with_led_chaser:
            self.submodules.leds = LedChaser(
                pads=platform.request_all("user_led"),
                sys_clk_freq=platform.sys_clk_freq)
            self.csr.add("leds")

        # UART
        self.add_serial()

        # Wishbone UART and CPU debug - JTAG must be disabled to use serial2
        if debug:
            self.add_uartbone("serial2", baudrate=UART_SPEED)
            self.bus.add_slave(
                "vexriscv_debug", self.cpu.debug_bus, self.vexriscv_region)

        if build_bios:
            # Timer (required for the BIOS build only)
            self.add_timer(name="timer0")
            self.timer0.add_uptime()


    def setup_ram(self, size):
        region = SoCRegion(self.sram_origin, size, cached=True, linker=True)
        self.submodules.lram = ClockDomainsRenamer("osc")(self.platform.create_ram(32, size))
        self.bus.add_slave("sram_lram", self.lram.bus, region)
        self.bus.add_region("sram", region)

    # define the "arena" region even if it's length-zero
    def setup_arena(self, size):
        region = SoCRegion(self.arena_origin, size, cached=True, linker=True)
        self.bus.add_region("arena", region)
        if size > 0:
            self.submodules.arena = ClockDomainsRenamer("osc")(self.platform.create_ram(32, size, dual_port=True))
            self.bus.add_slave("arena_lram", self.arena.bus, region)
            self.add_config('SOC_SEPARATE_ARENA')

    def setup_rom_in_lram(self):
        region = SoCRegion(self.cpu.reset_address, 64 * KB, mode='r',
                           cached=True, linker=True)
        self.submodules.rom = self.platform.create_ram(32, region.size)
        self.bus.add_slave("rom_lram", self.rom.bus, region)
        self.bus.add_region("rom", region)
        self.integrated_rom_initialized = False
        self.integrated_rom_size = region.size

    def setup_litespi_flash(self):
        self.submodules.spiflash_phy = LiteSPIPHY(
            self.platform.request("spiflash4x"),
            GD25LQ128D(Codes.READ_1_1_4),
            default_divisor=0,
            rate='1:2',
            extra_latency=1)
        self.submodules.spiflash_mmap  = LiteSPI(phy=self.spiflash_phy,
            mmap_endianness = self.cpu.endianness)
        self.csr.add("spiflash_mmap")
        self.csr.add("spiflash_phy")
        self.bus.add_slave(name="spiflash", slave=self.spiflash_mmap.bus, region=self.spiflash_region)

    def setup_rom_in_flash(self):
        region = SoCRegion(self.spiflash_region.origin + self.rom_offset,
                           self.spiflash_region.size - self.rom_offset,
                           mode='r', cached=True, linker=True)
        self.bus.add_region("rom", region)
        self.integrated_rom_initialized = False
        self.integrated_rom_size = region.size

    def add_serial(self):
        self.add_uart("uart", baudrate=UART_SPEED)

    def connect_cfu_to_lram(self):
        # create cfu <-> lram bus
        cfu_lram_bus_layout = [
           ("lram0", [("addr", 14), ("din", 32)]),
           ("lram1", [("addr", 14), ("din", 32)]),
           ("lram2", [("addr", 14), ("din", 32)]),
           ("lram3", [("addr", 14), ("din", 32)])]
        cfu_lram_bus = Record(cfu_lram_bus_layout)

        # add extra ports to the cfu pinout
        self.cpu.cfu_params.update(
            o_port0_addr    =    cfu_lram_bus.lram0.addr,
            i_port0_din     =    cfu_lram_bus.lram0.din,
            o_port1_addr    =    cfu_lram_bus.lram1.addr,
            i_port1_din     =    cfu_lram_bus.lram1.din,
            o_port2_addr    =    cfu_lram_bus.lram2.addr,
            i_port2_din     =    cfu_lram_bus.lram2.din,
            o_port3_addr    =    cfu_lram_bus.lram3.addr,
            i_port3_din     =    cfu_lram_bus.lram3.din,
        )

        # connect them to the lram module
        self.comb += [
            self.arena.b_addrs[0].eq(cfu_lram_bus.lram0.addr),
            self.arena.b_addrs[1].eq(cfu_lram_bus.lram1.addr),
            self.arena.b_addrs[2].eq(cfu_lram_bus.lram2.addr),
            self.arena.b_addrs[3].eq(cfu_lram_bus.lram3.addr),

            cfu_lram_bus.lram0.din.eq(self.arena.b_douts[0]),
            cfu_lram_bus.lram1.din.eq(self.arena.b_douts[1]),
            cfu_lram_bus.lram2.din.eq(self.arena.b_douts[2]),
            cfu_lram_bus.lram3.din.eq(self.arena.b_douts[3]),
        ]

    # This method is defined on SoCCore and the builder assumes it exists.
    def initialize_rom(self, data):
        if hasattr(self, 'rom') and not self.integrated_rom_initialized:
            self.rom.add_init(data)

    @property
    def mem_regions(self):
        return self.bus.regions

    def do_finalize(self):
        super().do_finalize()
        # Retro-compatibility for builder
        # TODO: just fix the builder
        for region in self.bus.regions.values():
            region.length = region.size
            region.type = "cached" if region.cached else "io"
            if region.linker:
                region.type += "+linker"
        self.csr_regions = self.csr.regions


def hps_soc_args(parser: argparse.ArgumentParser):
    builder_args(parser)
    radiant_build_args(parser)
    oxide_args(parser)

def create_builder(soc, args):
    builder = Builder(soc, **builder_argdict(args))
    # builder.output_dir = args.output_dir
    # required_packages = {"libcompiler_rt", "libbase"}
    # # Select required packages. Of most importance is to exclude the "bios"
    # # package, which is LiteX's BIOS, since we're using our own.
    # builder.software_packages = [
    #     (name, dir) for (name, dir) in builder.software_packages if name in required_packages]
    # # "bios" gets loaded automatically by the builder.
    # builder.add_software_package("bios", f"{SOC_DIR}/software/bios")
    return builder


def main():
    patch_cpu_variant()

    parser = argparse.ArgumentParser(description="HPS SoC")
    hps_soc_args(parser)
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    parser.add_argument("--slim_cpu", action="store_true",
                        help="DEPRECATED: use '--cpu-variant=slim+cfu' instead (Use slimmer VexRiscv (required for mnv2_first))")
    parser.add_argument("--build", action="store_true",
                        help="Whether to do a full build, including the bitstream")
    parser.add_argument("--toolchain", default="oxide",
                        help="Which toolchain to use: oxide (default) or radiant")
    parser.add_argument("--parallel-nextpnr", action="store_true",
                        help="Whether to use the parallel nextpnr script with the oxide toolchain")
    parser.add_argument("--extra-nextpnr-params", action="store_true", help="Enable extra nextpnr parameters")
    parser.add_argument("--synth_mode", default="radiant",
                        help="Which synthesis mode to use with Radiant toolchain: "
                        "radiant/synplify (default), lse, or yosys")
    parser.add_argument("--cpu-cfu", default=None, help="Specify file containing CFU Verilog module")
    parser.add_argument("--cpu-variant", default=None, help="Which CPU variant to use")
    parser.add_argument("--separate-arena", action="store_true", help="Create separate RAM for tensor arena")
    parser.add_argument("--cfu-mport", action="store_true", help="Create a direct connection between CFU and LRAM")
    parser.add_argument("--execute-from-lram", action="store_true",
                        help="Make the CPU execute from integrated ROM stored in LRAM instead of flash")
    parser.add_argument("--integrated-rom-init", metavar="FILE",
                        help="Use FILE as integrated ROM data instead of default BIOS")
    parser.add_argument("--build-bios", action="store_true",
                        help="Flag to specify that the BIOS is built as well")
    parser.add_argument("--just-synth", action='store_true', help="Stop after synthesis")
    parser.add_argument("--dynamic-clock-control", action="store_true",
                        help="Enable dynamic clock control between CPU and CFU to reduce FPGA power consumption.")

    args = parser.parse_args()

    if args.integrated_rom_init:
        integrated_rom_init = get_mem_data(args.integrated_rom_init, "little")
    else:
        integrated_rom_init = []

    if args.cpu_variant:
        variant = args.cpu_variant
    elif args.cpu_cfu:
        if  args.slim_cpu:
            variant = "slim+cfu+debug" if args.debug else "slim+cfu"
        else:
            variant = "full+cfu+debug" if args.debug else "full+cfu"
    else:
        variant = "full+debug" if args.debug else "full"
    copy_cpu_variant_if_needed(variant)
    soc = HpsSoC(Platform(args.toolchain, args.parallel_nextpnr, args.extra_nextpnr_params, args.just_synth),
                    debug=args.debug,
                    variant=variant,
                    cpu_cfu=args.cpu_cfu,
                    execute_from_lram=args.execute_from_lram,
                    separate_arena=args.separate_arena,
                    integrated_rom_init=integrated_rom_init,
                    build_bios=args.build_bios,
                    cfu_mport=args.cfu_mport,
                    dynamic_clock_control=args.dynamic_clock_control)

    if not args.build_bios:
        # To still allow building libraries needed
        # by the HPS software, without the necessity of
        # having the BIOS (and its gatware requirements such as the Timer)
        # this flag needs to be set to True
        soc.integrated_rom_initialized = True

    builder = create_builder(soc, args)
    builder_kwargs = {}
    if args.toolchain == "radiant":
        builder_kwargs.update(radiant_build_argdict(args))
    elif args.toolchain == "oxide":
        builder_kwargs.update(oxide_argdict(args))
    vns = builder.build(**builder_kwargs, run=args.build)
    soc.do_exit(vns)

    if not args.build:
        print("Use --build to build the bitstream, if needed")


if __name__ == "__main__":
    main()
