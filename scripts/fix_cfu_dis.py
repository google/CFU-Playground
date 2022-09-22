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


import sys
import re

regnames = ['x0', 'ra', 'sp', 'gp', 
                'tp', 't0', 't1', 't2', 
                's0', 's1', 'a0', 'a1',
                'a2', 'a3', 'a4', 'a5',
                'a6', 'a7', 's2', 's3',
                's4', 's5', 's6', 's7',
                's8', 's9', 's10', 's11',
                't3', 't4', 't5', 't6']


lines = sys.stdin.readlines()

for i in range(len(lines)):
    lin = lines[i]
    lin = lin.replace('\r','')
    lin = lin.replace('\n','')
    #
    # Replace the last word with 'cfu[funct7,funct3]   rd, rs1, rs2'
    #
    # 40000148:       0094280b                0x94280b
    #
    m = re.match(r"^( ?\w+:\s+\w+\s+)(0x[0-9A-Fa-f]+)$", lin)
    if m:
        bits   = int(m.group(2), 0)
        funct7 = (bits >> 25) & 127
        rs2    = (bits >> 20) & 31
        rs1    = (bits >> 15) & 31
        funct3 = (bits >> 12) & 7
        rd     = (bits >> 7) & 31
        op     = f'cfu[{funct7},{funct3}]  {regnames[rd]}, {regnames[rs1]}, {regnames[rs2]}'

        print(m.group(1) + op)

    else:
        n = re.match(r"^( ?\w+:\s+\w+\s+)(\w+)(\s+)(\S+.*)$", lin)
        if n:
            # Add two spaces so regular instruction lines line up with cfu[] lines
            print(n.group(1) + n.group(2) + n.group(3) + "  " + n.group(4))

        else:
            print(lin)

