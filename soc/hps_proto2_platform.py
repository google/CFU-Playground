# Copyright 2021 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from migen import Module, ClockDomain, Signal, If, log2_int
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.generic_platform import Pins, Subsignal, IOStandard, Misc
from litex.build.lattice import LatticePlatform, oxide
from litex.build.lattice.programmer import LatticeProgrammer
from litex.soc.cores.clock import NXOSCA
# from litex.soc.cores.ram import NXLRAM
from hps_lattice_nx import NXLRAM

hps_io = [
    ("done", 0, Pins("A5"), IOStandard("LVCMOS18H")),
    ("programn", 0, Pins("A4"), IOStandard("LVCMOS18H")),
    # JTAG: not usually programatically accessible
    ("jtag", 0,
        Subsignal("en", Pins("C2")),
        Subsignal("tck", Pins("D2")),
        Subsignal("tdi", Pins("C3")),
        Subsignal("tdo", Pins("D3")),
        Subsignal("tms", Pins("B1")),
        IOStandard("LVCMOS18H"),
        Misc("SLEWRATE=FAST"),
     ),
    # SPI flash, defined two ways
    ("spiflash", 0,
        Subsignal("cs_n", Pins("A3")),
        Subsignal("clk", Pins("B4")),
        Subsignal("mosi", Pins("B5")),
        Subsignal("miso", Pins("C4")),
        Subsignal("wp", Pins("B3")),
        Subsignal("hold", Pins("B2")),
        IOStandard("LVCMOS18"),
        Misc("SLEWRATE=FAST"),
     ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("A3")),
        Subsignal("clk", Pins("B4")),
        Subsignal("dq", Pins("B5 C4 B3 B2")),
        IOStandard("LVCMOS18"),
        Misc("SLEWRATE=FAST"),
     ),
]

# Debug IO that is specific to the HPS hardware. These should have equivalents
# defined in simulation.py if they are referenced from C code.
hps_nx17_debug_io = [
    # Debug UART
    ("serial", 0,
        Subsignal("rx", Pins("E2"), IOStandard("LVCMOS18")),
        Subsignal("tx", Pins("G1"), IOStandard("LVCMOS18H")),
     ),
]

# Debug IO that is common to both simulation and hardware.
hps_debug_common = [
    ("user_led", 0, Pins("G3"), IOStandard("LVCMOS18H")),
]


class _CRG(Module):
    """Clock Reset Generator"""

    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_por = ClockDomain()

        # Clock from HFOSC
        self.submodules.sys_clk = sys_osc = NXOSCA()
        sys_osc.create_hf_clk(self.cd_sys, sys_clk_freq)
        # We make the period constraint 10% tighter than our actual system
        # clock frequency, because the CrossLink-NX internal oscillator runs
        # at ±10% of nominal frequency.
        platform.add_period_constraint(self.cd_sys.clk,
                                       1e9 / (sys_clk_freq * 1.1))

        # Power On Reset
        por_cycles = 4096
        por_counter = Signal(log2_int(por_cycles), reset=por_cycles - 1)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.sync.por += If(por_counter != 0, por_counter.eq(por_counter - 1))
        self.specials += AsyncResetSynchronizer(
            self.cd_sys, (por_counter != 0))


_nextpnr_report_filename = 'nextpnr-nexus-report.json'

# Template for build script that uses parallel-nextpnr-nexus to run many copies
# of nextpnr-nexus in parallel
_oxide_parallel_build_template = [
    "yosys -l {build_name}.rpt {build_name}.ys",
    "parallel-nextpnr-nexus {build_name}.json {build_name}.pdc {build_name}.fasm \
        $(nproc) {seed}",
    "prjoxide pack {build_name}.fasm {build_name}.bit"
]

# Template for build script that adds custom nextpnr parameters
_oxide_custom_build_template = [
    "yosys -l {build_name}.rpt {build_name}.ys",
    "custom-nextpnr-nexus {build_name}.json {build_name}.pdc {build_name}.fasm",
    "prjoxide pack {build_name}.fasm {build_name}.bit"
]

# Template for ending the build after synthesis
_oxide_synth_build_template = [
    "yosys -l {build_name}.rpt {build_name}.ys"
]

# Template for build script that passes --router router1
_oxide_router1_build_template = [
    'yosys -l {build_name}.rpt {build_name}.ys',
    ('nextpnr-nexus '
     '--json {build_name}.json '
     '--pdc {build_name}.pdc '
     '--fasm {build_name}.fasm '
     '--report={build_name}-report.json '
     '--detailed-timing-report '
     '--device {device} '
     '{timefailarg} '
     '{ignoreloops} '
     '--seed {seed} '
     '--router router1'
     ),
    'prjoxide pack {build_name}.fasm {build_name}.bit',
]


class Platform(LatticePlatform):
    # The NX-17 has a 450 MHz oscillator. Our system clock should be a divisor
    # of that.
    clk_divisor = 9
    sys_clk_freq = int(450e6 / clk_divisor)

    def __init__(self, toolchain="radiant", parallel_pnr=False, custom_params=False, just_synth=False):
        LatticePlatform.__init__(self,
                                 # The HPS actually has the LIFCL-17-7UWG72C, but that doesn't
                                 # seem to be available in Radiant 2.2, at
                                 # least on Linux.
                                 device="LIFCL-17-8UWG72C",
                                 io=hps_io + hps_nx17_debug_io + hps_debug_common,
                                 connectors=[],
                                 toolchain=toolchain)
        if toolchain == "oxide":
            if just_synth:
                self.toolchain.build_template = _oxide_synth_build_template
            elif custom_params:
                self.toolchain.build_template = _oxide_custom_build_template
            elif parallel_pnr:
                self.toolchain.build_template = _oxide_parallel_build_template
            else:
                self.toolchain.build_template = _oxide_router1_build_template

    def create_crg(self):
        return _CRG(self, self.sys_clk_freq)

    def create_ram(self, width, size, dual_port=False):
        return NXLRAM(width, size, dual_port=dual_port)

    # TODO: add create_programmer function
