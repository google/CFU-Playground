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


from nmigen.hdl.ast import Cat, Const, signed
from nmigen.sim import Settle, Tick

from nmigen_cfu import TestBase

from .macc import MultiplyAccumulate


class MultiplyAccumulateTest(TestBase):
    def create_dut(self):
        return MultiplyAccumulate(3)

    def test_one_operation(self):
        def process():
            yield self.dut.enable.eq(1)
            yield self.dut.offset.eq(10)
            yield self.dut.operands.payload['inputs'].eq(Cat(
                    Const(0, signed(8)),
                    Const(1, signed(8)),
                    Const(2, signed(8))))
            yield self.dut.operands.payload['filters'].eq(Cat(
                    Const(10, signed(8)),
                    Const(10, signed(8)),
                    Const(10, signed(8))))
            yield self.dut.operands.valid.eq(1)
            yield
            self.assertEqual((yield self.dut.operands.ready), 1)
            # Results take 2 cycles to appear
            self.assertEqual((yield self.dut.result.valid), 0)
            yield
            self.assertEqual((yield self.dut.result.valid), 0)
            yield
            self.assertEqual((yield self.dut.result.valid), 1)
            self.assertEqual((yield self.dut.result.payload), 330)
        self.run_sim(process, True)

    def operand_producer(self, inputs, filters):
        """
        Returns a simulation generator function which feeds the given input and
        filter values to the dut's operands stream.
        """
        def process():
            for i, f in zip(inputs, filters):
                yield self.dut.operands.valid.eq(1)
                yield self.dut.operands.payload['inputs'].eq(
                        Cat(*[Const(x, signed(8)) for x in i]))
                yield self.dut.operands.payload['filters'].eq(
                        Cat(*[Const(x, signed(8)) for x in f]))
                yield Tick()
                while (yield self.dut.operands.ready) != 1:
                    yield Tick()
            yield self.dut.operands.valid.eq(0)
        return process

    def test_pipelined(self):
        offset = 128
        inputs = [
            (-128, 127, 0),
            (-128, 127, -8),
            (33, 45, 2),
        ]
        filters = [
            (-128, 127, 12),
            (-128, 127, 23),
            (-55, -66, -77),
        ]
        expected_results = [33921, 35145, -30283]
        self.sim.add_process(self.operand_producer(inputs, filters))
        def process():
            yield self.dut.offset.eq(offset)
            yield self.dut.enable.eq(1)
            yield self.dut.result.ready.eq(1)
            yield
            # Results take 2 cycles to appear
            self.assertEqual((yield self.dut.result.valid), 0)
            yield
            self.assertEqual((yield self.dut.result.valid), 0)
            yield
            for result in expected_results:
                self.assertEqual((yield self.dut.result.valid), 1)
                self.assertEqual((yield self.dut.result.payload), result)
                yield
            self.assertEqual((yield self.dut.result.valid), 0)
        self.run_sim(process, True)

    def test_pipeline_pauses_when_disabled(self):
        offset = 128
        inputs = [
            (-128, -127, -128),
            (-128, -128, -127),
            (-127, -128, -128),
            (-127, -127, -127),
        ]
        filters = [
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
            (10, 11, 12),
        ]
        expected_results = [2, 6, 7, 33]
        self.sim.add_process(self.operand_producer(inputs, filters))
        def process():
            yield self.dut.offset.eq(offset)
            yield self.dut.result.ready.eq(1)
            # Pipeline doesn't start while enable is low
            for cycle in range(10):
                self.assertEqual((yield self.dut.operands.ready), 0)
                self.assertEqual((yield self.dut.result.valid), 0)
                yield
            # Let values enter first stage of pipeline
            yield self.dut.enable.eq(1)
            yield
            yield self.dut.enable.eq(0)
            for cycle in range(10):
                self.assertEqual((yield self.dut.result.valid), 0)
                yield
            # Let values move to second stage of pipeline
            yield self.dut.enable.eq(1)
            yield
            yield self.dut.enable.eq(0)
            for cycle in range(10):
                self.assertEqual((yield self.dut.result.valid), 0)
                yield
            # Let first result pop out
            yield self.dut.enable.eq(1)
            yield Settle()
            self.assertEqual((yield self.dut.result.valid), 1)
            self.assertEqual((yield self.dut.result.payload), expected_results[0])
            yield
            yield self.dut.enable.eq(0)
            yield Settle()
            for cycle in range(10):
                self.assertEqual((yield self.dut.result.valid), 0)
                yield
            # Let it run, remaining results should pop out
            yield self.dut.enable.eq(1)
            yield
            for result in expected_results[1:]:
                self.assertEqual((yield self.dut.result.valid), 1)
                self.assertEqual((yield self.dut.result.payload), result)
                yield
            for cycle in range(10):
                self.assertEqual((yield self.dut.result.valid), 0)
                yield
        self.run_sim(process, True)
