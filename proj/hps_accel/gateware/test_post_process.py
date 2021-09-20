#!/bin/env python
# Copyright 2021 Google LLC
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

import random

from nmigen.sim import Delay
from nmigen_cfu import TestBase

from .post_process import (SaturatingRoundingDoubleHighMul, RoundingDivideByPowerOfTwo,
                           OutputParamsStorage, SaturateActivationPipeline,
                           PostProcessPipeline)


# Test cases generated from original C implementation
# See do_generated_srdhm() in proj_menu.cc
_SRDHM_TEST_CASES = [
    # a (value), b (quantized_multipler), expected result
    (76199, 1799162196, 63840),
    (-45918, 1999098553, -42745),
    (113093, 1673911861, 88153),
    (-103077, 1190764262, -57155),
    (-34232, 1477988098, -23560),
    (-59473, 1648902784, -45665),
    (120827, 1885389667, 106080),
    (-24191, 1473168262, -16595),
    (-56185, 1776203374, -46471),
    (113562, 2052420060, 108535),
    (47666, 1729231925, 38382),
    (27430, 1975945832, 25239),
    (-111628, 1393592893, -72440),
    (41103, 1818749429, 34811),
    (41380, 1274616254, 24561),
    (4902, 1678418407, 3831),
    (61765, 1287000734, 37016),
    (-36200, 1442403925, -24315),
    (-105187, 1197488585, -58655),
    (71639, 1565520041, 52225),
    (-33258, 1595957788, -24717),
    (39689, 1423886284, 26316),
    (-100633, 1760419674, -82495),
    (116562, 1802734351, 97850),
    (92914, 1092090772, 47251),
    (82883, 1734861670, 66958),
    (57166, 1912255582, 50904),
    (75346, 1992033070, 69892),
    (-83656, 1632785000, -63606),
    (63200, 1405592453, 41366),
    (-49318, 1200228270, -27564),
    (8275, 1673124755, 6447),
    (85644, 1737222681, 69282),
    (-40597, 1547023683, -29246),
    (-31909, 1336729220, -19862),
    (45454, 1206552787, 25538),
    (4972, 1266032220, 2931),
    (-19512, 2057461827, -18694),
    (235, 1953821820, 214),
    (61300, 1720881690, 49123),
    (68229, 1809146070, 57479),
    (36454, 1576160004, 26756),
    (-110586, 1428097357, -73541),
    (-96195, 1951204560, -87403),
    (92792, 1304886675, 56384),
    (89436, 1880314336, 78309),
    (82646, 1272078154, 48956),
    (34372, 2116064125, 33869),
    (-59501, 1664891747, -46130),
    (-99939, 1852312277, -86202),
    (-3113, 1145983455, -1661),
    (55215, 1880447994, 48349),
    (110403, 1113321777, 57236),
    (23116, 1570010167, 16900),
    (-2583, 1227779863, -1477),
    (85789, 1222210857, 48826),
    (-87366, 1102802313, -44865),
    (-27417, 1228124265, -15680),
    (-47617, 1998685012, -44318),
    (34293, 2140014655, 34174),
    (-3452, 1967903050, -3163),
    (-41255, 1543279806, -29648),
    (-19972, 1855490651, -17256),
    (-115484, 1944772033, -104583),
    (-94052, 1568785104, -68707),
    (-84195, 1542010281, -60457),
    (64620, 1444904141, 43479),
    (35658, 1729292906, 28714),
    (683, 1605542539, 511),
    (86664, 1218739791, 49184),
    (71854, 1825797432, 61090),
    (-40430, 1850313723, -34835),
    (517, 1207184966, 291),
    (55659, 1935689127, 50170),
    (-102608, 1649388495, -78809),
    (-91465, 1271253544, -54145),
    (-103661, 1745470500, -84255),
    (63765, 2060859198, 61193),
    (-53913, 1862618106, -46761),
    (-264, 1521947588, -187),
    (82360, 2082814599, 79880),
    (81899, 1529235916, 58321),
    (-116459, 1985030873, -107649),
    (-103947, 1102943297, -53387),
    (107625, 2139653618, 107233),
    (-86358, 1343644072, -54033),
    (-101746, 2111171020, -100026),
    (87873, 1815044516, 74270),
    (-11397, 1148791307, -6097),
    (23925, 1534599501, 17097),
    (-31358, 1488524351, -21736),
    (59542, 1645438751, 45622),
    (-113056, 1116124901, -58759),
    (-96429, 1975242245, -88695),
    (39948, 1483623346, 27599),
    (106175, 2119373911, 104785),
    (-123803, 1139955622, -65719),
    (115382, 1116312282, 59978),
    (56207, 1758239044, 46019),
    (46695, 1104444813, 24015),
    (-12552, 1170510491, -6842),
]


