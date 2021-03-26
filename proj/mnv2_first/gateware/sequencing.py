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

from nmigen import Signal
from nmigen.hdl.ast import Mux

from nmigen_cfu import SimpleElaboratable


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
    count_en: Signal() in
        Count up by one.
    done: Signal() out
        Set high for one cycle once counting finished.
    count: Signal(width)
        Current count
    max: Signal(width) in
        The number of counts
    """

    def __init__(self, width):
        self.restart = Signal()
        self.count_en = Signal()
        self.done = Signal()
        self.count = Signal(width)
        self.max = Signal(width)

    def elab(self, m):
        count_reg = Signal.like(self.count)
        last_count = self.max - 1
        next_count = Mux(count_reg == last_count, 0, count_reg + 1)
        m.d.comb += self.count.eq(count_reg)

        with m.If(self.count_en):
            m.d.sync += count_reg.eq(next_count)
            m.d.comb += self.count.eq(next_count)
            m.d.comb += self.done.eq(next_count == last_count)

        with m.If(self.restart):
            m.d.sync += count_reg.eq(0)
            m.d.comb += self.count.eq(0)


class Delayer(SimpleElaboratable):
    """Delays an input Signal via a shift register.

    Parameters
    ----------
    cycles: int
        Number of cycles to delay the signal

    Public Interface
    ---------------
    input: Signal() in
        The input signal
    output: Signal() out
        Mirrors the input signal after cycles delay
    """

    def __init__(self, cycles):
        self.cycles = cycles
        self.input = Signal()
        self.output = Signal()

    def elab(self, m):
        shift_register = Signal(self.cycles)
        m.d.comb += self.output.eq(shift_register[-1])
        m.d.sync += [
            shift_register[1:].eq(shift_register),
            shift_register[0].eq(self.input),
        ]


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

        m.d.comb += self.gate.eq(~self.all_output_finished
                                 & (running | self.start_run)
                                 & self.in_store_ready 
                                 & self.fifo_has_space)
