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

from nmigen import Signal, unsigned

from .actor import BinaryActor
from .stream import Endpoint


class FlowRestrictor(BinaryActor):
    """A component which passes through a specific number of values through the
    stream when instructed.

    In its resting state, the stream is paused and no packets flow from the
    input to the output. But when a number N arrives at the *release* endpoint,
    N values will be permitted to pass through the stream. Then it goes back to
    its paused state.

    Parameters
    ----------

    payload_type: Shape
      The payload shape/layout for the stream whose flow is being restricted.

    Attributes
    ----------

    input: Endpoint, in
      Input stream.

    output: Endpoint, out
      Output stream.
    """

    def __init__(self, payload_type):
        super().__init__(payload_type, payload_type)
        self.release = Endpoint(unsigned(32))

    def control(self, m):
        release_counter = Signal.like(self.release.payload)
        with m.If(release_counter > 0):
            m.d.comb += self.input.ready.eq(self.output.ready)
            m.d.comb += self.output.valid.eq(self.input.valid)
            with m.If(self.output.is_transferring()):
                m.d.sync += release_counter.eq(release_counter - 1)
        with m.Else():
            m.d.comb += self.release.ready.eq(1)
            with m.If(self.release.is_transferring()):
                m.d.sync += release_counter.eq(self.release.payload)

    def transform(self, m, input, output):
        # Pass through payload unmodified
        m.d.comb += output.eq(input)
