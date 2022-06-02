# This file is part of LiteX.
#
# Copyright (c) 2020 David Corrigan <davidcorrigan714@gmail.com>
# Copyright (c) 2019 William D. Jones <thor0505@comcast.net>
# Copyright (c) 2019 Tim 'mithro' Ansell <me@mith.ro>
# Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause
#
"""NX family-specific Wishbone interface to the LRAM primitive.

Each LRAM is 64kBytes arranged in 32 bit wide words.

##################################################################
 This is a modified version of litex/soc/cores/ram/lattice_nx.py
 Modified by CFU Playground Authors to:
  * optionally use the dual port LRAM primitive
  * optionally stripe consecutive addresses across the banks
##################################################################

 When the striping option is used:

 The RAM from which data is fetched consists of 4 32 bit wide, 16K words deep
 LRAMs, with word addresses in rows across the LRAMs:
 (this is how the "arena" address space looks from the Wishbone bus)

 +--------+--------+--------+--------+
 | LRAM 0 | LRAM 1 | LRAM 2 | LRAM 3 |
 +--------+--------+--------+--------+
 |    0   |    1   |    2   |    3   |
 +--------+--------+--------+--------+
 |    4   |    5   |    6   |    7   |
 +--------+--------+--------+--------+
 |    8   |    9   |   10   |   11   |
 +--------+--------+--------+--------+
 |  ...   |  ...   |  ...   |  ...   |
 +--------+--------+--------+--------+

  In addition, each LRAM has a second port that gets connected directly to the CFU.
  From each of these ports, the connected LRAM is word addressed consecutively.

  Thus, "arena" offset 4 from the Wishbone bus can also be accessed at
  address 0x1 from the LRAM-0 port connected to the CFU.

"""

from migen import *
from litex.soc.interconnect import wishbone

kB = 1024



def initval_parameters(contents, width):
    """
    In Radiant, initial values for LRAM are passed a sequence of parameters
    named INITVAL_00 ... INITVAL_7F. Each parameter value contains 4096 bits
    of data, encoded as a 1280-digit hexadecimal number, with
    alternating sequences of 8 bits of padding and 32 bits of real data,
    making up 64KiB altogether.
    """
    assert width in [32, 64]
    # Each LRAM is 64KiB == 524288 bits
    assert len(contents) == 524288 // width
    chunk_size = 4096 // width
    parameters = []
    for i in range(0x80):
        name = 'INITVAL_{:02X}'.format(i)
        offset = chunk_size * i
        if width == 32:
            value = '0x' + ''.join('00{:08X}'.format(contents[offset + j])
                                   for j in range(chunk_size - 1, -1, -1))
        elif width == 64:
            value = '0x' + ''.join('00{:08X}00{:08X}'.format(contents[offset + j] >> 32, contents[offset + j] | 0xFFFFFF)
                                   for j in range(chunk_size - 1, -1, -1))
        parameters.append(Instance.Parameter(name, value))
    return parameters


