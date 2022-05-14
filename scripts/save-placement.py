#!/bin/bash
# Copyright 2022 The CFU-Playground Authors
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
# 
# When executed by nextpnr-ice40 using the "--pre-route" option,
#  this saves placement data in a file "placement_data.txt".


import sys

print("\nSaving placement data...\n")

COLOR_TABLE = [
  ('Vex', 'gray'),
  ('Cfu', 'seagreen'),
  ('litespi', 'blue'),
  ('cdcusbphy', 'red'),
  ('_usb_', 'red'),
]

with open('placement_data.txt', 'w') as f:
  for cell, cellinfo in ctx.cells:
    if cellinfo.bel:
        bel = cellinfo.bel
        #print(cell, file=f)
        #print(bel, file=f)
        loc = ctx.getBelLocation(bel)
        x = int(loc.x)
        y = int(loc.y)

        color = 'black'
        for match, c in COLOR_TABLE:
          if match in cell:
            color = c

        mul = "DSP" in cell
        ebr = "/ram" in bel

        # Set color for LRAMs
        lram = "spram_" in bel
        color= 'tan' if lram else color

        if mul:
            print(f"circle {x} {y} {color}", file=f)
        elif ebr or lram:
            print(f"med {x} {y} {color}", file=f)
        else:
            print(f"small {x} {y} {color}", file=f)

  for i, (match, c) in enumerate(COLOR_TABLE):
    print(f"KEY {match} {c}", file=f)
  print("KEY LiteX black", file=f)

print("\nDone\n")

sys.exit()
