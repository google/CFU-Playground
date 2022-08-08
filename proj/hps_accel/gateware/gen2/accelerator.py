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

from amaranth import (
    Const,
    Memory,
    Mux,
    Record,
    ResetInserter,
    Signal,
    signed,
    unsigned)

from ..stream import connect, Endpoint
from ..util import SimpleElaboratable
from .constants import Constants
from .filter import FilterStore, FILTER_WRITE_COMMAND
from .mem import SinglePortMemory
from .mode0_input import Mode0InputFetcher
from .mode1_input import Mode1InputFetcher
from .post_process import (
    AccumulatorReader,
    OutputWordAssembler,
    ParamWriter,
    POST_PROCESS_PARAMS,
    POST_PROCESS_PARAMS_WIDTH,
    PostProcessPipeline,
    ReadingProducer,
    StreamLimiter)
from .ram_mux import RamMux
from .sysarray import SystolicArray
from .utils import unsigned_upto


ACCELERATOR_CONFIGURATION_LAYOUT = [
    # The mode of the accelerator - mode 0 for input, mode 1 for full speed
    ('mode', unsigned(1)),
    # Offset applied to each input activation value.
    ('input_offset', signed(9)),
    # Number of words of filter data, per filter store
    ('num_filter_words', unsigned_upto(Constants.FILTER_WORDS_PER_STORE)),
    # Offset applied to each output value.
    ('output_offset', signed(9)),
    #  The minimum output value
    ('output_activation_min', signed(8)),
    #  The maximum output value
    ('output_activation_max', signed(8)),
    # Address of start of input data, in bytes
    ('input_base_addr', 18),
    # How many pixels in output row
    ('num_pixels_x', 9),
    # Number of RAM blocks to advance to move to new pixel in X direction
    ('pixel_advance_x', 4),
    # Number of RAM blocks  to advance between pixels in Y direction
    ('pixel_advance_y', 8),
    # The number of 8bit values in the input channel - divisible by 16
    ('input_channel_depth', unsigned_upto(Constants.MAX_CHANNEL_DEPTH)),
    # Number of output channels - divisible by 4
    ('output_channel_depth', unsigned_upto(Constants.MAX_CHANNEL_DEPTH)),
    # Number of 8bit output values produced. Expected to be a multiple of 16.
    ('num_output_values', 18),
]


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

    Arguments
    ---------
    specialize_nx: bool
        Whether to generate specialized code for the Crosslink/NX-17.

    Attributes
    ----------

    reset: Signal(), in
        Resets internal logic ready for configuration.

    start: Signal(), in
        Starts accelerator working.

    config: Record(ACCELERATOR_CONFIGURATION_LAYOUT), in
        Configuration values for this component.

    write_filter_input: Endpoint(FILTER_WRITE_COMMAND), in
        Commands to write to the filter store.

    lram_addr: [Signal(14)] * 4, out
        Address for each LRAM bank

    lram_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.

    post_process_params: Endpoint(POST_PROCESS_PARAMS), out
        Stream of data to write to post_process memory.

    output: Endpoint(unsigned(32)), out
      The 8 bit output values as 4 byte words. Values are produced in an
      algorithm dependent order.
    """

    def __init__(self, specialize_nx=False):
        self._specialize_nx = specialize_nx
        self.reset = Signal()
        self.start = Signal()
        self.config = Record(ACCELERATOR_CONFIGURATION_LAYOUT)

        self.write_filter_input = Endpoint(FILTER_WRITE_COMMAND)
        self.lram_addr = [Signal(14, name=f"lram_addr{i}") for i in range(4)]
        self.lram_data = [Signal(32, name=f"lram_data{i}") for i in range(4)]
        self.post_process_params = Endpoint(POST_PROCESS_PARAMS)
        self.output = Endpoint(unsigned(32))

    def build_filter_store(self, m):
        m.submodules['filter_store'] = store = FilterStore()
        m.d.comb += [
            *connect(self.write_filter_input, store.write_input),
            store.size.eq(self.config.num_filter_words),
            store.start.eq(self.start),
        ]
        return store.values_out

    def create_fetcher(self, m, stop, name, klass):
        # Create a fetcher submodule and connect common interface
        m.submodules[name] = fetcher = klass()
        m.d.comb += [
            # We reset the fetcher on stop to avoid spurious first and last
            # signals that might corrupt the next accelerator reset.
            fetcher.reset.eq(self.reset | stop),
            fetcher.start.eq(self.start),
            fetcher.base_addr.eq(self.config.input_base_addr),
        ]
        return fetcher

    def build_input_fetcher(self, m, stop):
        # Create fetchers
        f0 = self.create_fetcher(m, stop, 'f0', Mode0InputFetcher)
        f1 = self.create_fetcher(m, stop, 'f1', Mode1InputFetcher)

        # Additional config for fetcher1
        repeats = (self.config.output_channel_depth //
                   Const(Constants.SYS_ARRAY_WIDTH))
        m.d.comb += [
            f1.num_pixels_x.eq(self.config.num_pixels_x),
            f1.pixel_advance_x.eq(self.config.pixel_advance_x),
            f1.pixel_advance_y.eq(self.config.pixel_advance_y),
            f1.depth.eq(self.config.input_channel_depth >> 4),
            f1.num_repeats.eq(repeats),
        ]

        # Create RamMux and connect to LRAMs
        m.submodules['ram_mux'] = ram_mux = RamMux()
        mode = self.config.mode
        for i in range(4):
            # Connect to ram mux addr and data ports
            m.d.comb += self.lram_addr[i].eq(ram_mux.lram_addr[i])
            m.d.comb += ram_mux.lram_data[i].eq(self.lram_data[i])
            m.d.comb += f0.ram_mux_data[i].eq(ram_mux.data_out[i])
            m.d.comb += f1.ram_mux_data[i].eq(ram_mux.data_out[i])
            m.d.comb += ram_mux.addr_in[i].eq(
                Mux(mode, f1.ram_mux_addr[i], f0.ram_mux_addr[i]))

        # phase input depends on mode
        m.d.comb += ram_mux.phase.eq(
            Mux(mode, f1.ram_mux_phase, f0.ram_mux_phase))

        # Router fetcher outputs depending on mode
        mode_first = Mux(mode, f1.first, f0.first)
        mode_last = Mux(mode, f1.last, f0.last)
        mode_data = [Mux(mode, f1.data_out[i], f0.data_out[i])
                     for i in range(4)]

        return (mode_first, mode_last, mode_data)

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
        repeats = Mux(self.config.mode,
                      Constants.SYS_ARRAY_HEIGHT,
                      Constants.SYS_ARRAY_HEIGHT // 2)
        m.d.comb += [
            # Reset reader whenever new parameters are written
            reader.reset.eq(pw.input_data.is_transferring()),
            reader.sizes.depth.eq(self.config.output_channel_depth),
            reader.sizes.repeats.eq(repeats),
            rp.addr.eq(reader.mem_addr),
            reader.mem_data.eq(rp.data),
        ]
        return reader.output_data

    def build_accumulator_reader(self, m, accumulators, accumulator_news):
        """Builds and connects the accumulator reader part."""
        ar = ResetInserter(self.reset)(AccumulatorReader())
        m.submodules['acc_reader'] = ar
        m.d.comb += ar.half_mode.eq(~self.config.mode)
        for i in range(8):
            m.d.comb += [
                ar.accumulator[i].eq(accumulators[i]),
                ar.accumulator_new[i].eq(accumulator_news[i]),
            ]
        m.submodules['acc_limiter'] = al = StreamLimiter()
        m.d.comb += connect(ar.output, al.stream_in)
        m.d.comb += al.num_allowed.eq(self.config.num_output_values)
        m.d.comb += al.start.eq(self.start)
        return al.stream_out, al.finished

    def elab(self, m):
        # Create filter store and input fetcher
        filter_values = self.build_filter_store(m)
        stop_input = Signal()
        first, last, activations = self.build_input_fetcher(m, stop_input)

        # Plumb in sysarray and its inputs
        m.submodules['sysarray'] = sa = SystolicArray(self._specialize_nx)
        for j, (in_a, activation) in enumerate(zip(sa.input_a, activations)):
            # Assign activation values with input offset
            for i in range(4):
                raw_val = Signal(signed(8), name=f"raw_{j}_{i}")
                m.d.comb += raw_val.eq(activation[i * 8:i * 8 + 8])
                with_offset = Signal(signed(9), name=f"val_{j}_{i}")
                m.d.sync += with_offset.eq(raw_val + self.config.input_offset)
                m.d.comb += in_a[i * 9:i * 9 + 9].eq(with_offset)
        for in_b, value in zip(sa.input_b, filter_values):
            m.d.sync += in_b.eq(value)
        m.d.sync += sa.first.eq(first)
        m.d.sync += sa.last.eq(last)

        # Get pipeline inputs from systolic array and parameters
        accumulator_stream, finished = self.build_accumulator_reader(
            m, sa.accumulator, sa.accumulator_new)
        param_stream = self.build_param_store(m)

        # When last accumulator read, stop input
        m.d.comb += stop_input.eq(finished)

        # Plumb in pipeline
        m.submodules['ppp'] = ppp = PostProcessPipeline()

        m.d.comb += connect(accumulator_stream, ppp.input)
        m.d.comb += connect(param_stream, ppp.params)
        m.d.comb += [
            ppp.offset.eq(self.config.output_offset),
            ppp.activation_min.eq(self.config.output_activation_min),
            ppp.activation_max.eq(self.config.output_activation_max),
        ]

        # Handle output
        m.submodules['owa'] = owa = ResetInserter(
            self.reset)(OutputWordAssembler())
        m.d.comb += owa.half_mode.eq(~self.config.mode)
        m.d.comb += connect(ppp.output, owa.input)
        m.d.comb += connect(owa.output, self.output)
