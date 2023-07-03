from argparse import ArgumentParser
from pprint import pprint


CYCLES_PER_TICK = 1024

def main(input_path: str):
    layers_cycles = {}
    for i, line in enumerate(open(input_path)):
        if i == 0:      # Skip header
            continue

        idx, name, ticks = line.strip().split(",")
        cur_cycles = layers_cycles.get(name, 0)
        layers_cycles[name] = cur_cycles + int(ticks) * CYCLES_PER_TICK
    pprint(layers_cycles)

    perc_cycles = {}
    all_ticks = sum(layers_cycles.values())
    for name, ticks in layers_cycles.items():
        perc_cycles[name] = ticks / all_ticks * 100
    
    pprint(perc_cycles)






if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    main(parser.parse_args().input)



 AVERAGE_POOL_2D & 40960 & 0.010067299899830367 \\  [1ex]
 CONV_2D & 404055040 & 99.31013827436412 \\  [1ex]
 FULLY_CONNECTED & 19456 & 0.004781967452419424 \\  [1ex]
 MAX_POOL_2D & 2736128 & 0.6724956333086685 \\  [1ex]
 RESHAPE & 1024 & 0.00025168249749575914 \\  [1ex]
 SOFTMAX & 921 & 0.002265142477461832 \\  [1ex]