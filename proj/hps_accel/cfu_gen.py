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
import sys

from amaranth import *
from amaranth.back import verilog

from gateware.gen2.hps_cfu import make_cfu as gen2_make_cfu

VERILOG_FILENAME = "cfu.v"

make_cfu_fns = {
    'gen2': gen2_make_cfu,
}


def read_file():
    if os.path.exists(VERILOG_FILENAME):
        with open(VERILOG_FILENAME, "r") as f:
            return f.read()
    return None


def main():
    gen_list = list(make_cfu_fns.keys()).sort()
    parser = argparse.ArgumentParser(description='Generate cfu.v')
    parser.add_argument('gen', metavar='GEN', type=str, choices=gen_list,
                        help=f'Which kind of CFU to generate - one of {gen_list}')
    parser.add_argument('--specialize-nx', action='store_true',
                        help='Generate code for Crosslink/NX-17.')
    args = parser.parse_args()
    if args.gen not in make_cfu_fns.keys():
        print(f'Unexpected GEN {args.gen}')
        sys.exit(5)
    cfu = make_cfu_fns[args.gen](specialize_nx=args.specialize_nx)

    new_verilog = verilog.convert(cfu, name='Cfu', ports=cfu.ports)
    old_verilog = read_file()
    if new_verilog != old_verilog:
        with open(VERILOG_FILENAME, "w") as f:
            f.write(new_verilog)


if __name__ == '__main__':
    main()
