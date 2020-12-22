#!/usr/bin/env python3

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

from migen import *

from litex_boards.targets.arty import BaseSoC

from litex.build.generic_platform import *
from litex.build.xilinx.vivado import vivado_build_args, vivado_build_argdict
from litex.build.sim.config import SimConfig

from litex.soc.integration.builder import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.common import get_mem_data

from litex.soc.cores.led import LedChaser
from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores.cpu import CPUS

from litex.tools.litex_sim import SimSoC

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

def configure_sim_builder(builder: Builder, args):
    required_packages = {"libcompiler_rt", "libbase"}
    # Remove unwanted packages that we don't need. Of most importance to remove
    # is the "bios" package, which is LiteX's BIOS, since we're using our own.
    builder.software_packages = [
        (name, dir) for (name, dir) in builder.software_packages if name in required_packages ]
    bios_dir = f"{builder.output_dir}/software/bios"
    os.makedirs(bios_dir, exist_ok=True)
    with open(f"{bios_dir}/Makefile", "w") as f:
        f.write(f"all:\n\tmake PLATFORM=sim -f {args.sim_rom_dir}/Makefile bios.bin")
    # "bios" gets loaded automatically by the builder.
    builder.add_software_package("bios", bios_dir)


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
    parser.add_argument("--sim-rom-dir", default=None,
        help="Simulate the FPGA on the local machine. Directory must support `make bios.bin`.")
    parser.add_argument("--sim-trace",  action="store_true", help="Whether to enable tracing of simulation")
    parser.add_argument("--sim-trace-start", default=0, help="Start tracing at this time in picoseconds")
    parser.add_argument("--sim-trace-end", default=-1, help="Stop tracing at this time in picoseconds")
    parser.set_defaults(
            csr_csv='csr.csv',
            uart_name='serial',
            uart_baudrate=115200,
            cpu_variant='full+debug',    # don't specify 'cfu' here
            with_etherbone=False)

    args = parser.parse_args()

    assert not (args.with_ethernet and args.with_etherbone)
    cpu = CPUS["vexriscv"]
    soc_kwargs = soc_sdram_argdict(args)
    sim_config = None
    sim_active = args.sim_rom_dir != None
    if sim_active:
        soc_kwargs["uart_name"] = "sim"
        soc = SimSoC(
            integrated_main_ram_size=32 * 1024 * 1024,
            **soc_kwargs)
        sim_config = SimConfig()
        sim_config.add_clocker("sys_clk", freq_hz=soc.clk_freq)
        sim_config.add_module("serial2console", "serial")
        soc.add_constant("ROM_BOOT_ADDRESS", 0x40000000)
    else:
        soc = CustomSoC(with_ethernet=args.with_ethernet, with_etherbone=args.with_etherbone,
            **soc_sdram_argdict(args))

    # get the CFU version, plus the CFU itself and a wrapper 
    # ...since we're using stock litex, it doesn't know about the Cfu variants, so we need to use "external_variant"
    if args.cfu:
        assert 'full' in args.cpu_variant
        var = "FullCfuDebug" if ('debug' in args.cpu_variant) else "FullCfu"
        vexriscv = "../third_party/python/pythondata_cpu_vexriscv/pythondata_cpu_vexriscv"
        soc.cpu.use_external_variant(f"{vexriscv}/verilog/VexRiscv_{var}.v")
        soc.platform.add_source(args.cfu)
        soc.platform.add_source(f"{vexriscv}/verilog/wrapVexRiscv_{var}.v")

    builder = Builder(soc, **builder_argdict(args))

    if sim_active:
        configure_sim_builder(builder, args)
        builder.build(
            build=True,
            run=True,
            sim_config=sim_config,
            trace=args.sim_trace,
            trace_fst=True,
            trace_start=int(float(args.sim_trace_start)),
            trace_end=int(float(args.sim_trace_end)))
    else:
        builder.build(**vivado_build_argdict(args), run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        bitstream_filename = os.path.join(builder.gateware_dir, soc.build_name + ".bit")
        prog.load_bitstream(bitstream_filename)


if __name__ == "__main__":
    main()
