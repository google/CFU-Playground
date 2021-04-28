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

import argparse
import os.path

parser = argparse.ArgumentParser(description='Convert binary file to C array')

parser.add_argument('infile', type=argparse.FileType('rb'))
parser.add_argument('outfile', type=argparse.FileType('w', encoding='UTF-8'))

LINE_LEN = 12


def main():
    args = parser.parse_args()
    data = args.infile.read()
    infile_name = args.infile.name
    outfile = args.outfile

    array_name = os.path.splitext(os.path.basename(infile_name))[0]

    def out(s):
        print(s, file=outfile, end='')

    out(f"/* C array created from file {infile_name}.*/\n\n")
    out(f"const unsigned char {array_name}[] = {{\n")

    for n, b in enumerate(data):
        if 0 == (n % LINE_LEN):
            out("\t")
        out(f"0x{b:02x},")
        out("\n" if (LINE_LEN - 1) == (n % LINE_LEN) else " ")

    out(f"\n}};\n\nunsigned int {array_name}_len = {len(data)};")

    args.infile.close()
    outfile.close()

    print(args)


if __name__ == '__main__':
    main()
