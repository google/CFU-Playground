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

from functools import reduce
import random

from nmigen import Module, signed, unsigned
from nmigen.sim import Passive

from nmigen_cfu import pack_vals, TestBase

from .accelerator import AcceleratorCore
from .constants import Constants
from .conv2d_data import fetch_data
from .ram_input import InputFetcher


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

    NUM_OUTPUT_PIXELS = 16

    def create_dut(self):
        return AcceleratorCore()

    def setUp(self):
        self.data = fetch_data('sample_conv_1')
        super().setUp()

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

    def configure(self):
        # Configure the accelerator
        dut = self.dut
        data = self.data
        num_filter_values = reduce(lambda a, b: a * b, data.filter_dims, 1)
        input_depth = data.input_dims[3]
        in_x_dim = data.input_dims[2]
        out_x_dim = data.output_dims[2]
        output_depth = data.output_dims[3]
        filter_words_per_store = num_filter_values // 4 // 2
        yield dut.config.input_offset.eq(data.input_offset)
        yield dut.config.num_filter_words.eq(filter_words_per_store)
        yield dut.config.output_offset.eq(data.output_offset)
        yield dut.config.output_activation_min.eq(data.output_min)
        yield dut.config.output_activation_max.eq(data.output_max)
        yield dut.config.input_base_addr.eq(0x123)
        yield dut.config.num_pixels_x.eq(out_x_dim)
        yield dut.config.pixel_advance_x.eq(input_depth // 16)
        yield dut.config.pixel_advance_y.eq((input_depth // 16) * in_x_dim)
        yield dut.config.input_channel_depth.eq(input_depth)
        yield dut.config.output_channel_depth.eq(output_depth)
        yield dut.config.num_output_values.eq(self.NUM_OUTPUT_PIXELS * output_depth)

        # Toggle resets
        yield dut.reset.eq(1)
        yield
        yield dut.reset.eq(0)

        # load post process parameters
        for i in range(output_depth):
            payload = dut.post_process_params.payload
            yield payload.bias.eq(data.output_biases[i])
            yield payload.multiplier.eq(data.output_multipliers[i])
            # Note: shift is stored as a negative number in tflite model
            yield payload.shift.eq(-data.output_shifts[i])
            yield dut.post_process_params.valid.eq(1)
            yield
        yield dut.post_process_params.valid.eq(0)
        yield

        # Load filters
        filter_data = self.extract_filter_data()
        for addr in range(filter_words_per_store):
            for store in range(2):
                inp = dut.write_filter_input
                yield inp.payload.store.eq(store)
                yield inp.payload.addr.eq(addr)
                yield inp.payload.data.eq(filter_data[store][addr])
                yield inp.valid.eq(True)
                yield
                yield inp.valid.eq(False)

    def test_convolution(self):
        # tests part of a convolution, producing results for 16 output pixels
        # uses data dumped from a real convolution
        dut = self.dut
        data = self.data

        def ram():
            yield Passive()
            while True:
                for i in range(4):
                    block = (yield dut.lram_addr[i]) - 0x123
                    data_addr = block * 4 + i
                    data_value = data.input_data[data_addr % len(
                        data.input_data)]
                    yield dut.lram_data[i].eq(data_value)
                yield
        self.add_process(ram)

        def start_dut():
            yield Passive()
            yield from self.configure()

            # Start the dut
            yield dut.start.eq(1)
            yield
            yield dut.start.eq(0)
            yield

        self.add_process(start_dut)

        def check_output():
            yield dut.output.ready.eq(1)

            # Collect all of the output data for all pixels
            actual_outputs = []
            for i in range(self.NUM_OUTPUT_PIXELS * data.output_dims[3] // 4):
                while not (yield dut.output.valid):
                    yield
                actual_outputs.append((yield dut.output.payload) & 0xffff_ffff)
                yield
            # Check for a bit longer to ensure no more data than expected
            for _ in range(100):
                self.assertFalse((yield dut.output.valid))
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
