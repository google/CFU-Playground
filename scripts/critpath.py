#!/usr/bin/env python3
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
#
# Display color-coded floowplan and critical path,
#  using data files written by nextpnr.
# Currently the critical path display is disabled
#  since it hasn't been tested with ice40.
#



import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random

fig, ax = plt.subplots(dpi=200)

# read placement file
with open('placement_data.txt', 'r') as pfile:
    placement_data=pfile.readlines()

if True:
    # read critical path file
    with open('kosagi_fomu_pvt-report.json', 'r') as myfile:
        data=myfile.read()

    # parse file
    obj = json.loads(data)

    # assume first CP is the one we're interested in (maybe print out from/to clk domains)
    cp = obj['critical_paths'][0]['path']
    #print(cp)

    accum = {}
    accum['logic'] = 0.0
    accum['routing'] = 0.0
    accum['clk-to-q'] = 0.0
    accum['setup'] = 0.0

# plot placement data first
for line in placement_data:
  if 'KEY' in line:
    continue
  [type,x,y,color]=line.rstrip().split(' ')
  x = int(x)
  y = int(y)
  if type == 'small':
    rx = random.uniform(0,0.7)
    ry = random.uniform(0,0.7)
    ax.add_patch(mpatches.Rectangle(
                [x+rx, y+ry], 0.1, 0.1,
                color=color, fill=True))
  if type == 'med':
    ax.add_patch(mpatches.Rectangle(
                [x, y-0.2], 1.6, 1.6,
                color=color, ec='white', fill=True))
  if type == 'circle':
    ax.add_patch(mpatches.Circle(
                [x, y+0.5], 0.7,
                color=color, ec='white', fill=True))

ax.set_aspect('equal')
ax.autoscale_view()


if 'cp' in locals():
    xs = []
    ys = []
    for hop in cp:
        dtype = hop['type']
        accum[dtype] += hop['delay']
        fromcell = hop['from']['cell']
        tocell = hop['to']['cell']
        delay = "%.3f" % hop['delay']
        fromloc = hop['from']['loc']
        toloc = hop['to']['loc']
        floc = str(fromloc[0]) + ":" + str(fromloc[1])
        tloc = str(toloc[0]) + ":" + str(toloc[1])
        if toloc != fromloc:
            xs.append(fromloc[0])
            ys.append(fromloc[1])
            xs.append(toloc[0])
            ys.append(toloc[1])
        if 'clk' in dtype:
            print(f"from {tloc} {tocell}  {dtype} --> {delay} ->")
        else:
            print(f"from {floc} {fromcell}  {dtype} --> {delay} ->")

    plt.plot(xs, ys, marker='x', linewidth=3, color='black', label=delay)

    print("");
    for k,v in accum.items():
        delay = "%.2f" % v
        print(f"total {k}: {delay}")

print("");
for line in placement_data:
  if 'KEY' in line:
    print(line.rstrip())
print("KEY Multiplier Circle")
print("KEY Memory Square")

plt.xlim([0, 27])
plt.ylim([0, 32])
# plt.show()
plt.savefig("critpath.png", format="png", dpi=300)
print("Done writing critical path image.\n")