class SaturatingRoundingDoubleHighMulTest(TestBase):
    def create_dut(self):
        return SaturatingRoundingDoubleHighMul()

    def test_it_calculates_correctly(self):
        def process():
            yield self.dut.output.ready.eq(1)
            for (a, b, expected) in _SRDHM_TEST_CASES:
                yield self.dut.input.payload.a.eq(a)
                yield self.dut.input.payload.b.eq(b)
                yield self.dut.input.valid.eq(1)
                yield
                yield self.dut.input.valid.eq(0)
                yield  # 3 cycles to process
                yield
                yield
                self.assertTrue((yield self.dut.output.valid))
                self.assertEqual((yield self.dut.output.payload), expected)

        self.run_sim(process, False)


# Test cases generated from original C implementation
# See do_generated_rdbpot() in proj_menu.cc
_RDBPOT_TEST_CASES = [
    # dividend, shift, expected result
    (8, 3, 1),
    (11, 3, 1),
    (12, 3, 2),
    (13, 3, 2),
    (-8, 3, -1),
    (-11, 3, -1),
    (-12, 3, -2),
    (-13, 3, -2),
    (-981784153, 7, -7670189),
    (37047458, 4, 2315466),
    (2036578757, 8, 7955386),
    (-225940133, 9, -441289),
    (-1322943928, 5, -41341998),
    (-1240393809, 3, -155049226),
    (-1482696709, 6, -23167136),
    (1895670145, 9, 3702481),
    (-1797446521, 9, -3510638),
    (1338227610, 7, 10454903),
    (735492658, 8, 2873018),
    (-1516082394, 3, -189510299),
    (970476532, 8, 3790924),
    (2022088847, 8, 7898785),
    (448176548, 9, 875345),
    (-1142287578, 10, -1115515),
    (-1066995387, 9, -2083975),
    (221868696, 8, 866675),
    (804283677, 4, 50267730),
    (-1501095977, 4, -93818499),
    (-1543668202, 7, -12059908),
    (-1937335543, 7, -15135434),
    (1281914599, 5, 40059831),
    (698337106, 10, 681970),
    (1381460722, 7, 10792662),
    (-1589427261, 9, -3104350),
    (-1455759538, 9, -2843280),
    (1015490130, 9, 1983379),
    (981252408, 3, 122656551),
    (1432286944, 8, 5594871),
    (1343045466, 9, 2623136),
    (94511187, 6, 1476737),
    (1101483660, 4, 68842729),
    (-951492245, 6, -14867066),
    (-942046373, 7, -7359737),
    (871543182, 6, 13617862),
    (226890604, 7, 1772583),
    (-1791380536, 6, -27990321),
    (-2076049173, 7, -16219134),
    (-1062277260, 5, -33196164),
    (-881128827, 9, -1720955),
    (1577750118, 7, 12326173),
    (132927494, 8, 519248),
    (-1004500931, 3, -125562616),
    (595552888, 6, 9305514),
    (-415802020, 3, -51975253),
    (-844938538, 5, -26404329),
    (-1583708604, 8, -6186362),
    (228923283, 6, 3576926),
    (-2050721379, 8, -8010630),
    (-1486228521, 10, -1451395),
    (1181669295, 5, 36927165),
    (-687362237, 4, -42960140),
    (424303180, 10, 414359),
    (126481897, 10, 123517),
    (21188381, 4, 1324274),
    (-323441990, 4, -20215124),
    (734893287, 4, 45930830),
    (-2125642241, 7, -16606580),
    (-842627595, 10, -822879),
    (18477700, 5, 577428),
    (-145662247, 9, -284497),
    (584167932, 6, 9127624),
    (442514660, 4, 27657166),
    (-327118692, 3, -40889837),
    (771274525, 4, 48204658),
    (914816108, 8, 3573500),
    (-1713468598, 5, -53545894),
    (-1188166997, 6, -18565109),
    (1474515592, 10, 1439957),
    (-1698490194, 3, -212311274),
    (-1138662894, 6, -17791608),
    (-1425931771, 9, -2785023),
    (-2121344661, 10, -2071626),
    (-2085064912, 10, -2036196),
    (-768566601, 3, -96070825),
    (-1391957229, 7, -10874666),
    (1328740629, 9, 2595197),
    (-179229337, 5, -5600917),
    (-1714553096, 7, -13394946),
    (1686585784, 10, 1647056),
    (-2145435669, 7, -16761216),
    (374356245, 4, 23397265),
    (709126645, 4, 44320415),
    (-1765825431, 5, -55182045),
    (-1788563798, 3, -223570475),
    (770470542, 7, 6019301),
    (-1044424895, 7, -8159569),
    (-1971203205, 6, -30800050),
    (-405119627, 8, -1582499),
    (1681229186, 10, 1641825),
    (1269491862, 10, 1239738),
    (1766868576, 8, 6901830),
    (-1415280813, 8, -5528441),
    (1900190732, 5, 59380960),
    (994811583, 10, 971496),
    (1198005349, 9, 2339854),
    (2107622070, 5, 65863190),
    (918739855, 7, 7177655),
    (1639364199, 8, 6403766),
    (-6842, 8, -27),
]


