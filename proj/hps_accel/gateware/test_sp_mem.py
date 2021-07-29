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


from nmigen.sim import Settle
from nmigen_cfu import TestBase

from .sp_mem import MemoryParameters, SinglePortMemory


class SinglePortMemoryTest(TestBase):
    def create_dut(self):
        params = MemoryParameters(width=16, depth=32)
        return SinglePortMemory(params)

    def test(self):
        X = XX = None
        A, B, C, D, E, F, G, H, I = range(11, 20)

        # Description
        # ((write_sink.valid,
        #   write_sink.addr,
        #   write_sink.data,
        #   read_addr_sink.valid,
        #   read_addr_sink.addr,
        #   read_data_source.ready),
        # (read_addr_sink.ready,
        #  read_data_source.valid,
        #  read_data_source.data)),
        DATA = [
            # Write Addr 11
            ((1, 11, A, 0, XX, 1), (0, 0, X)),
            # Write Addr 12
            ((1, 12, B, 0, XX, 1), (0, 0, X)),
            # Write Addr 13
            ((1, 13, C, 0, XX, 1), (0, 0, X)),
            # Read Addr 11
            ((0, XX, X, 1, 11, 1), (1, 0, X)),
            # Output data for Addr1
            ((0, XX, X, 0, XX, 1), (1, 1, A)),
            # Burst read - all ready
            ((0, XX, X, 1, 11, 1), (1, 0, X)),
            ((0, XX, X, 1, 12, 1), (1, 1, A)),
            ((0, XX, X, 1, 13, 1), (1, 1, B)),
            ((0, XX, X, 0, XX, 1), (1, 1, C)),
            # Idle
            ((0, XX, X, 0, XX, 1), (1, 0, X)),
            # Bust read, but data consumer not always ready
            ((0, XX, X, 1, 11, 0), (1, 0, X)),
            ((0, XX, X, 1, 12, 0), (0, 1, A)),
            ((0, XX, X, 1, 12, 0), (0, 1, A)),
            ((0, XX, X, 1, 12, 1), (1, 1, A)),
            ((0, XX, X, 1, 13, 0), (0, 1, B)),
            ((0, XX, X, 1, 13, 1), (1, 1, B)),
            ((0, XX, X, 1, 11, 1), (1, 1, C)),
            ((0, XX, X, 0, XX, 1), (1, 1, A)),
            # Back to Idle
            ((0, XX, X, 0, XX, 1), (1, 0, X)),
            # Read blocked by single write
            ((1, 14, D, 1, 11, 1), (0, 0, X)),
            ((0, XX, X, 1, 11, 1), (1, 0, X)),
            # Burst write blocks read
            ((1, 15, E, 1, 12, 1), (0, 1, A)),
            ((1, 16, F, 1, 12, 0), (0, 0, X)),
            ((0, XX, X, 1, 12, 0), (1, 0, X)),
            # Consumer takes read data while write is happening
            # New read starts while write still underway
            ((1, 17, G, 0, XX, 0), (0, 1, B)),
            ((1, 17, G, 1, 13, 0), (0, 1, B)),
            ((1, 18, H, 1, 13, 1), (0, 1, B)),
            ((1, 19, I, 1, 13, 1), (0, 0, X)),
            # Read delayed by write - takes one cycle to produce a result after
            # write burst completes
            ((0, XX, X, 1, 13, 1), (1, 0, X)),
            ((0, XX, X, 0, XX, 1), (1, 1, C)),
            # Have an idle cycle
            ((0, XX, X, 0, XX, 1), (1, 0, X)),
        ]

        def process():
            for n, (inputs, expected) in enumerate(DATA):
                with self.subTest(n=n, inputs=inputs, expected=expected):
                    ws_valid, ws_addr, ws_data, ras_valid, ras_addr, rds_ready = inputs
                    yield self.dut.write_sink.valid.eq(ws_valid)
                    if ws_addr is not None:
                        yield self.dut.write_sink.payload.addr.eq(ws_addr)
                    if ws_data is not None:
                        yield self.dut.write_sink.payload.data.eq(ws_data)
                    yield self.dut.read_addr_sink.valid.eq(ras_valid)
                    if ras_addr is not None:
                        yield self.dut.read_addr_sink.payload.eq(ras_addr)
                    yield self.dut.read_data_source.ready.eq(rds_ready)
                    yield Settle()
                    ras_ready, rds_valid, rds_data = expected
                    self.assertTrue((yield self.dut.write_sink.ready))
                    self.assertEqual((yield self.dut.read_addr_sink.ready), ras_ready)
                    self.assertEqual((yield self.dut.read_data_source.valid), rds_valid)
                    if rds_data is not None:
                        self.assertEqual((yield self.dut.read_data_source.payload), rds_data)
                    yield
        self.run_sim(process, False)
