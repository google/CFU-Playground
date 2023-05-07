import numpy as np


def parse_cycles_prints(prints: str):
    lines = prints.split("\n")
    cycless = []
    for line in lines:
        left_idx = line.find("(")
        right_idx = line.find(")")
        if left_idx < 0 or right_idx < 0:
            continue
        cycles_str = line[left_idx + 1 : right_idx]
        cycles = int(cycles_str)
        cycless.append(cycles)
        print(line.replace(".", "").strip())
    print(cycless)
    print(f"mean: {np.mean(cycless)}")
    print(f"median: {np.median(cycless)}")
    print(f"std: {np.std(cycless)}")



if __name__ == "__main__":
    s = """
................    66M (     66083613 )  cycles total
................    66M (     66065016 )  cycles total
................    66M (     66081619 )  cycles total
................    66M (     66056950 )  cycles total
................    66M (     66064052 )  cycles total
................    66M (     66063548 )  cycles total
................    66M (     66078644 )  cycles total
................    66M (     66036291 )  cycles total
................    66M (     66037426 )  cycles total
................    66M (     66046356 )  cycles total
................    66M (     66053939 )  cycles total   
    """
    parse_cycles_prints(s)