class RoundingDivideByPowerOfTwoTest(TestBase):
    def create_dut(self):
        return RoundingDivideByPowerOfTwo()

    def test_it_calculates_correctly(self):
        def process():
            yield self.dut.output.ready.eq(1)
            for dividend, shift, expected in _RDBPOT_TEST_CASES:
                yield self.dut.input.payload.dividend.eq(dividend)
                yield self.dut.input.payload.shift.eq(shift)
                yield self.dut.input.valid.eq(1)
                yield
                yield self.dut.input.valid.eq(0)
                yield  # 3 cycles to process
                yield
                yield
                self.assertTrue((yield self.dut.output.valid))
                self.assertEqual((yield self.dut.output.payload), expected)

        self.run_sim(process, False)


class OutputParamsStorageTest(TestBase):
    def create_dut(self):
        return OutputParamsStorage()

    def set_write_data(self, seed):
        """Given a seed, randomly set write_data"""
        random.seed(seed)
        data = self.dut.write_data
        yield data.bias.eq(random.randrange(-(2**15), 2**15))
        yield data.multiplier.eq(random.randrange(0x4000_0000, 0x8000_0000))
        yield data.shift.eq(random.randrange(4, 11))

    def write(self, seed):
        yield from self.set_write_data(seed)
        yield self.dut.write_enable.eq(1)
        yield
        yield self.dut.write_enable.eq(0)
        yield

    def check_read_data(self, seed):
        """Given a seed, check that it matches record generated from same seeed"""
        random.seed(seed)
        data = self.dut.read_data
        self.assertEqual((yield data.bias), random.randrange(-(2**15), 2**15))
        self.assertEqual((yield data.multiplier), random.randrange(0x4000_0000, 0x8000_0000))
        self.assertEqual((yield data.shift), random.randrange(4, 11))

    def check_read(self, seed):
        yield self.dut.read_enable.eq(1)
        yield
        yield self.dut.read_enable.eq(0)
        yield
        yield from self.check_read_data(seed)

    def test_it_works(self):
        """Set 8 numbers and read them back"""
        def process():
            for n in range(8):
                yield from self.write(n)
            for n in range(8):
                yield from self.check_read(n)
        self.run_sim(process, False)

    def test_it_reads_multiple_times(self):
        """Set 16 numbers and read them back many times"""
        def process():
            for n in range(8, 24):
                yield from self.write(n)
            for n in range(8, 24):
                yield from self.check_read(n)
            for n in range(8, 24):
                yield from self.check_read(n)
            for n in range(8, 24):
                yield from self.check_read(n)
        self.run_sim(process, False)

    def test_it_can_be_reset(self):
        """Show store can be reset and reused."""
        def process():
            for n in range(20, 28):
                yield from self.write(n)
            for n in range(20, 28):
                yield from self.check_read(n)

            yield self.dut.reset.eq(1)
            yield
            yield self.dut.reset.eq(0)
            yield

            for n in range(120, 128):
                yield from self.write(n)
            for n in range(120, 128):
                yield from self.check_read(n)
        self.run_sim(process, False)


