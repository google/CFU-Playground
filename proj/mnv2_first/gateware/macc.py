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

from nmigen import Signal, signed

from nmigen_cfu import all_words, Sequencer, SimpleElaboratable, tree_sum

from .registerfile import Xetter


class Madd4Pipeline(SimpleElaboratable):
    """A 4-wide Multiply Add pipeline.

    Pipeline takes 2 additional cycles.

    f_data and i_data each contain 4 signed 8 bit values. The
    calculation performed is:

    result = sum((i_data[n] + offset) * f_data[n] for n in range(4))

    Public Interface
    ----------------
    offset: Signal(signed(8)) input
        Offset to be added to all inputs.
    f_data: Signal(32) input
        4 bytes of filter data to use next
    i_data: Signal(32) input
        4 bytes of input data data to use next
    result: Signal(signed(32)) output
        Result of the multiply and add
    """
    PIPELINE_CYCLES = 2

    def __init__(self):
        super().__init__()
        self.offset = Signal(signed(9))
        self.f_data = Signal(32)
        self.i_data = Signal(32)
        self.result = Signal(signed(32))

    def elab(self, m):
        # Product is 17 bits: 8 bits * 9 bits = 17 bits
        products = [Signal(signed(17), name=f"product_{n}") for n in range(4)]
        for i_val, f_val, product in zip(
                all_words(self.i_data, 8), all_words(self.f_data, 8), products):
            f_tmp = Signal(signed(9))
            m.d.sync += f_tmp.eq(f_val.as_signed())
            i_tmp = Signal(signed(9))
            m.d.sync += i_tmp.eq(i_val.as_signed() + self.offset)
            m.d.comb += product.eq(i_tmp * f_tmp)

        m.d.sync += self.result.eq(tree_sum(products))


class ExplicitMacc4(Xetter):
    """A Macc4 that operates on in0 (input_vals) and in1 (filter_vals).

    Public Interface
    ----------------
    input_offset: Signal(signed(8)) input
        Offset to be added to all inputs.

    """

    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(9))

    def elab(self, m):
        m.submodules['madd4'] = madd4 = Madd4Pipeline()
        m.d.comb += [
            madd4.offset.eq(self.input_offset),
            madd4.f_data.eq(self.in1),
            madd4.i_data.eq(self.in0),
            self.output.eq(madd4.result),
        ]
        m.submodules['seq'] = seq = Sequencer(Madd4Pipeline.PIPELINE_CYCLES)
        m.d.comb += seq.inp.eq(self.start)
        m.d.comb += self.done.eq(seq.sequence[-1])


class AccumulatorRegisterXetter(Xetter):
    """An accumulator which can also be get and set.

    Sets new value from in0. Return previous value on set.


    Public Interface
    ----------------
    value: Signal(signed(32)) output
        The value held by this register. It will be set from in0 (on self.start)
        or added to from add_data (on self.add_en)
    add_en: Signal input
        This signal is pulsed high to add to the accumulator.
    add_data: Signal(signed(32)) input
        The value to add to the accumulator
    """

    def __init__(self):
        super().__init__()
        self.value = Signal(signed(32))
        self.add_en = Signal()
        self.add_data = Signal(signed(32))

    def elab(self, m):
        with m.If(self.start):
            m.d.sync += self.value.eq(self.in0),
            m.d.comb += self.output.eq(self.value)
            m.d.comb += self.done.eq(1)
        with m.Elif(self.add_en):
            m.d.sync += self.value.eq(self.value + self.add_data),


