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

from amaranth import Signal, Mux

from amaranth_cfu import SimpleElaboratable

from . import config
from .delay import Delayer
from .macc import Madd4Pipeline
from .post_process import PostProcessor


class UpCounter(SimpleElaboratable):
    """Counts pulses.

    Parameters
    ----------
    width: int
        Number of bits in counter

    Public Interface
    ---------------
    restart: Signal() in
        Zero all internal counter, get ready to start again.
    en: Signal() in
        Count up by one.
    done: Signal() out
        Set high for one cycle once max pulses received
    max: Signal(width) in
        The number of counts
    """

    def __init__(self, width):
        self.restart = Signal()
        self.en = Signal()
        self.done = Signal()
        self.max = Signal(width)

    def elab(self, m):
        count = Signal.like(self.max)
        last_count = self.max - 1
        next_count = Mux(count == last_count, 0, count + 1)

        with m.If(self.en):
            m.d.sync += count.eq(next_count)
            m.d.comb += self.done.eq(count == last_count)

        with m.If(self.restart):
            m.d.sync += count.eq(0)


class GateCalculator(SimpleElaboratable):
    """Calcaulates the 'gate' signal

    Public Interface
    ---------------
    start_run: Signal() in
        High for a single cycle when a run is started.
    all_output_finished: Signal() in
        High when all of the output channels calculations have been started.
    in_store_ready: Signal() in
        High while input store has data available for read.
    fifo_has_space: Signal() in
        High while fifo has space to store an entire pipeline's worth of data.
    gate: Signal() out
        High when pipeline should accept data
    """

    def __init__(self):
        self.start_run = Signal()
        self.all_output_finished = Signal()
        self.in_store_ready = Signal()
        self.fifo_has_space = Signal()
        self.gate = Signal()

    def elab(self, m):
        running = Signal()
        with m.If(self.start_run):
            m.d.sync += running.eq(1)
        with m.If(self.all_output_finished):
            m.d.sync += running.eq(0)

        m.d.comb += self.gate.eq((running | self.start_run)
                                 & self.in_store_ready
                                 & self.fifo_has_space)


class Sequencer(SimpleElaboratable):
    """Sequences a 1x1 convolution.

    This is the control logic required to calculate all output channel values
    for a single input pixel.

    Public Interface
    ---------------
    start_run: Signal() in
        When the run commences.
    in_store_ready: Signal() in
        Input store has data available
    fifo_has_space: Signal() in
        Output fifo has space to store a whole pipeline of output
    filter_value_words: Signal(range(FILTER_DATA_TOTAL_WORDS+1)) in
        Number of 32bit words of filter data there are.
        This value is output_channel_batch_size * input_depth / 4.
    input_depth_words: Signal(range(MAX_PER_PIXEL_INPUT_WORDS+1)) in
        Number of 32bit words of input channel data there are.
        This value is input_depth / 4.
    gate: Signal() out
        High when pipeline should accept data
    all_output_finished: Signal() out
        High when all of the output channels calculations have been started.
    madd_done: Signal() out
        Result available from Madd Pipeline
    acc_done: Signal() out
        Accumulation is done, and post processing is ready to start
    pp_done: Signal() out
        Post processing is done and pp output should be shifted into the ouput word
    out_word_done: Signal() out
        Four output channel values have been calculated into the output word which is
        ready to be put onto the FIFO.
    """

    def __init__(self):
        self.start_run = Signal()
        self.in_store_ready = Signal()
        self.fifo_has_space = Signal()
        self.filter_value_words = Signal(
            range(config.FILTER_DATA_TOTAL_WORDS + 1))
        self.input_depth_words = Signal(
            range(config.MAX_PER_PIXEL_INPUT_WORDS + 1))
        self.gate = Signal()
        self.all_output_finished = Signal()
        self.madd_done = Signal()
        self.acc_done = Signal()
        self.pp_done = Signal()
        self.out_word_done = Signal()

    def elab(self, m):
        m.submodules['gate_calc'] = gate_calc = GateCalculator()
        m.d.comb += [
            gate_calc.start_run.eq(self.start_run),
            gate_calc.in_store_ready.eq(self.in_store_ready),
            gate_calc.fifo_has_space.eq(self.fifo_has_space),
            gate_calc.all_output_finished.eq(self.all_output_finished),
            self.gate.eq(gate_calc.gate),
        ]
        m.submodules['f_count'] = f_count = UpCounter(
            self.filter_value_words.shape().width)
        m.d.comb += [
            f_count.en.eq(self.gate),
            f_count.max.eq(self.filter_value_words),
            self.all_output_finished.eq(f_count.done)
        ]
        m.submodules['i_count'] = i_count = UpCounter(
            self.input_depth_words.shape().width)
        m.d.comb += [
            i_count.max.eq(self.input_depth_words),
            self.acc_done.eq(i_count.done),
        ]
        m.submodules['four_count'] = four_count = UpCounter(3)
        m.d.comb += [
            four_count.max.eq(4),
            self.out_word_done.eq(four_count.done)
        ]

        m.submodules['madd_delay'] = madd_delay = Delayer(
            Madd4Pipeline.PIPELINE_CYCLES)
        m.d.comb += [
            madd_delay.input.eq(self.gate),
            self.madd_done.eq(madd_delay.output),
            i_count.en.eq(madd_delay.output),
        ]

        m.submodules['pp_delay'] = pp_delay = Delayer(
            PostProcessor.PIPELINE_CYCLES)
        m.d.comb += [
            pp_delay.input.eq(self.acc_done),
            self.pp_done.eq(pp_delay.output),
            four_count.en.eq(pp_delay.output),
        ]
