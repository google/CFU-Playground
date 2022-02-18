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

import os.path
from amaranth.back import verilog

from gateware.mnv2_cfu import make_cfu

VERILOG_FILENAME = "cfu.v"


def read_file():
    if os.path.exists(VERILOG_FILENAME):
        with open(VERILOG_FILENAME, "r") as f:
            return f.read()
    return None


def main():
    cfu = make_cfu()
    new_verilog = verilog.convert(cfu, name='Cfu', ports=cfu.ports)
    old_verilog = read_file()
    if new_verilog != old_verilog:
        with open(VERILOG_FILENAME, "w") as f:
            f.write(new_verilog)


if __name__ == '__main__':
    main()
