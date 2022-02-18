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

"""Utility functions."""

from amaranth import Signal, unsigned


def unsigned_upto(maximum_value):
    """Creates a shape of a size to hold maximum_value"""
    return unsigned(maximum_value.bit_length())


def delay(m, input_, cycles):
    result = [input_]
    for i in range(cycles):
        delayed = Signal.like(input_, name=f"{input_.name}_d{i+1}")
        m.d.sync += delayed.eq(result[-1])
        result.append(delayed)
    return result


def as_signed_int32_array(byte_array):
    """Interprets array of byte values as signed 32 bit ints."""
    def int32(a, b, c, d):
        unsigned = a + (b << 8) + (c << 16) + (d << 24)
        return unsigned if unsigned < (2**31) else (unsigned - 2**32)

    return [int32(*byte_array[i:i + 4]) for i in range(0, len(byte_array), 4)]


def as_unsigned_int32_array(byte_array):
    """Interprets array of byte values as unsigned 32 bit ints."""
    def uint32(a, b, c, d):
        return a + (b << 8) + (c << 16) + (d << 24)

    return [uint32(*byte_array[i:i + 4]) for i in range(0, len(byte_array), 4)]
