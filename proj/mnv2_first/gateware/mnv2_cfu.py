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

from nmigen.hdl.ast import Mux, Signal
from nmigen_cfu import Cfu, DualPortMemory, is_pysim_run

from .post_process import PostProcessor
from .store import CircularIncrementer, FilterValueFetcher, InputStore, InputStoreSetter, NextWordGetter, StoreSetter
from .registerfile import RegisterFileInstruction, RegisterSetter
from .macc import Macc4Run1, Madd4Pipeline

OUTPUT_CHANNEL_PARAM_DEPTH = 512
FILTER_DATA_MEM_DEPTH = 512
MAX_PER_PIXEL_INPUT_WORDS = 1024


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
            width=32, depth=OUTPUT_CHANNEL_PARAM_DEPTH, is_sim=is_pysim_run())
        m.submodules[f'{name}_inc'] = inc = CircularIncrementer(
            OUTPUT_CHANNEL_PARAM_DEPTH)
        m.submodules[f'{name}_set'] = psset = StoreSetter(
            32, 1, OUTPUT_CHANNEL_PARAM_DEPTH)
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
                width=32, depth=FILTER_DATA_MEM_DEPTH, is_sim=is_pysim_run())
            dps.append(dp)
        m.submodules[f'{name}_set'] = fvset = StoreSetter(
            32, 4, FILTER_DATA_MEM_DEPTH)
        self.register_xetter(reg_num, fvset)
        m.d.comb += [
            # Restart param store when reg is set
            fvset.restart.eq(restart_signal),
        ]
        m.d.comb += fvset.connect_write_port(dps)
        return dps, fvset.count, fvset.updated

    def _make_input_store(self, m, name, restart_signal, input_depth):
        m.submodules[f'{name}'] = ins = InputStore(MAX_PER_PIXEL_INPUT_WORDS)
        m.submodules[f'{name}_set'] = insset = InputStoreSetter()
        m.d.comb += insset.connect(ins)
        self.register_xetter(25, insset)
        _, read_finished = self._make_setter(m, 112, 'mark_read')
        m.d.comb += [
            ins.restart.eq(restart_signal),
            ins.input_depth.eq(input_depth),
            ins.r_finished.eq(read_finished),
        ]
        return ins

    def _make_macc_4_run_1(self, m, reg_num, name, input_offset, input_depth):
        """Constructs and registers an implicit macc4 instruction

        """
    
        m.submodules[name] = xetter = Macc4Run1(FILTER_DATA_MEM_DEPTH * 4)
        self.register_xetter(reg_num, xetter)
        m.submodules[f"{name}_madd4"] = madd4 = Madd4Pipeline()

        m.d.comb += [
            xetter.input_offset.eq(input_offset),
            xetter.input_depth.eq(input_depth),
        ]
        return xetter

    def _make_filter_value_getter(self, m, fvf):
        fvg_next = Signal()
        if is_pysim_run():
            m.submodules['fvg'] = fvg = NextWordGetter()
            m.d.comb += [
                fvf.next.eq(fvg.next),
                fvg.data.eq(fvf.data),
                fvg.ready.eq(1),
                fvg_next.eq(fvg.next),
            ]
            self.register_xetter(110, fvg)
        return fvg_next

    def _make_input_store_getter(self, m, ins):
        insget_next = Signal()
        if is_pysim_run():
            m.submodules['insget'] = insget = NextWordGetter()
            m.d.comb += [
                insget.data.eq(ins.r_data),
                insget.ready.eq(ins.r_ready),
                ins.r_next.eq(insget.next),
                insget_next.eq(insget.next),
            ]
            self.register_xetter(111, insget)
        return insget_next

    def elab_xetters(self, m):
        input_depth, set_id = self._make_setter(m, 10, 'set_input_depth')
        self._make_setter(m, 11, 'set_output_depth')
        input_offset, _ = self._make_setter(m, 12, 'set_input_offset')
        output_offset, _ = self._make_setter(m, 13, 'set_output_offset')
        activation_min, _ = self._make_setter(m, 14, 'set_activation_min')
        activation_max, _ = self._make_setter(m, 15, 'set_activation_max')

        _, restart = self._make_setter(m, 20, 'set_output_batch_size')
        multiplier, multiplier_next = self._make_output_channel_param_store(
            m, 21, 'store_output_multiplier', restart)
        shift, shift_next = self._make_output_channel_param_store(
            m, 22, 'store_output_shift', restart)
        bias, bias_next = self._make_output_channel_param_store(
            m, 23, 'store_output_bias', restart)
        fv_mems, fv_count, fv_updated = self._make_filter_value_store(
            m, 24, 'store_filter_values', restart)

        m.submodules['fvf'] = fvf = FilterValueFetcher(FILTER_DATA_MEM_DEPTH)
        m.d.comb += fvf.connect_read_ports(fv_mems)
        m.d.comb += [
            # fetcher only works for multiples of 4, and only for multiples of
            # 4 > 8
            fvf.limit.eq(fv_count & ~0x3),
            fvf.updated.eq(fv_updated),
            fvf.restart.eq(restart),
        ]
        ins = self._make_input_store(m, 'ins', set_id, input_depth)

        # Make getters for filter and instuction next words
        # Only required during pysim unit tests
        fvg_next = self._make_filter_value_getter(m, fvf)
        insget_next = self._make_input_store_getter(m, ins)


        m.submodules['pp'] = pp = PostProcessor()
        m.d.comb += [
            pp.offset.eq(output_offset),
            pp.activation_min.eq(activation_min),
            pp.activation_max.eq(activation_max),
            pp.bias.eq(bias),
            pp.multiplier.eq(multiplier),
            pp.shift.eq(shift),
        ]


        # MACC 4
        m.submodules['m4r1'] = m4r1 = Macc4Run1(FILTER_DATA_MEM_DEPTH * 4)
        self.register_xetter(32, m4r1)
        m.submodules['m4r1_madd4'] = madd4 = Madd4Pipeline()
        
        m.d.comb += [
            m4r1.input_depth.eq(input_depth),
            madd4.offset.eq(input_offset),
            madd4.f_data.eq(fvf.data),
            madd4.i_data.eq(ins.r_data),
            fvf.next.eq(m4r1.madd4_start | fvg_next),
            ins.r_next.eq(m4r1.madd4_start | insget_next),
            m4r1.madd4_inputs_ready.eq(ins.r_ready),
            m4r1.madd4_result.eq(madd4.result),
            
            pp.accumulator.eq(m4r1.pp_accumulator),
            m4r1.pp_result.eq(pp.result),
            bias_next.eq(m4r1.pp_start),
            multiplier_next.eq(m4r1.pp_start),
            shift_next.eq(m4r1.pp_start),
        ]


class Mnv2Cfu(Cfu):
    """Simple CFU for Mnv2.

    Most functionality is provided through a single set of registers.
    """

    def __init__(self):
        super().__init__({
            0: Mnv2RegisterInstruction(),
        })

    def elab(self, m):
        super().elab(m)


def make_cfu():
    return Mnv2Cfu()
