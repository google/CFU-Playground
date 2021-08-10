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
import ice40up5k
import io
from litex.build import dfu, generic_programmer
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder
from typing import BinaryIO, Callable, Collection


def create_image(gateware: BinaryIO, software: BinaryIO,
                 software_offset: int) -> Collection[bytes]:
    """Creates an image file that combines gateware and software.

    Args:
        gateware: BinaryIO object that contains the gateware bitstream.
        software: BinaryIO object that contains the software binary.
        software_offset: Offset from the start of the output image
            that the software begins at.
    
    Returns:
        A Collection of bytes that contains the gateware followed by the
        software beginning at `software_offset` bytes from the start of the
        output.
    
    Raises:
        ValueError: `gateware` is too large and will be partially overwritten
            by `software`.
    """
    with io.BytesIO() as output_image:
        bitstream = gateware.read()
        if len(bitstream) > software_offset:
            raise ValueError(('Gateware file overflowed by '
                              f'{len(bitstream) - software_offset} bytes.'))
        output_image.write(bitstream)
        output_image.write(
            bytes(0xff for _ in range(software_offset - len(bitstream))))
        output_image.write(software.read())
        return bytes(output_image.getvalue())


def fomu_image_builder(gateware_filename: str, software_filename: str,
                       image_filename: str, offset: int) -> None:
    """Creates and writes an image file for the Fomu.
    
    This is a thin wrapper around create_image that is useful for testing.

    Args:
        gateware_filename: The file that contains the gateware.
        software_filename: The file that contains the software.
        image_filename: The file that will hold the output image.
        offset: Offset from the start of the output image
            that the software begins at.
    
    Raises:
        ValueError: `gateware` is too large and will be partially overwritten
            by `software`.
    """
    with open(gateware_filename, 'rb') as gateware, \
         open(software_filename, 'rb') as software, \
         open(image_filename, 'wb') as image:
        image.write(create_image(gateware, software, offset))


class KosagiFomuSoCWorkflow(ice40up5k.Ice40UP5KWorkflow):
    """Workflow for the Fomu board."""
    def __init__(self,
                 args: argparse.Namespace,
                 soc_constructor: Callable[..., litex_soc.LiteXSoC],
                 builder_constructor: Callable[..., builder.Builder] = None,
                 warn: bool = True) -> None:
        super().__init__(args,
                         soc_constructor,
                         builder_constructor=builder_constructor,
                         warn=warn)
        # Fomu requires larger flash offset -- first 0x40000 bytes are reserved
        self.bios_flash_offset = 0x60000

    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """Makes the Fomu SoC without many LiteX peripherals to save LCs."""
        # integrated_rom_init required to avoid compiler errors building bios.
        return super().make_soc(integrated_rom_init=[None],
                                spi_flash_module='W25Q128JV',
                                with_ctrl=False,
                                with_led_chaser=False,
                                with_timer=False,
                                **kwargs)

    def load(self,
             soc: litex_soc.LiteXSoC,
             soc_builder: builder.Builder,
             programmer: generic_programmer.GenericProgrammer = None) -> None:
        """For the Fomu, this is a no-op.

           Because the Fomu requires a power cycle between flashes, loading the
           bios is skipped to simplify loading software.
        """

    def software_load(self,
                      filename: str,
                      programmer: generic_programmer.GenericProgrammer = None,
                      image_builder=fomu_image_builder) -> None:
        """Loads software for the Fomu.
        
        Args:
            filename: The software binary.
            programmer: The programmer used to flash the board. If none
                specified, DFUProg will be used.
            image_builder: The function used to create the image file. Used for
                dependency injection.
        """
        gateware_filename = (f'{self.args.output_dir}'
                             '/gateware/kosagi_fomu_pvt.bin')
        image_filename = f'{self.args.output_dir}/image.bin'

        image_builder(gateware_filename=gateware_filename,
                      software_filename=filename,
                      image_filename=image_filename,
                      offset=self.bios_flash_offset - 0x40000)

        prog = programmer or dfu.DFUProg(pid='5bf0', vid='1209')
        prog.load_bitstream(image_filename)
