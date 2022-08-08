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
from ..util import SimpleElaboratable


class RamMux(SimpleElaboratable):
    """Mux for the input RAM bus.

    The RAM from which data is fetched consists of four, 32 bit wide, 16K word
    deep LRAMs, for a total of 256kBytes storage. The LRAMs are addressed by
    word with the least two significant bits determining which LRAM data are
    stored in.

    Word addresses are thus arranged as follows:

    +--------+--------+--------+--------+
    | LRAM 0 | LRAM 1 | LRAM 2 | LRAM 3 |
    +--------+--------+--------+--------+
    |    0   |    1   |    2   |    3   |
    +--------+--------+--------+--------+
    |    4   |    5   |    6   |    7   |
    +--------+--------+--------+--------+
    |    8   |    9   |   10   |   11   |
    +--------+--------+--------+--------+
    |  ...   |  ...   |  ...   |  ...   |
    +--------+--------+--------+--------+

    Since words are stored in individually readable LRAMs, it is possible to
    ftech four per cycle.

    This mux Connects the four address inputs to the four LRAMs in one of four
    configurations, as directed by the `phase`. The following table shows for
    which LRAM each address line is connected to for a given phase:

    +-------+--------+--------+--------+--------+
    | Phase | addr 0 | addr 1 | addr 2 | addr 3 |
    +-------+--------+--------+--------+--------+
    |   0   |    0   |    3   |    2   |    1   |
    |   1   |    1   |    0   |    3   |    2   |
    |   2   |    2   |    1   |    0   |    3   |
    |   3   |    3   |    2   |    1   |    0   |
    +-------+--------+--------+--------+--------+

    Data for a given address is available at the data output corresponding to
    the address input, one cycle later.

    Attributes
    ----------

    phase: Signal(range(4)), in
        The current phase, indicating which signal is connected to
        which output.

    addr_in: [Signal(14)] * 4, in
        Address to look up in each LRAM.

    data_out: [Signal(32)] * 4, out
        Data retrieved from LRAMs.

    lram_addr: [Signal(14)] * 4, out
        Address for each LRAM bank.

    lram_data: [Signal(32)] * 4, in
        Data as read from addresses provided at previous cycle.
    """

    def __init__(self):
        self.phase = Signal(range(4))
        self.addr_in = [Signal(14, name=f"addr_in{i}") for i in range(4)]
        self.data_out = [Signal(32, name=f"data_out{i}") for i in range(4)]
        self.lram_addr = [Signal(14, name=f"lram_addr{i}") for i in range(4)]
        self.lram_data = [Signal(32, name=f"lram_data{i}") for i in range(4)]

    def connect(self, m, sig_phase, inputs, outputs):
        """Connects inputs and outputs per the given phase."""
        with m.Switch(sig_phase):
            with m.Case(0):
                m.d.comb += outputs[0].eq(inputs[0])
                m.d.comb += outputs[1].eq(inputs[3])
                m.d.comb += outputs[2].eq(inputs[2])
                m.d.comb += outputs[3].eq(inputs[1])
            with m.Case(1):
                m.d.comb += outputs[0].eq(inputs[1])
                m.d.comb += outputs[1].eq(inputs[0])
                m.d.comb += outputs[2].eq(inputs[3])
                m.d.comb += outputs[3].eq(inputs[2])
            with m.Case(2):
                m.d.comb += outputs[0].eq(inputs[2])
                m.d.comb += outputs[1].eq(inputs[1])
                m.d.comb += outputs[2].eq(inputs[0])
                m.d.comb += outputs[3].eq(inputs[3])
            with m.Case(3):
                m.d.comb += outputs[0].eq(inputs[3])
                m.d.comb += outputs[1].eq(inputs[2])
                m.d.comb += outputs[2].eq(inputs[1])
                m.d.comb += outputs[3].eq(inputs[0])

    def elab(self, m):
        last_phase = Signal(range(4))
        m.d.sync += last_phase.eq(self.phase)
        self.connect(m, self.phase, self.addr_in, self.lram_addr)
        self.connect(m, last_phase, self.lram_data, self.data_out)
