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
from amaranth.sim import Settle, Delay

from amaranth_cfu import InstructionTestBase, DualPortMemory, TestBase

from .store import CircularIncrementer, InputStore, StoreSetter
from .registerfile import RegisterSetter, Xetter, RegisterFileInstruction


class _CircularGetter(Xetter):
    """Wraps a Circular Reader.

    For testing.

    Public Interface
    ----------------
    next: Signal output
        Go to next address
    r_data: Signal(width) output
        Next address
    """

    def __init__(self):
        super().__init__()
        self.next = Signal()
        self.r_data = Signal(32)

    def elab(self, m):
        m.d.comb += [
            # Output always ready
            self.done.eq(1),
            # Output is whatever reader says
            self.output.eq(self.r_data),
            # Step reader on every start
            self.next.eq(self.start),
        ]


class _PSRegisterFileInstruction(RegisterFileInstruction):
    def elab_xetters(self, m):
        m = self.m
        # Set up a single memory store, such as used as a per-channel parameter
        # store
        m.submodules['dp'] = dp = DualPortMemory(
            width=8, depth=32, is_sim=True)
        m.submodules['inc'] = inc = CircularIncrementer(32)
        m.submodules['psset'] = psset = StoreSetter(8, 1, 32)
        m.submodules['psget'] = psget = _CircularGetter()
        m.submodules['reg'] = reg = RegisterSetter()
        m.d.comb += [
            # Restart param store when reg is set
            psset.restart.eq(reg.set),
            inc.restart.eq(reg.set),
            # Incrementer is limited to number of items set and increments
            # whenever an item is retrieved
            inc.limit.eq(psset.count),
            inc.next.eq(psget.next),
            # Hook memory up to various components
            psget.r_data.eq(dp.r_data),
            dp.r_addr.eq(inc.r_addr),
        ]
        m.d.comb += psset.connect_write_port([dp])
        self.register_xetter(1, psset)
        self.register_xetter(2, psget)
        self.register_xetter(9, reg)


class ParamStoreTest(InstructionTestBase):
    def create_dut(self):
        return _PSRegisterFileInstruction()

    def test(self):
        self.verify([
            # Restart
            (9, 0, 0, 0),
            # Put a thing in memory
            (1, 12, 0, 0),
            # Read it, twice.
            (2, 0, 0, 12),
            (2, 0, 0, 12),
            # Put more things in memory
            (1, 13, 0, 0),
            (1, 14, 0, 0),
            (1, 15, 0, 0),
            # Read it all back
            (2, 0, 0, 12),
            (2, 0, 0, 13),
            (2, 0, 0, 14),
            (2, 0, 0, 15),
            (2, 0, 0, 12),
            (2, 0, 0, 13),
        ], False)


TEST_INPUT_STORE_DEPTH = 32


