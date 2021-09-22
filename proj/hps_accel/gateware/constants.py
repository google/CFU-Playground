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


__doc__ = """This module contains constants used by both C++ and gateware.

The shared contants are mostly op code numbers and register IDs.
"""

import argparse
import sys


class Constants:
    """Constants shared by C++ and Gateware."""
    ###########################################################################
    # Funct3 codes - used to route CFU to instructions
    INS_SET = 0
    INS_GET = 1
    INS_POST_PROCESS = 2
    INS_PING = 7

    ###########################################################################
    # Register IDs
    # For convenience, readable and writable register IDs are allocated from a
    # shared pool of values 0-127.
    #
    # Generally registers are only writable or readable. Exceptions are noted
    # in the register description.

    # A write of any value to REG_RESET causes the accelerator gateware to be
    # reset and lose all state.
    #
    # Not currently implemented
    REG_RESET = 0

    # Number of 32 bit filter words
    REG_FILTER_NUM_WORDS = 1

    # Number of 32 bit input words - must be divisible by 4
    # Setting this register resets the input store state.
    REG_INPUT_NUM_WORDS = 2

    # Input offset for multiply-accumulate unit
    REG_INPUT_OFFSET = 3

    # Set next filter word
    REG_SET_FILTER = 4

    # Sets next input word and advances the write index.
    REG_SET_INPUT = 5

    # Set output offset
    REG_OUTPUT_OFFSET = 6

    # Sets minimum and maximum activation value
    REG_OUTPUT_MIN = 7
    REG_OUTPUT_MAX = 8

    # These registers contain values 0-3 of the current filter word
    REG_FILTER_0 = 0x10
    REG_FILTER_1 = 0x11
    REG_FILTER_2 = 0x12
    REG_FILTER_3 = 0x13

    # These registers contain values 0-3 of the current input word
    REG_INPUT_0 = 0x18
    REG_INPUT_1 = 0x19
    REG_INPUT_2 = 0x1a
    REG_INPUT_3 = 0x1b

    # A write of any value to this register advances the read index
    # for both the filter store and the input store.
    REG_FILTER_INPUT_NEXT = 0x1f

    # Retrieve result from multiply-accumulate unit
    REG_MACC_OUT = 0x30

    # Set bias, multiplier and shift.
    # Write to OUTPUT_PARAMS_RESET to reset the store.
    # Setting shift causes the three values to be added to the store
    REG_OUTPUT_PARAMS_RESET = 0x40
    REG_OUTPUT_BIAS = 0x41
    REG_OUTPUT_MULTIPLIER = 0x42
    REG_OUTPUT_SHIFT = 0x43

    # Registers for gateware verification
    # Any value n set into this register will be read back as n+1
    REG_VERIFY = 0x70

    # ID is guaranteed to not be a register ID
    REG_INVALID = 0x7f

    ###########################################################################
    # Post Process Function codes
    PP_POST_PROCESS = 0x03 # Post Process accumulator

    ###########################################################################
    # Size limits

    # Maximum number of words in filter
    MAX_FILTER_WORDS = 2048

    # Maximum number of words in input
    MAX_INPUT_WORDS = 256

    # Maximum number of channels in a layer
    MAX_CHANNELS = 64


CC_FILE_HEADER = """// Generated file
// Shared constants generated from gateware/constants.py
#ifndef _GATEWARE_CONSTANTS_H
#define _GATEWARE_CONSTANTS_H
"""

CC_FILE_TAIL = """#endif"""


def main():
    parser = argparse.ArgumentParser(
        description='Write C header file with constants')
    'outfile',
    parser.add_argument('output', metavar='FILE', nargs='?',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='Where to send output')
    args = parser.parse_args()

    with args.output as f:
        print(CC_FILE_HEADER, file=f)
        for name, value in vars(Constants).items():
            if not name.startswith('_'):
                print(f"#define {name} {value}", file=f)
        print(CC_FILE_TAIL, file=f)


if __name__ == "__main__":
    main()
