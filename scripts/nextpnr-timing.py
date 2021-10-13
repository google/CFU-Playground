#!/usr/bin/env python3

import json
import argparse

arg = argparse.ArgumentParser()

arg.add_argument('file', help='JSON timing report')
arg.add_argument('--src', default='', help='Source name')
arg.add_argument('--dst', default='', help='Destination name')
arg.add_argument('--results', default=100, type=int, help='Number of paths reported')
arg.add_argument('--tgt-len', default=0.0, type=float, help='List paths that are longer than this value (in ns)')

args = vars(arg.parse_args())

data = dict()

with open(args['file'], 'r') as file:
    data = json.load(file)

paths = []

for net in data['detailed_net_timings']:
    if args['src'] in net['driver']:
        src = net['driver']
        for endpoint in net['endpoints']:
            if args['dst'] in endpoint['cell']:
                dly = endpoint['delay']
                tgt = endpoint['cell']
                if args['tgt_len'] < dly:
                    paths.append((src, tgt, dly))

paths.sort(key=lambda tup: tup[2], reverse=True)

for path in paths[:args['results']]:
    src, tgt, dly = path
    print(f"{src} -> {tgt} : {dly}")
