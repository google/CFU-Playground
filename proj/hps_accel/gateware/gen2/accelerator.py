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

"""Accelerator Gateware"""

from nmigen import Memory, Mux, Record, ResetInserter, Signal, signed, unsigned
from nmigen_cfu.util import SimpleElaboratable

from ..stream import connect, Endpoint
from .constants import Constants
from .filter import FilterStore, FILTER_WRITE_COMMAND
from .mem import SinglePortMemory
from .post_process import (
    AccumulatorReader,
    OutputWordAssembler,
    ParamWriter,
    POST_PROCESS_PARAMS,
    POST_PROCESS_SIZES,
    POST_PROCESS_PARAMS_WIDTH,
    PostProcessPipeline,
    ReadingProducer,
    StreamLimiter)
from .ram_input import InputFetcher
from .sysarray import SystolicArray
from .utils import unsigned_upto


class AcceleratorCore(SimpleElaboratable):
    """Core of the accelerator.

    Sequence of use:
    1. Set filter and post process param sizes
    2. reset
    3. Add filter an post process param data

    This is a work in progress.

    The current version includes:
    -   input_offset adjustment
    -   Systolic Array
    -   Post Process Pipeline
    -   Post Process Parameter Write
    -   FIFO for output values

    Still TODO:
    -   Read Input activation values from memory

    Attributes
    ----------

    reset: Signal(), in
        Resets internal logic ready for configuration.

    start: Signal(), in
        Starts accelerator working.

    input_offset: Signal(signed(9)), in
        Offset applied to each input activation value.

    num_filter_words: Signal(unsigned_upto(FILTER_WORDS_PER_STORE)), in
        Number of words of filter data, per filter store

    output_offset: Signal(signed(9)), in
        Offset applied to each output value.

    output_activation_min: Signal(signed(8)), out
        The minimum output value

    output_activation_max: Signal(signed(8)), out
        The maximum output value

    write_filter_input: Endpoint(FILTER_WRITE_COMMAND), in
        Commands to write to the filter store.

    input_base_addr: Signal(14), in
        Address of start of input data, in 16 byte blocks (i.e addr 1 = byte 16)

    num_pixels_x: Signal(9), in
        How many pixels in output row

    pixel_advance_x: Signal(4), in
        Number of RAM blocks to advance to move to new pixel in X direction

    pixel_advance_y: Signal(8), in
        Number of RAM blocks  to advance between pixels in Y direction

    num_repeats: Signal(unsigned_upto(64)), in
        The number of times each stream of input pixel data is to be repeated.

    lram_addr: [Signal(14)] * 4, out
        Address for each LRAM bank

    lram_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.

    output_channel_depth: Signal(unsigned_upto(MAX_CHANNEL_DEPTH)), in
        Number of output channels - must be divisible by 16

    post_process_params: Endpoint(POST_PROCESS_PARAMS), out
        Stream of data to write to post_process memory.

    num_output_values: Signal(18), in
        Number of 8bit output values produced. Expected to be a multiple of 16.

    activations: [Signal(32) * 4], in
        Activation values as read from memory. Four 8 bit values are
        packed into each 32 bit word.

    first: Signal(), in
        Beginning of value computation signal for systolic array.

    last: Signal(), in
        End of value computation signal for systolic array.

    output: Endpoint(unsigned(32)), out
      The 8 bit output values as 4 byte words. Values are produced in an
      algorithm dependent order.

    """

    def __init__(self):
        self.reset = Signal()
        self.start = Signal()

        self.input_offset = Signal(signed(9))
        self.num_filter_words = Signal(
            unsigned_upto(Constants.FILTER_WORDS_PER_STORE))

        self.output_offset = Signal(signed(9))
        self.output_activation_min = Signal(signed(8))
        self.output_activation_max = Signal(signed(8))
        self.write_filter_input = Endpoint(FILTER_WRITE_COMMAND)

        self.input_base_addr = Signal(14)
        self.num_pixels_x = Signal(9)
        self.pixel_advance_x = Signal(4)
        self.pixel_advance_y = Signal(8)
        self.num_repeats = Signal(unsigned_upto(64))

        self.lram_addr = [Signal(14, name=f"lram_addr{i}") for i in range(4)]
        self.lram_data = [Signal(32, name=f"lram_data{i}") for i in range(4)]

        self.output_channel_depth = Signal(
            unsigned_upto(Constants.MAX_CHANNEL_DEPTH))
        self.post_process_params = Endpoint(POST_PROCESS_PARAMS)
        self.num_output_values = Signal(unsigned(18))

        self.output = Endpoint(unsigned(32))

    def build_filter_store(self, m):
        m.submodules['filter_store'] = store = FilterStore()
        m.d.comb += [
            *connect(self.write_filter_input, store.write_input),
            store.size.eq(self.num_filter_words),
            store.start.eq(self.start),
        ]
        return store.values_out

    def build_input_fetcher(self, m):
        m.submodules['fetcher'] = fetcher = InputFetcher()
        m.d.comb += [
            fetcher.reset.eq(self.reset),
            fetcher.start.eq(self.start),
            fetcher.base_addr.eq(self.input_base_addr),
            fetcher.num_pixels_x.eq(self.num_pixels_x),
            fetcher.pixel_advance_x.eq(self.pixel_advance_x),
            fetcher.pixel_advance_y.eq(self.pixel_advance_y),
            fetcher.depth.eq(self.output_channel_depth >> 4),  # divide by 16
            fetcher.num_repeats.eq(self.num_repeats),
        ]
        for i in range(4):
            m.d.comb += [
                self.lram_addr[i].eq(fetcher.lram_addr[i]),
                fetcher.lram_data[i].eq(self.lram_data[i]),
            ]

        return fetcher.first, fetcher.last, fetcher.data_out

    def build_param_store(self, m):
        # Create memory for post process params
        # Use SinglePortMemory here?
        param_mem = Memory(
            width=POST_PROCESS_PARAMS_WIDTH,
            depth=Constants.MAX_CHANNEL_DEPTH)
        m.submodules['param_rp'] = rp = param_mem.read_port(transparent=False)
        m.submodules['param_wp'] = wp = param_mem.write_port()

        # Configure param writer
        m.submodules['param_writer'] = pw = ParamWriter()
        m.d.comb += connect(self.post_process_params, pw.input_data)
        m.d.comb += [
            pw.reset.eq(self.reset),
            wp.en.eq(pw.mem_we),
            wp.addr.eq(pw.mem_addr),
            wp.data.eq(pw.mem_data),
        ]

        # Configure param reader
        m.submodules['param_reader'] = reader = ReadingProducer()
        m.d.comb += [
            # Reset reader whenever new parameters are written
            reader.reset.eq(pw.input_data.is_transferring()),
            reader.sizes.depth.eq(self.output_channel_depth),
            reader.sizes.repeats.eq(Constants.SYS_ARRAY_HEIGHT),
            rp.addr.eq(reader.mem_addr),
            reader.mem_data.eq(rp.data),
        ]
        return reader.output_data

    def build_accumulator_reader(self, m, accumulators, accumulator_news):
        """Builds and connects the accumulator reader part."""
        ar = ResetInserter(self.reset)(AccumulatorReader())
        m.submodules['acc_reader'] = ar
        for i in range(8):
            m.d.comb += [
                ar.accumulator[i].eq(accumulators[i]),
                ar.accumulator_new[i].eq(accumulator_news[i]),
            ]
        m.submodules['acc_limiter'] = al = StreamLimiter()
        m.d.comb += connect(ar.output, al.stream_in)
        m.d.comb += al.num_allowed.eq(self.num_output_values)
        m.d.comb += al.start.eq(self.start)
        return al.stream_out

    def elab(self, m):
        # Create filter store and input fetcher
        filter_values = self.build_filter_store(m)
        first, last, activations = self.build_input_fetcher(m)

        # Plumb in sysarray and its inputs
        m.submodules['sysarray'] = sa = SystolicArray()
        for in_a, activation in zip(sa.input_a, activations):
            # Assign activation values with input offset
            for i in range(4):
                with_offset = Signal(signed(8), name=f"val_{i}")
                raw_val = activation[i * 8:i * 8 + 8]
                m.d.comb += with_offset.eq(raw_val + self.input_offset)
                m.d.comb += in_a[i * 9:i * 9 + 9].eq(with_offset)
        for in_b, value in zip(sa.input_b, filter_values):
            m.d.comb += in_b.eq(value)
        m.d.comb += sa.first.eq(first)
        m.d.comb += sa.last.eq(last)

        # Get pipeline inputs from systolic array and parameters
        accumulator_stream = self.build_accumulator_reader(
            m, sa.accumulator, sa.accumulator_new)
        param_stream = self.build_param_store(m)

        # Plumb in pipeline
        m.submodules['ppp'] = ppp = PostProcessPipeline()

        m.d.comb += connect(accumulator_stream, ppp.input)
        m.d.comb += connect(param_stream, ppp.params)
        m.d.comb += [
            ppp.offset.eq(self.output_offset),
            ppp.activation_min.eq(self.output_activation_min),
            ppp.activation_max.eq(self.output_activation_max),
        ]

        # Handle output
        m.submodules['owa'] = owa = ResetInserter(
            self.reset)(OutputWordAssembler())
        m.d.comb += connect(ppp.output, owa.input)
        m.d.comb += connect(owa.output, self.output)
