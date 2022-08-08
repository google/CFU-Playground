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

"""Tests for uitls.py"""

from amaranth import Signal, Module
from ..util import TestBase
from .utils import delay
import random


class DelayTest(TestBase):
    """Tests the delay function."""

    def create_dut(self):
        module = Module()
        self.in_ = Signal(8)
        self.outs_ = delay(module, self.in_, 3)
        return module

    def test_it(self):
        # data with 3 zeros at end, since we are delaying by 3
        data = [random.randrange(256) for _ in range(20)] + [0] * 3

        def process():
            for i in range(len(data)):
                yield self.in_.eq(data[i])
                yield
                for j in range(3):
                    self.assertEqual((yield self.outs_[j]), data[i - j])
        self.run_sim(process, False)
