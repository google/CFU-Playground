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

"""Tests for hps_cfu.py"""


from amaranth.sim import Passive

from .constants import Constants
from .conv2d_data import fetch_data
from .hps_cfu import PoolInstruction, HpsCfu
from ..util import pack_vals
from ..cfu import CfuTestBase, InstructionTestBase
from functools import reduce


class PoolInstructionTest(InstructionTestBase):
    """Tests PoolInstruction class."""

    def create_dut(self):
        return PoolInstruction()

    def test_it(self):
        def p(a, b, c, d): return pack_vals(a, b, c, d, offset=-128)
        DATA = [
            (0, 0, 0),
            # min case
            (p(0, 0, 0, 0), p(0, 0, 0, 0), None),
            (p(0, 0, 0, 0), p(0, 0, 0, 0), p(0, 0, 0, 0)),
            # Max case
            (p(255, 255, 255, 255), p(255, 255, 255, 255), None),
            (p(255, 255, 255, 255), p(255, 255, 255, 255), p(255, 255, 255, 255)),
            # Arbitrary values
            (p(10, 20, 30, 40), p(50, 60, 70, 80), p(255, 255, 255, 255)),
            (p(10, 20, 30, 40), p(50, 60, 70, 80), p(50, 60, 70, 80)),
            (p(52, 37, 30, 40), p(12, 13, 34, 95), p(52, 60, 70, 95)),
            (p(51, 33, 30, 98), p(12, 13, 26, 90), p(52, 37, 34, 98)),            
            (p(251, 33, 30, 98), p(12, 13, 26, 90), p(251, 33, 30, 98)),            
            (p(0, 200, 0, 0), p(0, 0, 200, 0), p(251, 200, 200, 98)),
        ]

        self.verify(DATA, False)


