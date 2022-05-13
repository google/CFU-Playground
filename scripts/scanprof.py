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

totals =  {}

n = 1
cyc = 0
total_cyc = 0
lines = sys.stdin.readlines()

for i in range(len(lines)):
    lin = lines[i]
    lin = lin.replace('\r','')
    lin = lin.replace('\n','')
    #m = re.match(r".*PROFILER\", \"(.*)\", (\d+)", lin)
    m = re.match(r"(\d+),(.*),(\d+)", lin)
    if m:
        layer = m.group(1)
        tfop = m.group(2)
        cyc = m.group(3)
        print(n, ",", tfop, ",", cyc)
        n = n+1
        if tfop not in totals:
            totals[tfop] = 0
        totals[tfop] += int(cyc)
        total_cyc += int(cyc)

keys = sorted(totals, key=totals.get)

print("\nTotals\n")
for k in list(keys):
    print("%30s  %12d   (%3.1fM)" % (k, totals[k], totals[k]/1e3))

print("\nGrand Total: %3.1fM\n\n" % (total_cyc / 1e3))
