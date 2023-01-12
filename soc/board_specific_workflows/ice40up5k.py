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

import argparse
import general
import warnings
from litex.build import generic_programmer
from litex.soc.cores.cpu.vexriscv import core
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder
from typing import Callable



class Ice40UP5KWorkflow(general.GeneralSoCWorkflow):
    """Workflow for boards derived from the Ice40UP5K.
    
    This includes the iCEbreaker, Fomu, TinyFPGA, and a few more. All of these
    derived boards require a bios_flash_offset argument. They also cannot fit
    entire CFU-Playground into RAM, so they must put read-only data in flash.
    """
    def __init__(self,
                 args: argparse.Namespace,
                 soc_constructor: Callable[..., litex_soc.LiteXSoC],
                 builder_constructor: Callable[..., builder.Builder] = None,
                 warn: bool = True) -> None:

        allowed_variants = {
                'kosagi_fomu':  ['fomu', 'fonu+cfu', 'minimal', 'minimal+cfu'],
                'icebreaker':   ['fomu', 'fomu+cfu', 'breaker', 'breaker+cfu', 'minimal', 'minimal+cfu'],
        }
        assert args.target in allowed_variants, f"Internal error: unexpected target {args.target} for ice40-specific workflow."

        if args.cpu_variant not in allowed_variants[args.target]:
            if warn:
                warnings.warn(
                      f'\nOnly {allowed_variants[args.target]} variants of Vexriscv are supported for ' +
                      f'"{args.target}"; {args.cpu_variant} is not supported.\n' +
                      'Using fomu+cfu.')
            if 'cfu' in args.cpu_variant:
                args.cpu_variant = 'fomu+cfu'
            else:
                args.cpu_variant = 'fomu'

        # Offset of bios dictates CPU reset address. When loading the software
        # on the board, we overwrite the bios so now the CPU reset address
        # points to user code. At 0x30000, we can add approximately 90KiB to
        # the final gateware file before we start overwriting it with the
        # software (surprise?). Dynamically generating this offset is tricky
        # because we must specify the offset before building the gateware, but
        # we only know the ideal offset after the gateware file is made. The
        # offset must also be consistent in the linker script. For now, 0x30000
        # is sufficient.
        self.bios_flash_offset = 0x30000
        super().__init__(args, soc_constructor, builder_constructor)

    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """Runs the general make_soc with a bios_flash_offset."""
        soc = super().make_soc(bios_flash_offset=self.bios_flash_offset,
                                **kwargs)

        # restore full 128kB to "sram" region (steal back from "main_ram")
        soc.bus.regions["sram"].size = 128 * 1024;
        soc.bus.regions["main_ram"].origin = 128 * 1024;
        soc.bus.regions["main_ram"].size = 0;
        return soc

    def software_load(
            self,
            filename: str,
            programmer: generic_programmer.GenericProgrammer = None) -> None:
        """Boards derived from the Ice40UP5k need to flash software."""
        raise NotImplementedError
