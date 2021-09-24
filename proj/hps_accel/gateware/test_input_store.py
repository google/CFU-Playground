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


from nmigen.sim import Delay
from nmigen_cfu import TestBase
from nmigen_cfu.util import pack128

from .input_store import Signal, InputStore

SETTLE_DELAY = Delay(0.25)


class InputStoreTest(TestBase):
    def create_dut(self):
        return InputStore()

    def send(self, stream, payload):
        yield stream.payload.eq(payload)
        yield stream.valid.eq(1)
        yield
        while not (yield stream.ready):
            yield
        yield stream.valid.eq(0)

    def receive(self, stream, expected):
        yield stream.ready.eq(1)
        yield
        while not (yield stream.valid):
            yield
        payload = (yield stream.payload)
        self.assertEqual(payload, expected)
        yield stream.ready.eq(0)
        yield

    def toggle(self, signal):
        yield signal.eq(1)
        yield
        yield signal.eq(0)

    def set_num_words(self, n):
        yield from self.send(self.dut.num_words_input, n)

    def set_input(self, n):
        yield from self.send(self.dut.data_input, n)

    def check_outputs(self, vals):
        yield from self.receive(self.dut.data_output, pack128(*vals))

    def test_simple(self):
        # Fill once and read once
        def process():
            yield from self.set_num_words(20)
            for n in range(100, 120):
                yield from self.set_input(n)
            for n in range(100, 120, 4):
                yield from self.check_outputs(list(range(n, n + 4)))
        self.run_sim(process, False)

    def test_read_many(self):
        # Fill once and read many times
        def process():
            yield from self.set_num_words(20)
            for n in range(100, 120):
                yield from self.set_input(n)
            for i in range(5):
                for n in range(100, 120, 4):
                    yield from self.check_outputs(list(range(n, n + 4)))
        self.run_sim(process, False)

    def test_write_many_read_many(self):
        # Fill once and read many times
        def process():
            for i in range(3):
                num_words = 12 + i * 4
                yield from self.set_num_words(num_words)
                for n in range(100, 100 + num_words):
                    yield from self.set_input(n)
                for j in range(5):
                    for n in range(100, 100 + num_words, 4):
                        yield from self.check_outputs(list(range(n, n + 4)))

        self.run_sim(process, False)

    def test_reset_during_write(self):
        def process():
            yield from self.set_num_words(24)
            for n in range(100, 109):
                yield from self.set_input(n)
            yield from self.set_num_words(20)
            for n in range(100, 120):
                yield from self.set_input(n)
            for n in range(100, 120, 4):
                yield from self.check_outputs(list(range(n, n + 4)))
        self.run_sim(process, False)

    def test_reset_during_read(self):
        def process():
            yield from self.set_num_words(20)
            for n in range(100, 120):
                yield from self.set_input(n)
            for n in range(100, 112, 4):
                yield from self.check_outputs(list(range(n, n + 4)))
            yield from self.set_num_words(20)
            for n in range(100, 120):
                yield from self.set_input(n)
            for n in range(100, 120, 4):
                yield from self.check_outputs(list(range(n, n + 4)))
        self.run_sim(process, False)
