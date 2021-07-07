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
    # Handle arguments
    parser = argparse.ArgumentParser(description="Extract calculate once data")
    parser.add_argument(
        '--model-name',
        default="model",
        help="Name of the model")
    parser.add_argument(
        'infile',
        type=argparse.FileType(
            'r',
            encoding='latin-1'),
        help="Input file containing the strings to be extracted.")
    parser.add_argument(
        'outfile_cc',
        type=argparse.FileType(
            'w',
            encoding='latin-1'),
        help="Output C++ file")
    parser.add_argument(
        'outfile_h',
        type=argparse.FileType(
            'w',
            encoding='latin-1'),
        help="Output header file file")

    args = parser.parse_args()

    # Extract from output
    extracting = False
    for line in args.infile.readlines():
        if BEGIN in line:
            extracting = True
            got_content = False
        elif extracting and END in line:
            extracting = False
        elif extracting:
            line = line.replace('\r', '').replace('\n', '')
            line = line.replace('__CACHE_NAME__', args.model_name.capitalize())
            if got_content and line == '':
                got_content = False
            else:
                got_content = True
                print(line, file=args.outfile_cc)

    # Make the header file
    print(f"""// Generated header file

#ifndef {args.model_name.upper()}_CACHE_H
#define {args.model_name.upper()}_CACHE_H

calculate_once::Cache *GetCache{args.model_name.capitalize()}();

#endif
""", file=args.outfile_h)

if __name__ == '__main__':
    main()
