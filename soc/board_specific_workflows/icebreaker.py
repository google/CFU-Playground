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

import ice40up5k
from litex.build import generic_programmer
from litex.build.lattice import programmer as lattice_programmer
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder


def flash(offset: int,
          filename: str,
          programmer: generic_programmer.GenericProgrammer = None) -> None:
    """Flashes a file at a specific offset for the iCEbreaker.

    Args:
        offset: The offset (in bytes) of the start of the file in flash.
        filename: The file to be flashed.
        programmer: The programmer to flash the board. If none provided,
            the IceStormProgrammer will be used.
    """
    prog = programmer or lattice_programmer.IceStormProgrammer()
    prog.flash(offset, filename)


class IcebreakerSoCWorkflow(ice40up5k.Ice40UP5KWorkflow):
    """Workflow for the iCEbreaker board."""
    def load(self,
             soc: litex_soc.LiteXSoC,
             soc_builder: builder.Builder,
             programmer: generic_programmer.GenericProgrammer = None) -> None:
        """Loads gateware and bios onto the board.
        
        Args:
            soc: The SoC to be loaded.
            soc_builder: The Builder that generated the SoC.
            programmer: The programmer to flash the board. If none provided,
                the IceStormProgrammer will be used.
        """
        flash(0x0, f'{soc_builder.output_dir}/gateware/{soc.build_name}.bin',
              programmer)

        # Flashing bios perhaps unnecessary if we always plan to overwrite it.
        flash(self.bios_flash_offset,
              f'{soc_builder.output_dir}/software/bios/bios.bin', programmer)

    def software_load(
            self,
            filename: str,
            programmer: generic_programmer.GenericProgrammer = None) -> None:
        """Loads software on top of the bios.
        
        Args:
            filename: The file being uploaded over the bios.
            programmer: The programmer used to flash the board. If none
                specified, the IceStormProgrammer will be used.
        """
        flash(self.bios_flash_offset, filename, programmer)
