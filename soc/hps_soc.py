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
    rom_origin = spiflash_region.origin + rom_offset
    rom_region = SoCRegion(rom_origin, spiflash_region.size - rom_offset,
                           cached=True, linker=True)
    sram_origin = 0x40000000
    sram_region = SoCRegion(sram_origin, RAM_SIZE, cached=True, linker=True)
    vexriscv_region = SoCRegion(origin=0xf00f0000, size=0x100)

    # These variables are needed by builder.py. Normally they're defined by
    # SoCCore, but we don't inherit from SoCCore.
    integrated_rom_initialized = False
    integrated_rom_size = rom_region.size

    mem_map = {
        "rom":  rom_offset,
        "sram": sram_origin,
        "csr":  csr_origin,
    }

    cpu_type = "vexriscv"

    def __init__(self, platform, debug, litespi_flash=False, variant=None, cpu_cfu=None):
        LiteXSoC.__init__(self,
                          platform=platform,
                          sys_clk_freq=platform.sys_clk_freq,
                          csr_data_width=(32 if litespi_flash else 8))
        if variant == None:
            variant = "full+debug" if debug else "full"

        # Clock, Controller, CPU
        self.submodules.crg = platform.create_crg()
        self.add_controller("ctrl")
        self.add_cpu(self.cpu_type,
                     variant=variant,
                     reset_address=self.rom_origin,
                     cfu=cpu_cfu)

        # RAM
        self.setup_ram()

        # SPI Flash
        if litespi_flash:
            self.setup_litespi_flash()
        else:
            self.setup_flash()

        # ROM (part of SPI Flash)
        self.bus.add_region("rom", self.rom_region)

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

    def setup_ram(self):
        self.submodules.lram = self.platform.create_ram(
            32, self.sram_region.size)
        self.bus.add_slave("sram_lram", self.lram.bus, self.sram_region)
        self.bus.add_region("sram", self.sram_region)

    def setup_flash(self):
        self.submodules.spiflash = SpiFlash(self.platform.request("spiflash"), dummy=8,
                                            endianness="little", div=4)
        self.bus.add_slave("spiflash", self.spiflash.bus, self.spiflash_region)
        self.csr.add("spiflash")
        
    def setup_litespi_flash(self):
        self.submodules.spiflash_phy  = LiteSPIPHY(self.platform.request("spiflash"), GD25LQ128D(Codes.READ_1_1_1), default_divisor=9)
        #self.submodules.spiflash_phy  = LiteSPIPHY(self.platform.request("spiflash4x"), GD25LQ128D(Codes.READ_1_1_4), default_divisor=9)
        self.submodules.spiflash_mmap  = LiteSPI(phy=self.spiflash_phy,
            clk_freq        = self.platform.sys_clk_freq,
            mmap_endianness = self.cpu.endianness)
        self.csr.add("spiflash_mmap")
        self.csr.add("spiflash_phy")
        self.bus.add_slave(name="spiflash", slave=self.spiflash_mmap.bus, region=self.spiflash_region)

    def add_serial(self):
        self.add_uart("serial", baudrate=UART_SPEED)

    def create_i2c_controller(self, pads):
        return I2CMaster(pads)

    # This method is defined on SoCCore and the builder assumes it exists.
    def initialize_rom(self, data):
        pass

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

        self.configure_rom()

    def configure_rom(self):
        # Have the builder build the BIOS, but not create an integrated ROM
        # self.integrated_rom_size = 0
        # self.integrated_rom_initialized = False
        pass


def hps_soc_args(parser: argparse.ArgumentParser):
    builder_args(parser)
    radiant_build_args(parser)

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

    args = parser.parse_args()

    # soc = HpsSoC(Platform(args.toolchain), debug=args.debug, litespi_flash=args.litespi_flash)
    soc = HpsSoC(Platform(args.toolchain), debug=args.debug, litespi_flash=True)

    if args.cpu_cfu:
        variant = "full+cfu+debug" if args.debug else "full+cfu"
        soc = HpsSoC(Platform(args.toolchain), debug=args.debug, litespi_flash=args.litespi_flash, variant=variant, cpu_cfu=args.cpu_cfu)
        if args.slim_cpu:
            # override the actual source to get the Slim version
            #  -- this is a hack needed because litex/.../vexriscv/core.py doesn't know about the Slim versions.
            vexriscv = "../third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv"
            var = "SlimCfuDebug" if args.debug else "SlimCfu"
            soc.cpu.use_external_variant(f"{vexriscv}/verilog/VexRiscv_{var}.v")
    else:
        variant = "full+debug" if args.debug else "full"
        soc = HpsSoC(Platform(args.toolchain), debug=args.debug, litespi_flash=args.litespi_flash, variant=variant)
        

    builder = create_builder(soc, args)
    builder_kwargs = radiant_build_argdict(args) if args.toolchain == "radiant" else {}
    vns = builder.build(**builder_kwargs, run=args.build)
    soc.do_exit(vns)

    if not args.build:
        print("Use --build to build the bitstream, if needed")


if __name__ == "__main__":
    main()
