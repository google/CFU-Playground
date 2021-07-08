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
from litex.soc.integration import builder
from litex.soc.integration import soc as litex_soc
from litex.soc.integration.soc import SoCRegion

from litespi.modules import MX25L12835F
from litespi.opcodes import SpiNorFlashOpCodes as Codes
from litespi.phy.generic import LiteSPIPHY
from litespi import LiteSPI

KB = 1024
MB = 1024 * KB

class LatticeCrossLinkNXEVNSoCWorkflow(general.GeneralSoCWorkflow):
    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        soc = super().make_soc(
            integrated_rom_size=0,
            integrated_rom_init=[],
            **kwargs
        )

        soc.spiflash_region = SoCRegion(0x00000000, 16 * MB, mode="r", cached=True, linker=True)
        soc.submodules.spiflash_phy = LiteSPIPHY(
            soc.platform.request("spiflash"),
            MX25L12835F(Codes.READ_1_1_1),
            default_divisor=1)
        soc.submodules.spiflash_mmap = LiteSPI(phy=soc.spiflash_phy,
            clk_freq        = soc.sys_clk_freq,
            mmap_endianness = soc.cpu.endianness)

        soc.csr.add("spiflash_mmap")
        soc.csr.add("spiflash_phy")
        soc.bus.add_slave(name="spiflash", slave=soc.spiflash_mmap.bus, region=soc.spiflash_region)
        soc.bus.add_region("rom", soc.spiflash_region)

        return soc

    def build_soc(self, soc: litex_soc.LiteXSoC, **kwargs) -> builder.Builder:
        return super().build_soc(soc, **kwargs)
