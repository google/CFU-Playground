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
from litex.soc.integration import soc as litex_soc
from litex.soc.integration import builder
from litex.build.xilinx import vivado
from typing import Callable


class DigilentArtySoCWorkflow(general.GeneralSoCWorkflow):
    """Specializes the general workflow for the Digilent Arty."""
    def __init__(
        self,
        args: argparse.Namespace,
        soc_constructor: Callable[..., litex_soc.LiteXSoC],
        builder_constructor: Callable[..., builder.Builder] = None,
    ) -> None:
        """Initializes the Arty workflow with an extra --variant argument.
        
        Args:
            args: An argparse Namespace that holds SoC and build options.
            soc_constructor: The constructor for the LiteXSoC.
            builder_constructor: The constructor for the LiteX Builder. If
              omitted, litex.soc.integration.builder.Builder will be used.
        """
        parser = argparse.ArgumentParser(description='Digilent Arty args.')
        parser.add_argument('--variant',
                            default='a7-35',
                            help='Arty variant: a7-35 (default) or a7-100')
        arty_args = parser.parse_known_args()[0]
        args = argparse.Namespace(**vars(arty_args), **vars(args))

        #
        # If using SymbiFlow, and the user hasn't specified the target freq,
        # use 75MHz as default. Currently, using the litex-boards default 100MHz
        # with SymbiFlow usually results in a bitstream that does not function
        # on the board.
        #
        # This should be removed when SymbiFlow can reliably
        # produce a working bitstream at 100MHz.
        #
        if args.toolchain == 'symbiflow' and not args.sys_clk_freq:
            args.sys_clk_freq = 75000000
            print("INFO:Workflow:Setting sys_clk_freq to 75MHz.");

        super().__init__(args, soc_constructor, builder_constructor)

    def make_soc(self, **kwargs) -> litex_soc.LiteXSoC:
        """Runs make_soc with jtagbone disabled."""
        return super().make_soc(l2_size=self.args.l2_size,
                                variant=self.args.variant,
                                with_jtagbone=False,
                                **kwargs)

    def build_soc(self, soc: litex_soc.LiteXSoC, **kwargs) -> builder.Builder:
        """Specializes build_soc to add Vivado args if needed."""
        if isinstance(soc.platform.toolchain, vivado.XilinxVivadoToolchain):
            kwargs.update(vivado.vivado_build_argdict(self.args))
        return super().build_soc(soc, **kwargs)
