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
"""This script is executed by nextpnr-nexus to generate a placement plot."""


import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random

fig, ax = plt.subplots(dpi=200)

print("\nGenerating placement image...\n")

for cell, cellinfo in ctx.cells:
    if cellinfo.bel:
        #print("Cell %s   %s" % (cell, cellinfo.type))
        bel = cellinfo.bel
        loc = ctx.getBelLocation(bel)
        x = int(loc.x)
        y = int(loc.y)

        color = 'black'
        COLOR_TABLE = [
          ('Vex', 'gray'),
          ('Cfu', 'seagreen'),
          ('Cfu.core', 'lime'),
          ('Cfu.core.sysarray', 'red'),
          ('Cfu.core.ppp', 'violet'),
          ('Cfu.core.f0', 'yellow'),
          ('Cfu.core.f1', 'tan'),
        ]
        for match, c in COLOR_TABLE:
          if match in cell:
            color = c

        mul = "MULT" in bel
        ebr = "EBR" in bel

        # Set color for LRAMs
        lram = "SP512K" in cell
        arena = "DPSC512K" in cell
        color='tan' if arena else ('bisque' if lram else color)

        if mul:
            ax.add_patch(mpatches.Circle(
                [x, y+0.5], 0.7,
                color=color,
                ec='white',
                fill=True
                ))
        elif ebr or lram or arena:
            ax.add_patch(mpatches.Rectangle(
                [x, y-0.2], 1.6, 1.6,
                color=color,
                ec='white',
                fill=True
                ))
        else:
            rx = random.uniform(0,0.7)
            ry = random.uniform(0,0.7)
            ax.add_patch(mpatches.Rectangle(
                [x+rx, y+ry], 0.1, 0.1,
                color=color,
                fill=True
                ))

ax.set_aspect('equal')
nl = ',\n'
comma = ', '
ax.set_title(''.join([f'{match}={c}{nl if i&1 else comma}' for i, (match, c) in enumerate(COLOR_TABLE)]) +
    'Black=LiteX, Circle=DSP, Square=MEM')
ax.autoscale_view()
#plt.show()
plt.savefig("placement.png", format="png")
print("Done\n")

# Uncommenting this will cause nextpnr to stop without running routing (but still produce the placement plot)
# exit()
