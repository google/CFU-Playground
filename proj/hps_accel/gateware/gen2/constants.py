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

"""Constants shared between gateware and C++"""

import argparse
import sys


class Constants:
    ###########################################################################
    # Funct3 codes - used to route CFU to instructions
    INS_SET = 0
    INS_GET = 1
    INS_PING = 7

    # Registers
    REG_VERIFY = 0

    # Write any value to start or reset to trigger accelerator start or reset
    REG_ACCELERATOR_START = 1
    REG_ACCELERATOR_RESET = 2

    # Write data to filter store at address
    # in0 = (store << 16 | addr), in1  = data
    REG_FILTER_WRITE = 3

    # Configuration values
    REG_INPUT_OFFSET = 4
    REG_NUM_FILTER_WORDS = 5
    REG_OUTPUT_OFFSET = 6
    REG_OUTPUT_ACTIVATION_MIN = 7
    REG_OUTPUT_ACTIVATION_MAX = 8
    REG_INPUT_BASE_ADDR = 9
    REG_NUM_PIXELS_X = 10
    REG_PIXEL_ADVANCE_X = 11
    REG_PIXEL_ADVANCE_Y = 12
    REG_NUM_REPEATS = 13
    REG_OUTPUT_CHANNEL_DEPTH = 14
    REG_NUM_OUTPUT_VALUES = 15

    # For post process parameters. Writing multiplier sends all values
    REG_POST_PROCESS_BIAS = 16
    REG_POST_PROCESS_SHIFT = 17
    REG_POST_PROCESS_MULTIPLIER = 18

    # Gets the output value
    REG_OUTPUT_WORD = 19

    # Number of items in FIFO
    REG_FIFO_ITEMS = 20

    # Maximum number of 8-bit channels per pixel
    MAX_CHANNEL_DEPTH = 512

    # Height (A dimension, aka activation values, aka inputs)
    SYS_ARRAY_HEIGHT = 4

    # Width (B dimension, aka filter values) of the Systolic array
    SYS_ARRAY_WIDTH = 2

    # Total Number of MACC blocks in Systolic array
    SYS_ARRAY_MACC_BLOCKS = SYS_ARRAY_HEIGHT * SYS_ARRAY_WIDTH

    # Total number of separate store
    NUM_FILTER_STORES = SYS_ARRAY_WIDTH

    # Depth of filter storage, per store
    FILTER_WORDS_PER_STORE = 512


CC_FILE_HEADER = """// Generated file
// Shared constants generated from gen2/gateware/constants.py
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
