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
from litex.soc.cores.clock.common import *

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

        if dual_port:
            self.b_addrs = []
            self.b_douts = []

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

                if dual_port:
                    b_addr = Signal(14)
                    b_dout = Signal(32)
                    lram_block = Instance("DPSC512K",
                        p_ECC_BYTE_SEL = "BYTE_EN",
                        i_DIA       = datain,
                        i_ADA       = self.bus.adr[adr_bits_start:adr_bits_start+14],
                        i_CLK       = ClockSignal(),
                        i_CEA       = 0b1,
                        i_WEA       = wren,
                        i_CSA       = cs,
                        i_RSTA      = 0b0,
                        i_CEOUTA    = 0b0,
                        i_BENA_N    = ~self.bus.sel[4*w:4*(w+1)],
                        o_DOA       = dataout,
                        # port B read only
                        i_ADB       = b_addr,
                        o_DOB       = b_dout,
                        i_CEB       = 0b1,
                        i_WEB       = 0b0,
                        i_CSB       = 0b1,
                        i_RSTB      = 0b0,
                        i_CEOUTB    = 0b0
                    )
                    self.b_addrs.append(b_addr)
                    self.b_douts.append(b_dout)

                else:
                    lram_block = Instance("SP512K",
                        p_ECC_BYTE_SEL = "BYTE_EN",
                        i_DI       = datain,
                        i_AD       = self.bus.adr[adr_bits_start:adr_bits_start+14],
                        i_CLK      = ClockSignal(),
                        i_CE       = 0b1,
                        i_WE       = wren,
                        i_CS       = cs,
                        i_RSTOUT   = 0b0,
                        i_CEOUT    = 0b0,
                        i_BYTEEN_N = ~self.bus.sel[4*w:4*(w+1)],
                        o_DO       = dataout
                    )
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


from collections import namedtuple
import logging
import pprint
from math import log10, pi
from cmath import phase

logging.basicConfig(level=logging.INFO)

io_i2 = namedtuple('io_i2',['io', 'i2', 'IPP_CTRL', 'BW_CTL_BIAS', 'IPP_SEL'])
nx_pll_param_permutation = namedtuple("nx_pll_param_permutation",[
                                "C1","C2","C3","C4","C5","C6",
                                "IPP_CTRL","BW_CTL_BIAS","IPP_SEL","CSET","CRIPPLE","V2I_PP_RES","IPI_CMP"])


# Lattice / NX PLL ---------------------------------------------------------------------------------

