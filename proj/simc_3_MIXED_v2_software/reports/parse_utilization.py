import os
import ast
from pprint import pprint
from argparse import ArgumentParser

# cycles_filepath = os.path.abspath("speed_simulation.txt")

def parse_cycles(cycles_filepath: str):
    # state = "looking_for_cycles"
    state = "looking_for_anchor"

    results = {}
    cur_cfu_name = None

    for line in open(cycles_filepath, 'r'):
        line = line.strip()
        if line.startswith("// CFU V") and state == "looking_for_anchor":
            state = "looking_for_cycles"
            cur_cfu_name = line.strip("//").strip()
            results[cur_cfu_name] = None
        if line.startswith("[") and state == "looking_for_cycles":
            state = "looking_for_anchor"
            results[cur_cfu_name] = ast.literal_eval(line)

    pprint(results)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    args = parser.parse_args()

    parse_cycles(args.input)
