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

from nmigen import Shape
from nmigen.hdl.rec import Layout, Record

__all__ = ['StreamDefinition', 'Stream', 'connect']


class StreamDefinition:
    """Defines a stream and the guarantees that it makes.

    ignores_valid:
      Stream may use payload without valid being set.

    ignores_ready:
      Stream may present a new payload while valid is asserted
      and before ready is asserted.
    """

    @staticmethod
    def cast(obj, src_loc_at=0, ignores_ready=False, ignores_valid=False):
        if isinstance(obj, StreamDefinition):
            return StreamDefinition(
                paylad_type=obj.payload_type,
                ignores_ready=obj.ignores_ready,
                ignores_valid=obj.ignores_valid)
        else:
            return StreamDefinition(
                payload_type=obj, src_loc_at=1 + src_loc_at)

    def __init__(self, *, payload_type,
                 ignores_ready=False, ignores_valid=False, src_loc_at=0):
        self.ignores_ready = ignores_ready
        self.ignores_valid = ignores_valid
        self.payload_type = payload_type
        self.layout = Layout([
            ("valid", Shape()),
            ("ready", Shape()),
            ("payload", payload_type),
        ],
            src_loc_at=1 + src_loc_at
        )


class Stream:
    """Interface to a stream
    
    Parameters
    ----------

    definition: StreamDefintion
      Specifies the payload type and other parameters of this type.
    
    """

    def __init__(self, definition=None, *, payload_type=None, name=None, src_loc_at=0):
        if definition is None:
            self.definition = StreamDefinition(
                payload_type=payload_type,
                src_loc_at=src_loc_at + 1)
        else:
            self.definition = StreamDefinition.cast(definition)
        self._record = Record(
            self.definition.layout,
            name=name,
            src_loc_at=1 + src_loc_at)
        self.valid = self._record.valid
        self.ready = self._record.ready
        self.payload = self._record.payload

    @staticmethod
    def like(other):
        return Stream(other.definition)

    def is_transferring(self):
        """Is a transfer taking place this cycle?

        True iff valid and ready are both asserted.
        """
        return self.valid & self.ready


def connect(from_stream, to_stream):
    """Convenience function for connecting an upstream to a downstream.

    Examples:

    m.d.comb += connect(one_components_output, another_components_input)
    m.d.comb += connect(my_input, child_input)

    Arguments
    ---------
    from_stream:
        The upstream side of the stream. Presents payload and valid.
    to_stream:
        The downstream side of the stream. Presents ready.

    Result
    ------
    A list of statements.
    """
    return [
        to_stream.valid.eq(from_stream.valid),
        to_stream.payload.eq(from_stream.payload),
        from_stream.ready.eq(to_stream.ready),
    ]
