#!/usr/bin/env python3
# Copyright 2021 The CFU-Playground Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Parses the data captured by the calculate_once::Capturer

import sys
import argparse

BEGIN = "+++ calculate_once::Capture begin +++"
END = "+++ calculate_once::Capture end +++"


def main():
    parser = argparse.ArgumentParser(description="Extract calculate once data")
    parser.add_argument(
        '--var-name',
        default="model_cache",
        help="Name of the model variable")
    parser.add_argument(
        'infile',
        type=argparse.FileType(
            'r',
            encoding='latin-1'),
        help="Input file containing the strings to be extracted.")
    parser.add_argument(
        'outfile',
        type=argparse.FileType(
            'w',
            encoding='latin-1'),
        help="Output file")

    args = parser.parse_args()
    extracting = False
    for line in args.infile.readlines():
        if BEGIN in line:
            extracting = True
            got_content = False
        elif extracting and END in line:
            extracting = False
        elif extracting:
            line = line.replace('\r', '').replace('\n', '')
            line = line.replace('XXX_cache', args.var_name)
            if got_content and line ==  '':
                got_content = False
            else:
                got_content = True
                print(line, file=args.outfile)


if __name__ == '__main__':
    main()