class NXPLL(Module):
    nclkouts_max        = 5
    clki_div_range      = ( 1, 128+1)
    clkfb_div_range     = ( 1, 128+1)
    clko_div_range      = ( 1, 128+1)
    clki_freq_range     = ( 10e6,   500e6)
    clko_freq_range     = ( 6.25e6, 800e6)
    vco_in_freq_range   = ( 10e6,   500e6)
    vco_out_freq_range  = ( 800e6,  1600e6)
    instance_num        = 0

    def __init__(self, platform = None, create_output_port_clocks=False):
        self.logger = logging.getLogger("NXPLL")
        self.logger.info("Creating NXPLL.")
        self.params     = {}
        self.reset      = Signal()
        self.locked     = Signal()
        self.params["o_LOCK"] = self.locked
        self.clkin_freq = None
        self.vcxo_freq  = None
        self.nclkouts   = 0
        self.clkouts    = {}
        self.config     = {}
        self.name       = 'PLL_' + str(NXPLL.instance_num)
        NXPLL.instance_num += 1
        self.platform   = platform
        self.create_output_port_clocks = create_output_port_clocks

        self.calc_valid_io_i2()
        self.calc_tf_coefficients()

    def register_clkin(self, clkin, freq):
        (clki_freq_min, clki_freq_max) = self.clki_freq_range
        assert freq >= clki_freq_min
        assert freq <= clki_freq_max
        self.clkin = Signal()
        if isinstance(clkin, (Signal, ClockSignal)):
            self.comb += self.clkin.eq(clkin)
        else:
            raise ValueError
        self.clkin_freq = freq
        register_clkin_log(self.logger, clkin, freq)

    def create_clkout(self, cd, freq, phase=0, margin=1e-2):
        (clko_freq_min, clko_freq_max) = self.clko_freq_range
        assert freq >= clko_freq_min
        assert freq <= clko_freq_max
        assert self.nclkouts < self.nclkouts_max
        self.clkouts[self.nclkouts] = (cd.clk, freq, phase, margin)
        create_clkout_log(self.logger, cd.name, freq, margin, self.nclkouts)
        self.nclkouts += 1

    def compute_config(self):
        config = {}
        for clki_div in range(*self.clki_div_range):
            config["clki_div"] = clki_div
            for clkfb_div in range(*self.clkfb_div_range):
                all_valid = True
                vco_freq = self.clkin_freq/clki_div*clkfb_div
                (vco_freq_min, vco_freq_max) = self.vco_out_freq_range
                if vco_freq >= vco_freq_min and vco_freq <= vco_freq_max:
                    for n, (clk, f, p, m) in sorted(self.clkouts.items()):
                        valid = False
                        for d in range(*self.clko_div_range):
                            clk_freq = vco_freq/d
                            if abs(clk_freq - f) <= f*m:
                                config["clko{}_freq".format(n)]  = clk_freq
                                config["clko{}_div".format(n)]   = d
                                config["clko{}_phase".format(n)] = p
                                valid = True
                                break
                        if not valid:
                            all_valid = False
                else:
                    all_valid = False
                if all_valid:
                    config["vco"] = vco_freq
                    config["clkfb_div"] = clkfb_div
                    compute_config_log(self.logger, config)
                    return config
        raise ValueError("No PLL config found")

    def calculate_analog_parameters(self, clki_freq, fb_div, bw_factor = 5):
        config = {}

        params = self.calc_optimal_params(clki_freq, fb_div, 1, bw_factor)
        config["p_CSET"]            = params["CSET"]
        config["p_CRIPPLE"]         = params["CRIPPLE"]
        config["p_V2I_PP_RES"]      = params["V2I_PP_RES"]
        config["p_IPP_SEL"]         = params["IPP_SEL"]
        config["p_IPP_CTRL"]        = params["IPP_CTRL"]
        config["p_BW_CTL_BIAS"]     = params["BW_CTL_BIAS"]
        config["p_IPI_CMP"]         = params["IPI_CMP"]

        return config

    def do_finalize(self):
        config = self.compute_config()
        clkfb  = Signal()

        self.params.update(
            p_V2I_PP_ICTRL      = "0b11111", # Hard coded in all reference files
            p_IPI_CMPN          = "0b0011", # Hard coded in all reference files

            p_V2I_1V_EN         = "ENABLED", # Enabled = 1V (Default in references, but not the primitive), Disabled = 0.9V
            p_V2I_KVCO_SEL      = "60", # if (VOLTAGE == 0.9V) 85 else 60
            p_KP_VCO            = "0b00011", # if (VOLTAGE == 0.9V) 0b11001 else 0b00011

            p_PLLPD_N           = "USED",
            p_PLLRESET_ENA      = "ENABLED",
            p_REF_INTEGER_MODE  = "ENABLED", # Ref manual has a discrepency so lets always set this value just in case
            p_REF_MMD_DIG       = "1", # Divider for the input clock, ie 'M'

            i_PLLRESET          = self.reset,
            i_REFCK             = self.clkin,
            o_LOCK              = self.locked,

            # Use CLKOS5 & divider for feedback
            p_SEL_FBK           = "FBKCLK5",
            p_ENCLK_CLKOS5      = "ENABLED",
            p_DIVF              = str(config["clkfb_div"]-1), # str(Actual value - 1)
            p_DELF              = str(config["clkfb_div"]-1),
            p_CLKMUX_FB         = "CMUX_CLKOS5",
            i_FBKCK             = clkfb,
            o_CLKOS5            = clkfb,

            # Set feedback divider to 1
            p_FBK_INTEGER_MODE  = "ENABLED",
            p_FBK_MASK          = "0b00000000",
            p_FBK_MMD_DIG       = "1",
        )

        analog_params = self.calculate_analog_parameters(self.clkin_freq, config["clkfb_div"])
        self.params.update(analog_params)
        n_to_l = {0: "P", 1: "S", 2: "S2", 3:"S3", 4:"S4"}

        for n, (clk, f, p, m) in sorted(self.clkouts.items()):
            div    = config["clko{}_div".format(n)]
            phase = int((1+p/360) * div)
            letter = chr(n+65)
            self.params["p_ENCLK_CLKO{}".format(n_to_l[n])] = "ENABLED"
            self.params["p_DIV{}".format(letter)] = str(div-1)
            self.params["p_PHI{}".format(letter)] = "0"
            self.params["p_DEL{}".format(letter)] = str(phase - 1)
            self.params["o_CLKO{}".format(n_to_l[n])] = clk

            # In theory this really shouldn't be necessary, in practice
            # the tooling seems to have suspicous clock latency values
            # on generated clocks that are causing timing problems and Lattice
            # hasn't responded to my support requests on the matter.
            if self.platform and self.create_output_port_clocks:
                self.platform.add_platform_command("create_clock -period {} -name {} [get_pins {}.PLL_inst/CLKO{}]".format(str(1/f*1e9), self.name + "_" + n_to_l[n],self.name, n_to_l[n]))

        if self.platform and self.create_output_port_clocks:
            i = 0
        self.specials += Instance("PLL", name = self.name, **self.params)

    # The gist of calculating the analog parameters is to run through all the
    # permutations of the parameters and find the optimum set of values based
    # on the transfer function of the PLL loop filter. There are constraints on
    # on a few specific parameters, the open loop transfer function, and the closed loop
    # transfer function. An optimal solution is chosen based on the bandwidth
    # of the response relative to the input reference frequency of the PLL.

    # Later revs of the Lattice calculator BW_FACTOR is set to 10, may need to change it
    def calc_optimal_params(self, fref, fbkdiv, M = 1, BW_FACTOR = 5):
        print("Calculating Analog Paramters for a reference freqeuncy of " + str(fref*1e-6) +
              " Mhz, feedback div " + str(fbkdiv) + ", and input div " + str(M) + "."
        )

        best_params = None
        best_3db = 0

        for params in self.transfer_func_coefficients:
            closed_loop_peak = self.closed_loop_peak(fbkdiv, params)
            if (closed_loop_peak["peak"] < 0.8 or
               closed_loop_peak["peak"] > 1.35):
                continue

            open_loop_crossing = self.open_loop_crossing(fbkdiv, params)
            if open_loop_crossing["phase"] <= 45:
                continue

            closed_loop_3db = self.closed_loop_3db(fbkdiv, params)
            bw_factor = fref*1e6 / M / closed_loop_3db["f"]
            if bw_factor < BW_FACTOR:
                continue

            if best_3db < closed_loop_3db["f"]:
                best_3db = closed_loop_3db["f"]
                best_params = params

        print("Done calculating analog parameters:")
        HDL_params = self.numerical_params_to_HDL_params(best_params)
        pprint.pprint(HDL_params)

        return HDL_params


    def numerical_params_to_HDL_params(self, params):
        IPP_SEL_LUT = {1: 1, 2: 3, 3: 7, 4: 15}
        ret = {
            "CRIPPLE": str(int(params.CRIPPLE / 1e-12)) + "P",
            "CSET": str(int((params.CSET / 4e-12)*4)) + "P",
            "V2I_PP_RES": "{0:g}".format(params.V2I_PP_RES/1e3).replace(".","P") + "K",
            "IPP_CTRL": "0b{0:04b}".format(int(params.IPP_CTRL / 1e-6 + 3)),
            "IPI_CMP": "0b{0:04b}".format(int(params.IPI_CMP / .5e-6)),
            "BW_CTL_BIAS": "0b{0:04b}".format(params.BW_CTL_BIAS),
            "IPP_SEL": "0b{0:04b}".format(IPP_SEL_LUT[params.IPP_SEL]),
        }

        return ret

    def calc_valid_io_i2(self):
        # Valid permutations of IPP_CTRL, BW_CTL_BIAS, IPP_SEL, and IPI_CMP paramters are constrained
        # by the following equation so we can narrow the problem space by calculating the
        # them early in the process.
        # ip = 5.0/3 * ipp_ctrl*bw_ctl_bias*ipp_sel
        # ip/ipi_cmp == 50 +- 1e-4

        self.valid_io_i2_permutations = []

        # List out the valid values of each parameter
        IPP_CTRL_VALUES = range(1,4+1)
        IPP_CTRL_UNITS = 1e-6
        IPP_CTRL_VALUES = [element * IPP_CTRL_UNITS for element in IPP_CTRL_VALUES]
        BW_CTL_BIAS_VALUES = range(1,15+1)
        IPP_SEL_VALUES = range(1,4+1)
        IPI_CMP_VALUES = range(1,15+1)
        IPI_CMP_UNITS = 0.5e-6
        IPI_CMP_VALUES = [element * IPI_CMP_UNITS for element in IPI_CMP_VALUES]

        for IPP_CTRL in IPP_CTRL_VALUES:
            for BW_CTL_BIAS in BW_CTL_BIAS_VALUES:
                for IPP_SEL in IPP_SEL_VALUES:
                    for IPI_CMP in IPI_CMP_VALUES:
                        is_valid_io_i2 = self.is_valid_io_i2(IPP_CTRL, BW_CTL_BIAS, IPP_SEL, IPI_CMP)
                        if is_valid_io_i2 and self.is_unique_io(is_valid_io_i2['io']):
                            self.valid_io_i2_permutations.append( io_i2(
                                is_valid_io_i2['io'], is_valid_io_i2['i2'],
                                IPP_CTRL, BW_CTL_BIAS, IPP_SEL
                            ) )

    def is_unique_io(self, io):
        return not any(x.io == io for x in self.valid_io_i2_permutations)

    def is_valid_io_i2(self, IPP_CTRL, BW_CTL_BIAS, IPP_SEL, IPI_CMP):
        tolerance = 1e-4
        ip = 5.0/3.0 * IPP_CTRL * BW_CTL_BIAS * IPP_SEL
        i2 = IPI_CMP
        if abs(ip/i2-50) < tolerance:
            return {'io':ip,'i2':i2}
        else:
            return False

    def calc_tf_coefficients(self):
        # Take the permutations of the various analog parameters
        # then precalculate the coefficients of the transfer function.
        # During the final calculations sub in the feedback divisor
        # to get the final transfer functions.

        #       (ABF+EC)s^2 + (A(F(G+1)+B) + ED)s + A(G+1)          C1s^s + C2s + C3
        # tf = -------------------------------------------- =  --------------------------
        #               ns^2(CFs^2 + (DF+C)s + D)                ns^2(C4s^2 + C5s + C6)

        # A = i2*g3*ki
        # B = r1*c3
        # C = B*c2
        # D = c2+c3
        # E = io*ki*k1
        # F = r*cs
        # G = k3
        # n = total divisor of the feedback signal (output + N)

        # Constants
        c3 = 20e-12
        g3 = 0.2952e-3
        k1 = 6
        k3 = 100
        ki = 508e9
        r1 = 9.8e6
        B = r1*c3

        # PLL Parameters
        CSET_VALUES = range(2,17+1)
        CSET_UNITS = 4e-12
        CSET_VALUES = [element * CSET_UNITS for element in CSET_VALUES]
        CRIPPLE_VALUES = [1, 3, 5, 7, 9, 11, 13, 15]
        CRIPPLE_UNITS = 1e-12
        CRIPPLE_VALUES = [element * CRIPPLE_UNITS for element in CRIPPLE_VALUES]
        V2I_PP_RES_VALUES = [9000, 9300, 9700, 10000, 10300, 10700, 11000, 11300]

        self.transfer_func_coefficients = []

        # Run through all the permutations and cache it all
        for io_i2 in self.valid_io_i2_permutations:
            for CSET in CSET_VALUES:
                for CRIPPLE in CRIPPLE_VALUES:
                    for V2I_PP_RES in V2I_PP_RES_VALUES:
                        A = io_i2.i2*g3*ki
                        B = r1*c3
                        C = B*CSET
                        D = CSET+c3
                        E = io_i2.io*ki*k1
                        F = V2I_PP_RES*CRIPPLE
                        G = k3

                        self.transfer_func_coefficients.append( nx_pll_param_permutation(
                            A*B*F+E*C, # C1
                            A*(F*(G+1)+B)+E*D, # C2
                            A*(G+1), # C3
                            C*F, # C4
                            D*F+C, # C5
                            D, # C6
                            io_i2.IPP_CTRL, io_i2.BW_CTL_BIAS, io_i2.IPP_SEL,
                            CSET, CRIPPLE, V2I_PP_RES, io_i2.i2
                        ))

    def calc_tf(self, n, s, params):
        return ( (params.C1 * s ** 2 + params.C2 * s + params.C3) /
                ( n * s ** 2 * (params.C4 * s ** 2 + params.C5 * s + params.C6) ) )

    def closed_loop_peak(self, fbkdiv, params):
        f = 1e6
        step = 1.1
        step_divs = 0

        peak_value = -99
        peak_f = 0

        last_value = -99

        while f < 1e9:
            s = 1j * 2 * pi * f
            tf_value = self.calc_tf(fbkdiv, s, params)
            this_result = 20*log10(abs(tf_value/(1+tf_value)))
            if this_result > peak_value:
                peak_value = this_result
                peak_f = f

            if this_result < last_value and step_divs < 5:
                f = f/(step**2)
                step = (step - 1) * .5 + 1
                step_divs = step_divs + 1
            elif this_result < last_value and step_divs == 5:
                break
            else:
                last_value = this_result
                f = f * step

        return {"peak":peak_value, "peak_freq":peak_f}

    def closed_loop_3db(self, fbkdiv, params):
        f = 1e6
        step = 1.1
        step_divs = 0

        last_f = 1

        while f < 1e9:
            s = 1j * 2 * pi * f
            tf_value = self.calc_tf(fbkdiv, s, params)
            this_result = 20*log10(abs(tf_value/(1+tf_value)))

            if (this_result+3) < 0 and step_divs < 5:
                f = last_f
                step = (step - 1) * .5 + 1
                step_divs = step_divs + 1
            elif (this_result+3) < 0 and step_divs == 5:
                break
            else:
                last_f = f
                f = f * step

        return {"f":last_f}

    def open_loop_crossing(self, fbkdiv, params):
        f = 1e6
        step = 1.1
        step_divs = 0

        last_f = 1
        last_tf = 0

        while f < 1e9:
            s = 1j * 2 * pi * f
            tf_value = self.calc_tf(fbkdiv, s, params)
            this_result = 20*log10(abs(tf_value))

            if this_result < 0 and step_divs < 5:
                f = last_f
                step = (step - 1) * .5 + 1
                step_divs = step_divs + 1
            elif this_result < 0 and step_divs == 5:
                break
            else:
                last_f = f
                last_tf = tf_value
                f = f * step

        return {"f":last_f, "phase":phase(-last_tf)*180/pi}
