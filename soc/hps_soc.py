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

from hps_platform import Platform
from litex.soc.cores.clock import S7PLL
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import Builder, builder_args, builder_argdict
from litex.soc.integration.soc import LiteXSoC, SoCRegion
from litex.soc.cores.led import LedChaser
from litex.soc.cores.spi_flash import SpiFlash
from litex.soc.cores.bitbang import I2CMaster

from litex.build.lattice.radiant import radiant_build_args, radiant_build_argdict
from litex.build.lattice.oxide import oxide_args, oxide_argdict

from litespi.modules import GD25LQ128D
from litespi.opcodes import SpiNorFlashOpCodes as Codes
from litespi.phy.generic import LiteSPIPHY
from litespi import LiteSPI

from patch import Patch
# from cam_control import CameraControl

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
    vexriscv_region = SoCRegion(origin=0xf00f0000, size=0x100)

    mem_map = {
        "sram": sram_origin,
        "csr":  csr_origin,
    }

    cpu_type = "vexriscv"

    def __init__(self, platform, debug, litespi_flash=False, variant=None,
                 cpu_cfu=None, execute_from_lram=False):
        LiteXSoC.__init__(self,
                          platform=platform,
                          sys_clk_freq=platform.sys_clk_freq,
                          csr_data_width=(32 if litespi_flash else 8))
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
        if execute_from_lram:
            # Leave one LRAM free for ROM
            ram_size = RAM_SIZE - 64*KB
        else:
            ram_size = RAM_SIZE
        self.setup_ram(size=ram_size)

        # SPI Flash
        if litespi_flash:
            self.setup_litespi_flash()
        else:
            self.setup_flash()

        # ROM (either part of SPI Flash, or embedded)
        if execute_from_lram:
            self.setup_rom_in_lram()
        else:
            self.setup_rom_in_flash()

        # "LEDS" - Just one LED on JTAG port
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

        # Timer
        self.add_timer(name="timer0")
        self.timer0.add_uptime()


        # i2c1
        self.submodules.i2c = self.create_i2c_controller(
            self.platform.request("i2c", 1))
        self.csr.add("i2c")

    def setup_ram(self, size):
        region = SoCRegion(self.sram_origin, size, cached=True, linker=True)
        self.submodules.lram = self.platform.create_ram(32, size)
        self.bus.add_slave("sram_lram", self.lram.bus, region)
        self.bus.add_region("sram", region)

    def setup_rom_in_lram(self):
        region = SoCRegion(self.cpu.reset_address, 64 * KB, mode='r',
                           cached=True, linker=True)
        self.submodules.rom = self.platform.create_ram(32, region.size)
        self.bus.add_slave("rom_lram", self.rom.bus, region)
        self.bus.add_region("rom", region)
        self.integrated_rom_initialized = False
        self.integrated_rom_size = region.size

    def setup_flash(self):
        self.submodules.spiflash = SpiFlash(self.platform.request("spiflash"), dummy=8,
                                            endianness="little", div=4)
        self.bus.add_slave("spiflash", self.spiflash.bus, self.spiflash_region)
        self.csr.add("spiflash")
        
    def setup_litespi_flash(self):
        self.submodules.spiflash_phy  = LiteSPIPHY(self.platform.request("spiflash"), GD25LQ128D(Codes.READ_1_1_1), default_divisor=1)
        self.submodules.spiflash_mmap  = LiteSPI(phy=self.spiflash_phy,
            clk_freq        = self.platform.sys_clk_freq,
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
        self.add_uart("serial", baudrate=UART_SPEED)

    def create_i2c_controller(self, pads):
        return I2CMaster(pads)

    # This method is defined on SoCCore and the builder assumes it exists.
    def initialize_rom(self, data):
        if hasattr(self, 'rom'):
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
    parser = argparse.ArgumentParser(description="HPS SoC")
    hps_soc_args(parser)
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    parser.add_argument("--slim_cpu", action="store_true",
                        help="Use slimmer VexRiscv (required for mnv2_first)")
    parser.add_argument("--build", action="store_true",
                        help="Whether to do a full build, including the bitstream")
    parser.add_argument("--toolchain", default="radiant",
                        help="Which toolchain to use, radiant (default) or oxide")
    parser.add_argument("--synth_mode", default="radiant",
                        help="Which synthesis to use, radiant/synplify (default), lse, or yosys")
    parser.add_argument("--litespi-flash", action="store_true", help="Use litespi flash")
    parser.add_argument("--cpu-cfu", default=None, help="Specify file containing CFU Verilog module")
    parser.add_argument("--execute-from-lram", action="store_true",
                        help="Make the CPU execute from integrated ROM stored in LRAM instead of flash")

    args = parser.parse_args()


    if args.cpu_cfu:
        variant = "full+cfu+debug" if args.debug else "full+cfu"
        soc = HpsSoC(Platform(args.toolchain),
                     debug=args.debug,
                     litespi_flash=args.litespi_flash,
                     variant=variant,
                     cpu_cfu=args.cpu_cfu,
                     execute_from_lram=args.execute_from_lram)
        if args.slim_cpu:
            # override the actual source to get the Slim version
            #  -- this is a hack needed because litex/.../vexriscv/core.py doesn't know about the Slim versions.
            vexriscv = "../third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv"
            var = "SlimCfuDebug" if args.debug else "SlimCfu"
            soc.cpu.use_external_variant(f"{vexriscv}/verilog/VexRiscv_{var}.v")
    else:
        variant = "full+debug" if args.debug else "full"
        soc = HpsSoC(Platform(args.toolchain),
                     debug=args.debug,
                     litespi_flash=args.litespi_flash,
                     variant=variant,
                     execute_from_lram=args.execute_from_lram)

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