class HpsCfuTest(CfuTestBase):
    """Tests HpsCfu class."""

    NUM_OUTPUT_PIXELS = 16
    RAM_BASE_ADDR = 0x1230

    def create_dut(self):
        return HpsCfu()

    @staticmethod
    def do_set(reg, val0, val1=0):
        return ((Constants.INS_SET, reg, val0, val1), None)

    @staticmethod
    def do_get(expected):
        return ((Constants.INS_GET, Constants.REG_OUTPUT_WORD, 0, 0), expected)

    def load_filter_data(self, data, chan_start, chan_count):
        """ Loads filter data for a range of output channels."""
        dims = data.filter_dims
        filter_data = data.filter_data
        num_filter_words_per_output = dims[1] * dims[2] * dims[3] // 4
        chan_data_index = chan_start * num_filter_words_per_output
        addr_base = 0

        for _ in range(0, chan_count, 2):
            for store in range(2):
                addr = addr_base
                for index in range(num_filter_words_per_output):
                    value = filter_data[chan_data_index]
                    chan_data_index += 1
                    yield self.do_set(Constants.REG_FILTER_WRITE,
                                      (store << 16 | addr), value)
                    addr += 1
            addr_base += num_filter_words_per_output

    def configure(self, data, output_chan_start, output_chan_count):
        # Configure the accelerator
        do_set = self.do_set
        C = Constants
        input_depth = data.input_dims[3]
        in_x_dim = data.input_dims[2]
        out_x_dim = data.output_dims[2]
        output_depth = data.output_dims[3]
        num_filter_values = (
            output_chan_count *
            data.filter_dims[1] *
            data.filter_dims[2] *
            data.filter_dims[3])
        # values / 4 = bytes then /2 to get per store
        filter_words_per_store = num_filter_values // 4 // 2

        # Set simple values
        yield do_set(C.REG_MODE, C.MODE_0 if input_depth == 1 else C.MODE_1)
        yield do_set(C.REG_INPUT_OFFSET, data.input_offset)
        yield do_set(C.REG_NUM_FILTER_WORDS, filter_words_per_store)
        yield do_set(C.REG_OUTPUT_OFFSET, data.output_offset)
        yield do_set(C.REG_OUTPUT_ACTIVATION_MIN, data.output_min)
        yield do_set(C.REG_OUTPUT_ACTIVATION_MAX, data.output_max)
        yield do_set(C.REG_INPUT_BASE_ADDR, self.RAM_BASE_ADDR)
        yield do_set(C.REG_NUM_PIXELS_X, out_x_dim)
        yield do_set(C.REG_PIXEL_ADVANCE_X, input_depth // 16)
        yield do_set(C.REG_PIXEL_ADVANCE_Y, (input_depth // 16) * in_x_dim)
        yield do_set(C.REG_INPUT_CHANNEL_DEPTH, input_depth)
        yield do_set(C.REG_OUTPUT_CHANNEL_DEPTH, output_chan_count)
        yield do_set(C.REG_NUM_OUTPUT_VALUES,
                     self.NUM_OUTPUT_PIXELS * output_chan_count)

        # Toggle reset
        yield do_set(C.REG_ACCELERATOR_RESET, 0)

        # load post process parameters
        for i in range(output_chan_count):
            index = i + output_chan_start
            yield do_set(C.REG_POST_PROCESS_BIAS, data.output_biases[index])
            # Note: shift is stored as a negative number in tflite model
            yield do_set(C.REG_POST_PROCESS_SHIFT, -data.output_shifts[index])
            yield do_set(C.REG_POST_PROCESS_MULTIPLIER,
                         data.output_multipliers[index])

        # Load filters
        yield from self.load_filter_data(data, output_chan_start,
                                         output_chan_count)

    def add_ram_process(self, data):
        """Adds logic for a RAM connected to the DUT."""
        def ram():
            yield Passive()
            while True:
                for i in range(4):
                    block = (yield self.dut.lram_addr[i])
                    data_addr = (block - self.RAM_BASE_ADDR // 16) * 4 + i
                    data_value = data.input_data[data_addr % len(
                        data.input_data)]
                    yield self.dut.lram_data[i].eq(data_value)
                yield
        self.add_process(ram)

    def test_simple_05(self):
        """Tests a 4x4 convolution producing 16 channels per start."""
        dut = self.dut
        data = fetch_data('sample_conv_05')

        self.add_ram_process(data)

        def process():
            # Configure, start accelerator
            yield from self.configure(data, 0, 16)
            yield self.do_set(Constants.REG_ACCELERATOR_START, 0)

            # Collect all of the output data for all pixels
            words_per_pixel = data.output_dims[3] // 4
            num_output_words = self.NUM_OUTPUT_PIXELS * words_per_pixel
            words_per_group = words_per_pixel * 4
            for i in range(num_output_words):
                group = i // words_per_group
                index_in_pixel = (i // 4) % words_per_pixel
                pixel_in_group = i % 4
                addr = (group * words_per_group +
                        pixel_in_group * words_per_pixel +
                        index_in_pixel)
                expected = data.expected_output_data[addr]
                yield self.do_get(expected)

        self.run_ops(process(), False)

    def test_simple_06(self):
        """Tests a 4x4 convolution over an input layer."""
        dut = self.dut
        data = fetch_data('sample_conv_06')

        self.add_ram_process(data)

        def process():
            # Configure, start accelerator
            yield from self.configure(data, 0, 16)
            yield self.do_set(Constants.REG_ACCELERATOR_START, 0)

            # Collect all of the output data for all pixels - output is in
            # groups of 2
            words_per_pixel = data.output_dims[3] // 4
            num_output_words = self.NUM_OUTPUT_PIXELS * words_per_pixel
            words_per_group = words_per_pixel * 2
            for i in range(num_output_words):
                group = i // words_per_group
                pixel_in_group = i % 2
                index_in_pixel = (i // 2) % words_per_pixel
                addr = (group * words_per_group +
                        pixel_in_group * words_per_pixel +
                        index_in_pixel)
                expected = data.expected_output_data[addr]
                yield self.do_get(expected)

        self.run_ops(process(), False)

    def test_groups_of_four(self):
        """Tests a 4x4 convolution producing 4 channels per start."""
        dut = self.dut
        data = fetch_data('sample_conv_05')

        self.add_ram_process(data)

        def process():
            # Configure, start accelerator
            output_depth = data.output_dims[3]
            for channel in range(0, output_depth, 4):
                yield from self.configure(data, channel, 4)
                yield self.do_set(Constants.REG_ACCELERATOR_START, 0)

                # Collect all of the output data for the pixels in this group
                words_per_pixel = output_depth // 4
                num_output_words = self.NUM_OUTPUT_PIXELS
                addr = channel // 4
                for word in range(num_output_words):
                    expected = data.expected_output_data[addr]
                    addr += words_per_pixel
                    yield self.do_get(expected)

        self.run_ops(process(), False)

    def test_pool(self):
        OPS = [
            ((Constants.INS_POOL, 0x80808080, 0x80808080), None),
            ((Constants.INS_POOL, 0x80808080, 0x80808080), 0x80808080),
            ((Constants.INS_POOL, 0x08030601, 0x04070205), 0x08070605),
            ((Constants.INS_POOL, 0x00660000, 0x00007700), 0x08667705),
        ]

        self.run_ops(OPS, False)