class InputStoreTest(TestBase):
    def create_dut(self):
        return InputStore(TEST_INPUT_STORE_DEPTH)

    def run_test(self, data, write_trace):
        def process():
            for n, (inputs, outputs) in enumerate(data):
                restart, input_depth, w_data, w_en, r_next, r_finished = inputs
                yield self.dut.restart.eq(restart)
                if input_depth is not None:
                    yield self.dut.input_depth.eq(input_depth)
                yield self.dut.w_data.eq(w_data)
                yield self.dut.w_en.eq(w_en)
                yield self.dut.r_next.eq(r_next)
                yield self.dut.r_finished.eq(r_finished)
                yield Delay(0.25)
                w_ready, r_ready, r_data = outputs
                if w_ready is not None:
                    self.assertEqual((yield self.dut.w_ready), w_ready, f"cycle={n}")
                if r_ready is not None:
                    self.assertEqual((yield self.dut.r_ready), r_ready, f"cycle={n}")
                if r_data is not None:
                    self.assertEqual((yield self.dut.r_data), r_data, f"cycle={n}")
                yield
        self.run_sim(process, write_trace)

    def test_restart_on_init(self):
        def data():
            yield ((0, 4, 0, 0, 0, 0), (1, 0, 0))
            yield ((1, 4, 0, 0, 0, 0), (1, 0, 0))
        self.run_test(data(), False)

    def set_input_depth(self, n):
        # set depth and restart
        return ((1, n, 0, 0, 0, 0), (None, None, None))

    def read_data(self, value):
        # Read value assuming r_ready is set
        return ((0, None, 0, 0, 1, 0), (None, 1, value))

    def write_data(self, value):
        # Write value assuming w_ready is set
        return ((0, None, value, 1, 0, 0), (1, None, None))

    def read_write_data(self, value_read, value_write):
        # Check r_ready and w_ready both set
        return ((0, None, value_write, 1, 1, 0), (1, 1, value_read))

    def check_read_write_ready(self, r_ready, w_ready):
        return ((0, None, 0, 0, 0, 0), (w_ready, r_ready, None))

    def no_input(self):
        return ((0, None, 0, 0, 0, 0), (None, None, None))

    def finish_read(self):
        return ((0, None, 0, 0, 0, 1), (None, None, None))

    def test_size8(self):
        def process():
            # write buffer 0 and read it back
            yield self.set_input_depth(8)
            for d in [111, 222, 333, 444, 555, 666, 777, 888]:
                yield self.write_data(d)
            yield self.no_input()
            for d in [111, 222, 333, 444, 555, 666, 777, 888]:
                yield self.read_data(d)
            # write buffer 1 and read buffer 0
            for d in [1, 2, 3, 4, 5, 6, 7, 8]:
                yield self.write_data(d)
            for d in [111, 222, 333, 444, 555, 666, 777, 888]:
                yield self.read_data(d)
            # Read buffer 1
            yield self.finish_read()
            yield self.no_input()
            for d in [1, 2, 3, 4, 5, 6, 7, 8]:
                yield self.read_data(d)
            # Read buffer 0 while writing buffer 1, then read buffer 1
            for (r, w) in zip(range(1, 9), range(101, 109)):
                yield self.read_write_data(r, w)
            yield self.finish_read()
            yield self.no_input()
            for d in range(101, 109):
                yield self.read_data(d)
        self.run_test(process(), False)

    def test_size2(self):
        # Smallest size that will be used
        def process():
            # write buffer 0 and read it back
            yield self.set_input_depth(2)
            for d in [111, 222]:
                yield self.write_data(d)
            yield self.no_input()
            for d in [111, 222]:
                yield self.read_data(d)
            # write buffer 1 and read buffer 0
            for d in [1, 2]:
                yield self.write_data(d)
            for d in [111, 222]:
                yield self.read_data(d)
            # Read buffer 1
            yield self.finish_read()
            yield self.no_input()
            for d in [1, 2]:
                yield self.read_data(d)
            # Read buffer 0 while writing buffer 1, then read buffer 1
            for (r, w) in [(1, 101), (2, 102)]:
                yield self.read_write_data(r, w)
            yield self.finish_read()
            yield self.no_input()
            for d in [101, 102]:
                yield self.read_data(d)
        self.run_test(process(), False)

    def test_size30(self):
        # Larger size
        def process():
            yield self.set_input_depth(30)
            for d in range(100, 130):
                yield self.write_data(d)
            yield self.no_input()
            for d in range(100, 130):
                yield self.read_data(d)
            for r, w in zip(range(100, 130), range(200, 230)):
                yield self.read_write_data(r, w)
            yield self.check_read_write_ready(True, False)
            for d in range(100, 130):
                yield self.read_data(d)
            yield self.finish_read()
            yield self.check_read_write_ready(False, True)
            yield self.check_read_write_ready(True, True)
            for d in range(200, 230):
                yield self.read_data(d)
        self.run_test(process(), False)

    def test_size20(self):
        # multiple of 4
        def process():
            yield self.set_input_depth(20)
            for d in range(100, 120):
                yield self.write_data(d)
            yield self.no_input()
            for d in range(100, 120):
                yield self.read_data(d)
            for r, w in zip(range(100, 120), range(200, 220)):
                yield self.read_write_data(r, w)
            yield self.check_read_write_ready(True, False)
            for d in range(100, 120):
                yield self.read_data(d)
            yield self.finish_read()
            yield self.check_read_write_ready(False, True)
            yield self.check_read_write_ready(True, True)
            for d in range(200, 220):
                yield self.read_data(d)
        self.run_test(process(), False)