class NXLRAM(Module):
    def __init__(self, width=32, size=128*kB, dual_port=False, init=[]):
        self.bus = wishbone.Interface(width)
        assert width in [32, 64]
        self.width = width
        self.size = size

        if width == 32:
            assert size in [64*kB, 128*kB, 192*kB, 256*kB, 320*kB]
            self.depth_cascading = size//(64*kB)
            self.width_cascading = 1
        if width == 64:
            assert size in [128*kB, 256*kB]
            self.depth_cascading = size//(128*kB)
            self.width_cascading = 2

        self.lram_blocks = []
        sel_bits = (self.depth_cascading-1).bit_length()

        # currently tie "sel_uses_lsb" to "dual_port"
        #   (they *can* be independent)
        sel_uses_lsb = dual_port

        if sel_uses_lsb:
            #
            # REQUIRES that self.depth_cascading be a power of 2
            #
            assert 2**sel_bits == self.depth_cascading, \
                f"Memory size {size} results in depth of {self.depth_cascading}, but depth must be a power of 2."
            sel_bits_start = 0
            adr_bits_start = sel_bits
        else:
            sel_bits_start = 14
            adr_bits_start = 0

        print("sel_bits ", sel_bits)
        print("sel_bits_start ", sel_bits_start)
        print("adr_bits_start ", adr_bits_start)

        self.a_clkens = []

        if dual_port:
            self.b_addrs = []
            self.b_douts = []
            self.b_clkens = []

        # Combine RAMs to increase Depth.
        for d in range(self.depth_cascading):
            self.lram_blocks.append([])
            # Combine RAMs to increase Width.
            for w in range(self.width_cascading):
                datain  = Signal(32)
                dataout = Signal(32)
                cs      = Signal()
                wren    = Signal()

                if sel_bits > 0:
                    self.comb += [
                        datain.eq(self.bus.dat_w[32*w:32*(w+1)]),
                        If(self.bus.adr[sel_bits_start:sel_bits_start+sel_bits] == d,
                            cs.eq(1),
                            wren.eq(self.bus.we & self.bus.stb & self.bus.cyc),
                            self.bus.dat_r[32*w:32*(w+1)].eq(dataout)
                        ),
                    ]
                else:
                    self.comb += [
                        datain.eq(self.bus.dat_w[32*w:32*(w+1)]),
                        cs.eq(1),
                        wren.eq(self.bus.we & self.bus.stb & self.bus.cyc),
                        self.bus.dat_r[32*w:32*(w+1)].eq(dataout)
                    ]

                a_clken = Signal()
                if dual_port:
                    b_clken = Signal()
                    b_addr = Signal(14)
                    b_dout = Signal(32)
                    lram_block = Instance("DPSC512K",
                        p_ECC_BYTE_SEL = "BYTE_EN",
                        i_DIA       = datain,
                        i_ADA       = self.bus.adr[adr_bits_start:adr_bits_start+14],
                        i_CLK       = ClockSignal(),
                        i_CEA       = a_clken,
                        i_WEA       = wren,
                        i_CSA       = cs,
                        i_RSTA      = 0b0,
                        i_CEOUTA    = 0b0,
                        i_BENA_N    = ~self.bus.sel[4*w:4*(w+1)],
                        o_DOA       = dataout,
                        # port B read only
                        i_ADB       = b_addr,
                        o_DOB       = b_dout,
                        i_CEB       = b_clken,
                        i_WEB       = 0b0,
                        i_CSB       = 0b1,
                        i_RSTB      = 0b0,
                        i_CEOUTB    = 0b0
                    )
                    self.b_clkens.append(b_clken)
                    self.b_addrs.append(b_addr)
                    self.b_douts.append(b_dout)

                else:
                    lram_block = Instance("SP512K",
                        p_ECC_BYTE_SEL = "BYTE_EN",
                        i_DI       = datain,
                        i_AD       = self.bus.adr[adr_bits_start:adr_bits_start+14],
                        i_CLK      = ClockSignal(),
                        i_CE       = a_clken,
                        i_WE       = wren,
                        i_CS       = cs,
                        i_RSTOUT   = 0b0,
                        i_CEOUT    = 0b0,
                        i_BYTEEN_N = ~self.bus.sel[4*w:4*(w+1)],
                        o_DO       = dataout
                    )
                self.a_clkens.append(a_clken)

                self.lram_blocks[d].append(lram_block)
                self.specials += lram_block

        self.sync += self.bus.ack.eq(self.bus.stb & self.bus.cyc & ~self.bus.ack)

        if init != []:
            self.add_init(init)

    def add_init(self, data):
        # Pad it out to make slicing easier below.
        data += [0] * (self.size // self.width * 8 - len(data))
        for d in range(self.depth_cascading):
            for w in range(self.width_cascading):
                offset = d * self.width_cascading * 64*kB + w * 64*kB
                chunk = data[offset:offset + 64*kB]
                self.lram_blocks[d][w].items += initval_parameters(chunk, self.width)
