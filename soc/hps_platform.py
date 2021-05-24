# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from migen import Module, ClockDomain, Signal, If, log2_int
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.generic_platform import Pins, Subsignal, IOStandard
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import LatticeProgrammer
from litex.soc.cores.ram import NXLRAM
from litex.soc.cores.clock import NXOSCA

hps_io = [
    # Connection to motherboard
    ("i2c", 0,
        Subsignal("scl", Pins("D1")),
        Subsignal("sda", Pins("E3")),
        IOStandard("LVCMOS18H")
     ),
    ("done", 0, Pins("A5"), IOStandard("LVCMOS18H")),
    ("programn", 0, Pins("A4"), IOStandard("LVCMOS18H")),
    # JTAG: not usually programatically accessible
    ("jtag", 0,
        Subsignal("en", Pins("C2")),
        Subsignal("tck", Pins("D2")),
        Subsignal("tdi", Pins("C3")),
        Subsignal("tdo", Pins("D3")),
        Subsignal("tms", Pins("B1")),
        IOStandard("LVCMOS18H")
     ),
    # SPI flash, defined two ways
    ("spiflash", 0,
        Subsignal("cs_n", Pins("A3")),
        Subsignal("clk",  Pins("B4")),
        Subsignal("mosi", Pins("B5")),
        Subsignal("miso", Pins("C4")),
        Subsignal("wp",   Pins("B3")),
        Subsignal("hold", Pins("B2")),
        IOStandard("LVCMOS18")
     ),
    ("spiflash4x", 0,
        Subsignal("cs_n", Pins("A3")),
        Subsignal("clk", Pins("B4")),
        Subsignal("dq", Pins("B5 C4 B3 B2")),
        IOStandard("LVCMOS18")
     ),
]

# These should have equivalents defined in simulation.py.
hps_nx17_io = [
    ("i2c", 1,
        Subsignal("scl", Pins("H1")),
        Subsignal("sda", Pins("G2")),
        IOStandard("LVCMOS18H")
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
    # 2nd UART on JTAG TDI/TDO pins - must disable JTAG to use
    ("serial2", 0,
        Subsignal("rx", Pins("C3")),
        Subsignal("tx", Pins("D3")),
        IOStandard("LVCMOS18H")
     ),
]

# Debug IO that is common to both simulation and hardware.
hps_debug_common = [
    # Single LED on JTAG pin - J8 pin 6
    ("user_led", 0, Pins("D2"),  IOStandard("LVCMOS18")),
]


class _CRG(Module):
    """Clock Reset Generator"""

    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_por = ClockDomain()

        # Clock from HFOSC
        self.submodules.sys_clk = sys_osc = NXOSCA()
        sys_osc.create_hf_clk(self.cd_sys, sys_clk_freq)
        platform.add_period_constraint(self.cd_sys.clk, 1e9/sys_clk_freq)

        # Power On Reset
        por_cycles = 4096
        por_counter = Signal(log2_int(por_cycles), reset=por_cycles-1)
        self.comb += self.cd_por.clk.eq(self.cd_sys.clk)
        self.sync.por += If(por_counter != 0, por_counter.eq(por_counter - 1))
        self.specials += AsyncResetSynchronizer(
            self.cd_sys, (por_counter != 0))


class Platform(LatticePlatform):
    # The NX-17 has a 450 MHz clock. Our system clock should be a divisor of that.
    clk_divisor = 4
    sys_clk_freq = int(450e6 / clk_divisor)

    def __init__(self, toolchain="radiant"):
        LatticePlatform.__init__(self,
                                 # The HPS actually has the LIFCL-17-7UWG72C, but that doesn't
                                 # seem to be available in Radiant 2.2, at least on Linux.
                                 device="LIFCL-17-8UWG72C",
                                 io=hps_io + hps_nx17_io + hps_nx17_debug_io + hps_debug_common,
                                 connectors=[],
                                 toolchain=toolchain)

    def create_crg(self):
        return _CRG(self, self.sys_clk_freq)

    def create_ram(self, width, size):
        return NXLRAM(width, size)

    # TODO: add create_programmer function
