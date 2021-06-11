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
import importlib
import litex.build.xilinx.vivado as litex_vivado
import litex.soc.integration.builder as litex_builder
import litex.soc.integration.soc as litex_soc
import litex.soc.integration.soc_core as litex_soc_core
import os

# By caching this type we are allowed to patch it in tests.
_VIVADO_TOOLCHAIN_TYPE = litex_vivado.XilinxVivadoToolchain


class GeneralSoCWorkflow():
    """Base class that implements general workflow for building/loading a SoC.

    For many boards this class is sufficient, but some boards will require
    a subclass that overrides one or more of the methods for designing,
    building, and loading the SoC.

    Attributes:
        args: An argparse Namespace that holds SoC and build options.
        module: The Litex-Boards module for the target board.
    """
    def __init__(self, args: argparse.Namespace) -> None:
        try:
            self.module = importlib.import_module(
                self.format_import_path(args.target))
        except:
            raise ModuleNotFoundError(f'Could not load {args.target} target.')
        self.args = args

    @classmethod
    def format_import_path(cls, target: str) -> str:
        """Formats the import path for the litex_boards import."""
        return f'litex_boards.targets.{target}'

    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """ Utilizes self.module.BaseSoC to make a LiteXSoC.
        
        Args:
            **kwargs: Arguments meant to extend/overwrite the general
              arguments to self.module.BaseSoc.
        
        Returns:
            The LiteXSoC for the target board.
        """
        base_soc_kwargs = {
            'with_ethernet': self.args.with_ethernet,
            'with_etherbone': self.args.with_etherbone,
            'with_mapped_flash': self.args.with_mapped_flash,
        }
        base_soc_kwargs.update(litex_soc_core.soc_core_argdict(self.args))
        if self.args.toolchain:
            base_soc_kwargs['toolchain'] = self.args.toolchain

        base_soc_kwargs.update(kwargs)
        return self.module.BaseSoC(**base_soc_kwargs)

    def build_soc(self, soc: litex_soc.LiteXSoC,
                  **kwargs) -> litex_builder.Builder:
        """ Creates a LiteX Builder and builds the Soc if self.args.build.
        
        Args:
            soc: The LiteXSoC meant to be built.
            **kwargs: Arguments meant to extend/overwrite the general
              arguments to the LiteX Builder.

        Returns:
            The LiteX Builder for the SoC.
        """
        builder_kwargs = litex_builder.builder_argdict(self.args)
        builder_kwargs.update(kwargs)
        builder = litex_builder.Builder(soc, **builder_kwargs)
        if isinstance(soc.platform.toolchain, _VIVADO_TOOLCHAIN_TYPE):
            builder.build(**litex_vivado.vivado_build_argdict(self.args),
                          run=self.args.build)
        else:
            builder.build(run=self.args.build)
        return builder

    def load(self, soc: litex_soc.LiteXSoC,
             builder: litex_builder.Builder) -> None:
        """ Loads a SoC onto the target baord.
        
        Args:
            soc: The LiteXSoc meant to be loaded.
            builder: The LiteX builder used to build the SoC.
        """
        prog = soc.platform.create_programmer()
        bitstream_filename = self.format_bitstream_filename(builder.gateware_dir, soc.build_name)
        prog.load_bitstream(bitstream_filename)
    
    @classmethod
    def format_bitstream_filename(cls, directory: str, build_name: str) -> str:
        return os.path.join(directory, f'{build_name}.bit')

    def run(self) -> None:
        """ Runs the workflow in order (make_soc -> build_soc -> load)."""
        soc = self.make_soc()
        builder = self.build_soc(soc)
        if self.args.load:
            self.load(soc, builder)
