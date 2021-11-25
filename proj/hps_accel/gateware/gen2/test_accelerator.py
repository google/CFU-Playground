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

"""Tests for accelerator.py"""

import random

from nmigen import unsigned, signed

from nmigen_cfu import pack_vals, TestBase

from .accelerator import AcceleratorCore
from .constants import Constants
from .conv2d_data import fetch_data


def unpack_bytes(word):
    """Unpacks a 32 bit word into 4 signed byte length values."""
    def as_8bit_signed(val):
        val = val & 0xff
        return val if val < 128 else val - 256
    return (as_8bit_signed(word),
            as_8bit_signed(word >> 8),
            as_8bit_signed(word >> 16),
            as_8bit_signed(word >> 24))


def group(list_, size):
    """Separate list into sublists of size size"""
    return [list_[i:i + size] for i in range(0, len(list_), size)]


def flatten(list_of_lists):
    """Single level flattening of a list."""
    return sum((list(sublist) for sublist in list_of_lists), [])


class AcceleratorCoreTest(TestBase):
    """Tests AcceleratorCore"""

    def create_dut(self):
        return AcceleratorCore()

    def setUp(self):
        super().setUp()
        self.data = fetch_data('sample_conv_1')

    def extract_filter_data(self):
        # Splits filter data into "evens" and "odds" for the two columns of the
        # systolic array.
        dims = self.data.filter_dims
        filter_data = self.data.filter_data
        # Group by words that are used to calculate a single output value
        num_filters_per_output = dims[1] * dims[2] * dims[3]
        filters_by_output = group(filter_data, num_filters_per_output // 4)
        # Split into two sets of groups
        evens, odds = filters_by_output[::2], filters_by_output[1::2]
        return flatten(evens), flatten(odds)

    @staticmethod
    def activation_address_generator(*,
                                     base_addr, repeats, inter_pixel_stride,
                                     fetch_num_rows, inter_row_stride,
                                     fetch_words_per_row, debug=0):
        # Specifies addresses of data to be streamed into the accelerator
        # via the "activations" attribute. Designed to allow all values
        # from a 4x4 region of input pixels to be fetched in the correct
        # order.
        while True:
            for _ in range(repeats):
                row_start = base_addr
                for _ in range(fetch_num_rows):
                    addr = row_start
                    for _ in range(fetch_words_per_row):
                        if debug:
                            print(f"Channel 1 yield {addr}")
                        yield addr
                        addr += 1
                    row_start += inter_row_stride
                debug = False
            base_addr += inter_pixel_stride

    @staticmethod
    def apply_input_offset(word):
        with_offset = [byte + data.input_offset for byte in unpack_bytes(word)]
        return pack_vals(*unpack_bytes(word), offset=input_offset)

    def configure(self):
        # Configure the accelerator
        dut = self.dut
        data = self.data
        depth = data.output_dims[3]
        yield dut.half.eq(0)
        yield dut.input_offset.eq(data.input_offset)
        yield dut.output_offset.eq(data.output_offset)
        yield dut.output_activation_min.eq(data.output_min)
        yield dut.output_activation_max.eq(data.output_max)

        yield dut.post_process_sizes.depth.eq(depth)
        yield dut.post_process_sizes.repeats.eq(Constants.SYS_ARRAY_HEIGHT)
        for i in range(depth):
            payload = dut.post_process_params.payload
            yield payload.bias.eq(data.output_biases[i])
            yield payload.multiplier.eq(data.output_multipliers[i])
            # Note: shift is stored as a negative number in tflite model
            yield payload.shift.eq(-data.output_shifts[i])
            yield dut.post_process_params.valid.eq(1)
            yield
        yield dut.post_process_params.valid.eq(0)
        yield

    def test_convolution(self):
        # tests part of a convolution, producing results for 16 output pixels
        # uses data dumped from a real convolution
        dut = self.dut
        data = self.data
        filter_even, filter_odd = self.extract_filter_data()

        def feed_dut():
            # Toggle reset
            yield dut.reset.eq(1)
            yield
            yield dut.reset.eq(0)

            # Configure
            yield from self.configure()
            input_depth = data.filter_dims[3]
            input_depth_words = input_depth // 4
            filter_size = data.filter_dims[1] * data.filter_dims[2]
            output_depth = data.filter_dims[0]

            # Addresses of inputs within input activation buffer
            activation_addr = [
                self.activation_address_generator(
                    base_addr=i * input_depth_words,
                    repeats=output_depth // 2,
                    inter_pixel_stride=input_depth_words * 4,  # Stride 4 pixels along
                    fetch_num_rows=4,
                    inter_row_stride=data.input_dims[2] *
                    data.input_dims[3] // 4,
                    fetch_words_per_row=16)
                for i in range(4)]

            # Pump through data
            # We want to produce 16 pixels of output data
            # Total of 16 pixels * 16 depth= 256 values
            # The first activation stream produces (1/4 * 16 =) 4 pixels
            # 4 pixels * output_depth = 64 values.
            # Each pass of of input data produces 2 values7.
            # Therefore 32 passes are required
            # Each pass increments over 16 pixels of data.
            # Input pass = 16 pixels * 16 depth = 256 values = 64 words
            # 32 passes * 64 words/pass * 1 cycle/word = 2048 cycles
            # Add 3 cycles to allow other input streams to complete
            for clock in range(2048 + 3):
                first = (clock < 2048) and (clock % 64) == 0
                last = (clock < 2048) and (clock % 64) == 63
                yield dut.first.eq(first)
                yield dut.last.eq(last)

                # set activations
                # act[0] starts on clock 0, act[1] starts on clock 1 etc.
                for a in range(min(clock + 1, 4)):
                    addr = next(activation_addr[a])
                    activation = data.input_data[addr]
                    with_offset = pack_vals(
                        *unpack_bytes(activation),
                        bits=9,
                        offset=data.input_offset)
                    yield dut.activations[a].eq(with_offset)

                # set filters
                yield dut.filters[0].eq(filter_even[clock % len(filter_even)])
                yield dut.filters[1].eq(filter_odd[(clock - 1) % len(filter_odd)])
                yield
        self.add_process(feed_dut)

        def check_output():
            yield dut.output.ready.eq(1)

            # Collect all of the output data for 16 pixels
            # 16 pixels * 16 depth = 256 values = 64 words
            actual_outputs = []
            for i in range(64):
                while not (yield dut.output.valid):
                    yield
                actual_outputs.append((yield dut.output.payload) & 0xffff_ffff)
                yield
            # Reorder output words to match tflite expected order
            reordered_actual = []
            for four_pixels in group(actual_outputs, 16):
                reordered_actual += four_pixels[::4]
                reordered_actual += four_pixels[1::4]
                reordered_actual += four_pixels[2::4]
                reordered_actual += four_pixels[3::4]

            # Check reordered output against expected
            for i, (actual, expected) in enumerate(
                    zip(reordered_actual, self.data.expected_output_data)):
                self.assertEqual(
                    actual, expected, f" word {i}: " +
                    f"actual {actual:08x} != expected {expected:08x} "
                    f"(pos {i*4}, output {i // 4}, row {i % 4}, col {i %2})")

        self.run_sim(check_output, False)
