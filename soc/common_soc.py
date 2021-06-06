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

from migen import *

from litex.build.xilinx.vivado import vivado_build_args, vivado_build_argdict, XilinxVivadoToolchain

from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import soc_core_args, soc_core_argdict

import argparse
import os

from importlib import import_module

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    parser.add_argument("--toolchain", help="Specify toolchain for implementing gateware ('vivado' or 'symbiflow')")
    builder_args(parser)
    soc_core_args(parser)
    vivado_build_args(parser)
    parser.add_argument("--with-ethernet",  action="store_true", help="Enable Ethernet support")
    parser.add_argument("--with-etherbone", action="store_true", help="Enable Etherbone support")
    parser.add_argument("--with-mapped-flash", action="store_true", help="Add litespi SPI flash")
    parser.add_argument("--target",  default="digilent_arty", help="Specify target board")
    parser.set_defaults(
            csr_csv='csr.csv',
            uart_name='serial',
            uart_baudrate=921600,
            cpu_variant='full+cfu+debug',
            with_etherbone=False)

    args = parser.parse_args()

    assert not (args.with_ethernet and args.with_etherbone)
    soc_kwargs = soc_core_argdict(args)
    soc_kwargs["l2_size"] = 8 * 1024

    try:
        module = import_module("litex_boards.targets." + args.target)
    except:
        raise ModuleNotFoundError("could not load " + args.target + " target.")
    
    class CustomSoC(module.BaseSoC):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    kwargs = dict(
        with_ethernet=args.with_ethernet, 
        with_etherbone=args.with_etherbone,
        with_mapped_flash=args.with_mapped_flash,
        **soc_kwargs
    )
    
    if args.toolchain:
        kwargs["toolchain"] = args.toolchain
    soc = CustomSoC(**kwargs)

    builder = Builder(soc, **builder_argdict(args))

    if isinstance(soc.platform.toolchain, XilinxVivadoToolchain):
        builder.build(**vivado_build_argdict(args), run=args.build)
    else:
        builder.build(**{}, run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        bitstream_filename = os.path.join(builder.gateware_dir, soc.build_name + ".bit")
        prog.load_bitstream(bitstream_filename)

if __name__ == "__main__":
    main()
