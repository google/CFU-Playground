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
from .registerfile import Xetter

class OutputQueueGetter(Xetter):
    """A getter to read from a 32-bit wide FIFO.

    Blocks until data is available.

    Public Interface
    ----------------
    r_data: Signal(32) in
        The FIFO's r_data signal
    r_rdy: Signal() in
        The FIFO's r_rdy signal
    r_en: Signal() out
        The FIFO's r_en signal
    """
    def __init__(self):
        super().__init__()
        self.r_data = Signal(32) 
        self.r_rdy = Signal() 
        self.r_en = Signal() 

    def connect(self, fifo):
        """Returns statements to comb this instance to a fifo"""
        return [
            self.r_data.eq(fifo.r_data),
            self.r_rdy.eq(fifo.r_rdy),
            fifo.r_en.eq(self.r_en),
        ]

    def elab(self, m):
        waiting = Signal()
        with m.If (self.start | waiting):
            m.d.comb += self.r_en.eq(1)
            with m.If(self.r_rdy):
                m.d.comb += [
                    self.output.eq(self.r_data),
                    self.done.eq(1),
                ]
                m.d.sync += waiting.eq(0)
            with m.Else():
                m.d.sync += waiting.eq(1)
        