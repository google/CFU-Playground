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

from amaranth import Signal
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth_cfu import simple_cfu, DualPortMemory, is_pysim_run

from . import config
from .macc import Accumulator, ByteToWordShifter, Madd4Pipeline
from .post_process import PostProcessor
from .store import CircularIncrementer, FilterValueFetcher, InputStore, InputStoreSetter, NextWordGetter, StoreSetter
from .registerfile import RegisterFileInstruction, RegisterSetter
from .sequencing import Sequencer


class Mnv2RegisterInstruction(RegisterFileInstruction):

    def _make_setter(self, m, reg_num, name):
        """Constructs and registers a simple RegisterSetter.

        Return a pair of signals from setter: (value, set)
        """
        setter = RegisterSetter()
        m.submodules[name] = setter
        self.register_xetter(reg_num, setter)
        return setter.value, setter.set

    def _make_output_channel_param_store(
            self, m, reg_num, name, restart_signal):
        """Constructs and registers a param store connected to a memory
        and a circular incrementer.

        Returns a pair of signals: (current data, inc.next)
        """
        m.submodules[f'{name}_dp'] = dp = DualPortMemory(
            width=32, depth=config.OUTPUT_CHANNEL_PARAM_DEPTH, is_sim=is_pysim_run())
        m.submodules[f'{name}_inc'] = inc = CircularIncrementer(
            config.OUTPUT_CHANNEL_PARAM_DEPTH)
        m.submodules[f'{name}_set'] = psset = StoreSetter(
            32, 1, config.OUTPUT_CHANNEL_PARAM_DEPTH)
        self.register_xetter(reg_num, psset)
        m.d.comb += [
            # Restart param store when reg is set
            psset.restart.eq(restart_signal),
            inc.restart.eq(restart_signal),
            # Incrementer is limited to number of items already set
            inc.limit.eq(psset.count),
            # Hook memory up to various components
            dp.r_addr.eq(inc.r_addr),
        ]
        m.d.comb += psset.connect_write_port([dp])
        return dp.r_data, inc.next

    def _make_filter_value_store(
            self, m, reg_num, name, restart_signal):
        """Constructs and registers a param store connected to a memory
        and a circular incrementer.

        Returns a list of dual port memories used to implement the store,
        plus signal for count of words.
        """
        dps = []
        for i in range(4):
            m.submodules[f'{name}_dp_{i}'] = dp = DualPortMemory(
                width=32, depth=config.FILTER_DATA_MEM_DEPTH, is_sim=is_pysim_run())
            dps.append(dp)
        m.submodules[f'{name}_set'] = fvset = StoreSetter(
            32, 4, config.FILTER_DATA_MEM_DEPTH)
        self.register_xetter(reg_num, fvset)
        m.d.comb += [
            # Restart param store when reg is set
            fvset.restart.eq(restart_signal),
        ]
        m.d.comb += fvset.connect_write_port(dps)
        return dps, fvset.count, fvset.updated

    def _make_input_store(self, m, name, restart_signal, input_depth_words):
        m.submodules[f'{name}'] = ins = InputStore(
            config.MAX_PER_PIXEL_INPUT_WORDS)
        m.submodules[f'{name}_set'] = insset = InputStoreSetter()
        m.d.comb += insset.connect(ins)
        self.register_xetter(25, insset)
        _, mark_finished = self._make_setter(m, 112, 'mark_read')
        read_finished = Signal()
        m.d.comb += [
            ins.restart.eq(restart_signal),
            ins.input_depth.eq(input_depth_words),
            ins.r_finished.eq(mark_finished | read_finished),
        ]
        return ins, read_finished

    def _make_filter_value_getter(self, m, fvf_data):
        fvg_next = Signal()
        if is_pysim_run():
            m.submodules['fvg'] = fvg = NextWordGetter()
            m.d.comb += [
                fvg.data.eq(fvf_data),
                fvg.ready.eq(1),
                fvg_next.eq(fvg.next),
            ]
            self.register_xetter(110, fvg)
        return fvg_next

    def _make_input_store_getter(self, m, ins_r_data, ins_r_ready):
        insget_next = Signal()
        if is_pysim_run():
            m.submodules['insget'] = insget = NextWordGetter()
            m.d.comb += [
                insget.data.eq(ins_r_data),
                insget.ready.eq(ins_r_ready),
                insget_next.eq(insget.next),
            ]
            self.register_xetter(111, insget)
        return insget_next

    def _make_output_queue(self, m):
        m.submodules['FIFO'] = fifo = SyncFIFOBuffered(
            depth=config.OUTPUT_QUEUE_DEPTH, width=32)
        m.submodules['oq_get'] = oq_get = NextWordGetter()
        m.d.comb += [
            oq_get.data.eq(fifo.r_data),
            oq_get.ready.eq(fifo.r_rdy),
            fifo.r_en.eq(oq_get.next),
        ]
        self.register_xetter(34, oq_get)
        oq_has_space = fifo.w_level < (config.OUTPUT_QUEUE_DEPTH - 8)
        return fifo.w_data, fifo.w_en, oq_has_space

    def elab_xetters(self, m):
        # Simple registers
        input_depth_words, set_id = self._make_setter(
            m, 10, 'set_input_depth_words')
        self._make_setter(m, 11, 'set_output_depth')
        input_offset, _ = self._make_setter(m, 12, 'set_input_offset')
        output_offset, _ = self._make_setter(m, 13, 'set_output_offset')
        activation_min, _ = self._make_setter(m, 14, 'set_activation_min')
        activation_max, _ = self._make_setter(m, 15, 'set_activation_max')

        # Stores of input and output data
        _, restart = self._make_setter(m, 20, 'set_output_batch_size')
        multiplier, multiplier_next = self._make_output_channel_param_store(
            m, 21, 'store_output_multiplier', restart)
        shift, shift_next = self._make_output_channel_param_store(
            m, 22, 'store_output_shift', restart)
        bias, bias_next = self._make_output_channel_param_store(
            m, 23, 'store_output_bias', restart)
        fv_mems, fv_count, fv_updated = self._make_filter_value_store(
            m, 24, 'store_filter_values', restart)

        m.submodules['fvf'] = fvf = FilterValueFetcher(
            config.FILTER_DATA_MEM_DEPTH)
        m.d.comb += fvf.connect_read_ports(fv_mems)
        m.d.comb += [
            # fetcher only works for multiples of 4, and only for multiples of
            # 4 > 8
            fvf.limit.eq(fv_count & ~0x3),
            fvf.updated.eq(fv_updated),
            fvf.restart.eq(restart),
        ]
        ins, ins_r_finished = self._make_input_store(
            m, 'ins', set_id, input_depth_words)

        # Make getters for filter and instruction next words
        # Only required during pysim unit tests
        fvg_next = self._make_filter_value_getter(m, fvf.data)
        insget_next = self._make_input_store_getter(m, ins.r_data, ins.r_ready)

        # The output queue
        oq_w_data, oq_enable, oq_has_space = self._make_output_queue(m)

        # Calculation aparatus
        m.submodules['madd'] = madd = Madd4Pipeline()
        m.d.comb += [
            madd.offset.eq(input_offset),
            madd.f_data.eq(fvf.data),
            madd.i_data.eq(ins.r_data),
        ]

        m.submodules['acc'] = acc = Accumulator()
        m.d.comb += acc.in_value.eq(madd.result)

        m.submodules['pp'] = pp = PostProcessor()
        m.d.comb += [
            pp.offset.eq(output_offset),
            pp.activation_min.eq(activation_min),
            pp.activation_max.eq(activation_max),
            pp.bias.eq(bias),
            pp.multiplier.eq(multiplier),
            pp.shift.eq(shift),
            pp.accumulator.eq(acc.result),
        ]

        m.submodules['btw'] = btw = ByteToWordShifter()
        m.d.comb += btw.in_value.eq(pp.result)

        # Sequencer
        _, start_run = self._make_setter(m, 33, 'start_run')
        m.submodules['seq'] = seq = Sequencer()
        m.d.comb += [
            seq.start_run.eq(start_run),
            seq.in_store_ready.eq(ins.r_ready),
            seq.fifo_has_space.eq(oq_has_space),
            seq.filter_value_words.eq(fv_count),
            seq.input_depth_words.eq(input_depth_words),

            ins.r_next.eq(insget_next | seq.gate),
            fvf.next.eq(fvg_next | seq.gate),
            ins_r_finished.eq(seq.all_output_finished),

            acc.add_en.eq(seq.madd_done),
            acc.clear.eq(seq.acc_done),

            bias_next.eq(seq.acc_done),
            multiplier_next.eq(seq.acc_done),
            shift_next.eq(seq.acc_done),

            btw.shift_en.eq(seq.pp_done),
            oq_w_data.eq(btw.result),
            oq_enable.eq(seq.out_word_done),
        ]

def make_cfu():
    return simple_cfu({
            0: Mnv2RegisterInstruction(),
        })
