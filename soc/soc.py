#!/usr/bin/env python3
# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "vivado"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

from migen import *

from litex_boards.targets.arty import BaseSoC

from litex.build.generic_platform import *
from litex.build.xilinx.vivado import vivado_build_args, vivado_build_argdict

from litex.soc.integration.builder import *
from litex.soc.integration.soc_sdram import *

from litex.soc.cores.led import LedChaser
from litex.soc.cores.uart import UARTWishboneBridge

import argparse
import os

_uart_bone_serial = [ 
    ("uart_bone_serial", 0,
        # Outer analog header, marked "A0", "A1"
        Subsignal("tx", Pins("F5")),
        Subsignal("rx", Pins("D8")),
        IOStandard("LVCMOS33")
    )
]


class CustomSoC(BaseSoC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Add a UARTBone bridge connected to external UART/USB bridge
        # self.platform.add_extension(_uart_bone_serial)
        # self.add_uartbone(name="uart_bone_serial", baudrate=kwargs['uart_baudrate'])

        # Add in debug registers
        if 'debug' in kwargs['cpu_variant']:
            self.register_mem("vexriscv_debug", 0xf00f0000, self.cpu.debug_bus, 0x100)

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Arty A7")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    builder_args(parser)
    soc_sdram_args(parser)
    vivado_build_args(parser)
    parser.add_argument("--with-ethernet",  action="store_true", help="Enable Ethernet support")
    parser.add_argument("--with-etherbone", action="store_true", help="Enable Etherbone support")
    parser.add_argument("--cfu", default=None, help="Specify file containing CFU Verilog module")
    parser.set_defaults(
            csr_csv='csr.csv',
            uart_name='serial',
            uart_baudrate=115200,
            cpu_variant='full+debug',    # don't specify 'cfu' here
            with_etherbone=False)

    args = parser.parse_args()

    assert not (args.with_ethernet and args.with_etherbone)
    soc = CustomSoC(with_ethernet=args.with_ethernet, with_etherbone=args.with_etherbone,
        **soc_sdram_argdict(args))

    # get the CFU version, plus the CFU itself and a wrapper 
    # ...since we're using stock litex, it doesn't know about the Cfu variants, so we need to use "external_variant"
    if args.cfu:
        assert 'full' in args.cpu_variant
        var = "FullCfuDebug" if ('debug' in args.cpu_variant) else "FullCfu"
        soc.cpu.use_external_variant("deps/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv/verilog/VexRiscv_"+var+".v")
        soc.platform.add_source(args.cfu)
        soc.platform.add_source("deps/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv/verilog/wrapVexRiscv_"+var+".v")

    builder = Builder(soc, **builder_argdict(args))
    builder.build(**vivado_build_argdict(args), run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        bitstream_filename = os.path.join(builder.gateware_dir, soc.build_name + ".bit")
        prog.load_bitstream(bitstream_filename)


if __name__ == "__main__":
    main()