class ImplicitMacc4(Xetter):
    """A Macc4 that operates on input_vals and filter_vals provided
    from within the CFU.

    Public Interface
    ----------------
    input_offset: Signal(signed(8)) input
        Offset to be added to all inputs.
    f_data: Signal(32) input
        Filter data to use next
    f_next: Signal() output
        Indicates filter data has been used
    i_data: Signal(32) input
        Input data to use next
    i_next: Signal() output
        Indicates input data has been used
    i_ready: Signal() input
        Whether or not i_data is valid.
    """

    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(9))
        self.f_data = Signal(32)
        self.f_next = Signal()
        self.i_data = Signal(32)
        self.i_next = Signal()
        self.i_ready = Signal()

    def elab(self, m):
        m.submodules['madd4'] = madd4 = Madd4Pipeline()
        m.d.comb += [
            madd4.offset.eq(self.input_offset),
            madd4.f_data.eq(self.f_data),
            madd4.i_data.eq(self.i_data),
            self.output.eq(madd4.result),
        ]

        # Signal only when i_ready has been set, then start sequence to be done
        # next cycle
        m.submodules['seq'] = seq = Sequencer(Madd4Pipeline.PIPELINE_CYCLES)
        m.d.comb += self.done.eq(seq.sequence[-1])
        waiting_for_i_ready = Signal()
        with m.If(self.i_ready & (waiting_for_i_ready | self.start)):
            m.d.comb += [
                self.f_next.eq(1),
                self.i_next.eq(1),
                seq.inp.eq(1),
            ]
            m.d.sync += waiting_for_i_ready.eq(0)
        with m.Elif(self.start & ~self.i_ready):
            m.d.sync += waiting_for_i_ready.eq(1)


class Macc4Run1(Xetter):
    """A Macc4 that accumlates 1 input channel's worth of data.

    Public Interface
    ----------------
    input_offset: Signal(signed(8)) input
        Offset to be added to all inputs.
    input_depth: Signal(10) input
        Number of words in input
    f_data: Signal(32) input
        Filter data to use next
    f_next: Signal() output
        Indicates filter data has been used
    i_data: Signal(32) input
        Input data to use next
    i_next: Signal() output
        Indicates input data has been used
    i_ready: Signal() input
        Whether or not i_data is valid.
    add_en: Signal output
        Indicates something avialable to add
    add_data: Signal(signed(32)) output
        The value to add to the accumulator
    """

    def __init__(self):
        super().__init__()
        self.input_offset = Signal(signed(9))
        self.input_depth = Signal(32)
        self.f_data = Signal(32)
        self.f_next = Signal()
        self.i_data = Signal(32)
        self.i_next = Signal()
        self.i_ready = Signal()
        self.add_en = Signal()
        self.add_data = Signal(signed(32))

    def elab(self, m):
        m.submodules['madd4'] = madd4 = Madd4Pipeline()
        m.d.comb += [
            madd4.offset.eq(self.input_offset),
            madd4.f_data.eq(self.f_data),
            madd4.i_data.eq(self.i_data),
            self.output.eq(madd4.result),
        ]
        m.submodules['macc_seq'] = macc_seq = Sequencer(
            Madd4Pipeline.PIPELINE_CYCLES)

        started_macc4s = Signal(10)
        starting_last = Signal()
        retired_macc4s = Signal(10)
        retiring_last = Signal()

        # Puts 1 word of data into the pipeline, if it's ready
        def start_macc4():
            with m.If(self.i_ready):
                m.d.sync += started_macc4s.eq(started_macc4s + 1)
                m.d.comb += [
                    macc_seq.inp.eq(1),
                    self.f_next.eq(1),
                    self.i_next.eq(1),
                    starting_last.eq(started_macc4s == self.input_depth - 1)
                ]

        def retire_macc4():
            with m.If(macc_seq.sequence[-1]):
                m.d.sync += retired_macc4s.eq(retired_macc4s + 1)
                m.d.comb += [
                    self.add_en.eq(1),
                    self.add_data.eq(madd4.result),
                    retiring_last.eq(retired_macc4s == self.input_depth - 1)
                ]

        with m.FSM():
            with m.State("PREPARE"):
                m.d.sync += [
                    started_macc4s.eq(0),
                    retired_macc4s.eq(0),
                ]
                m.next = "READY"
            with m.State("READY"):
                with m.If(self.start):
                    start_macc4()
                    m.next = "RUN"
            with m.State("RUN"):
                start_macc4()
                retire_macc4()
                with m.If(starting_last):
                    m.next = "FINISH"
            with m.State("FINISH"):
                retire_macc4()
                with m.If(retiring_last):
                    m.d.comb += self.done.eq(1)
                    m.d.sync += [
                        started_macc4s.eq(0),
                        retired_macc4s.eq(0),
                    ]
                    m.next = "READY"