class SaturateActivationPipelineTest(TestBase):
    """Tests the SaturateActivationPipeline"""

    def create_dut(self):
        return SaturateActivationPipeline()

    def test_it_works(self):
        """Show store can be reset and reused."""
        TEST_CASES = [
            # (offset, min, max, input), expected result
            ((0, 0, 0, 0), 0),
            ((-128, -128, 127, 0), -128),
            ((-128, -128, 127, 10), -118),
            ((-128, -128, 127, -50), -128),
            ((-128, -128, 127, 500), 127),
        ]

        def process():
            yield self.dut.output.ready.eq(1)
            for (offset, min, max, input_), expected in TEST_CASES:
                yield self.dut.offset.eq(offset)
                yield self.dut.min.eq(min)
                yield self.dut.max.eq(max)
                yield
                yield self.dut.input.payload.eq(input_)
                yield self.dut.input.valid.eq(1)
                yield
                yield self.dut.input.valid.eq(0)
                while not (yield self.dut.output.valid):
                    yield
                self.assertEqual((yield self.dut.output.payload), expected)
        self.run_sim(process, False)


class PostProcessPipelineTest(TestBase):
    """Tests the entire post process pipeline"""

    def create_dut(self):
        return PostProcessPipeline()

    def test_it_works(self):
        TEST_CASES = [
            # ((acc_in,bias,multiplier,shift), expected)
            ((-15150, 2598, 1170510491, 8), -128),
            ((-432, 2193, 2082838296, 9), -125),
            ((37233, -18945, 1368877765, 9), -105),
            ((-294, 1851, 1661334583, 8), -123),
            ((3908, 1994, 1384690194, 8), -113),
            ((153, 1467, 1177612918, 8), -125),
        ]

        def process():
            yield self.dut.output.ready.eq(1)
            yield self.dut.offset.eq(-128)
            yield self.dut.activation_min.eq(-128)
            yield self.dut.activation_max.eq(127)
            yield
            for (acc_in, bias, multiplier, shift), expected in TEST_CASES:
                self.assertEqual((yield self.dut.read_strobe), 0)
                yield self.dut.read_data.bias.eq(bias)
                yield self.dut.read_data.multiplier.eq(multiplier)
                yield self.dut.read_data.shift.eq(shift)
                yield self.dut.input.payload.eq(acc_in)
                yield self.dut.input.valid.eq(1)
                yield
                self.assertEqual((yield self.dut.read_strobe), 1)
                yield self.dut.input.valid.eq(0)
                while not (yield self.dut.output.valid):
                    yield
                self.assertEqual((yield self.dut.output.payload), expected)
        self.run_sim(process, False)
