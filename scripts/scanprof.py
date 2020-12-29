#!/usr/bin/env python

import sys
import re

totals =  {}

n = 1
cyc = 0
lines = sys.stdin.readlines()

for i in range(len(lines)):
    lin = lines[i]
    lin = lin.replace('\r','')
    m = re.match(r"(\S+) took (\d+) cyc", lin)
    if m:
        tfop = m.group(1)
        cyc = m.group(2)
        print(n, ",", tfop, ",", cyc)
        n = n+1
        if tfop not in totals:
            totals[tfop] = 0
        totals[tfop] += int(cyc)

print("\nTotals\n")
for k in list(totals):
    print(k, ",", totals[k])

