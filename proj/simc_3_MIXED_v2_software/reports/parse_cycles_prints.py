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
        # print(line.replace(".", "").strip())
    print(cycless)
    print(f"mean: {np.mean(cycless)}")
    print(f"median: {np.median(cycless)}")
    print(f"std: {np.std(cycless)}")



if __name__ == "__main__":
    s = """
................    29M (     28805282 )  cycles total
................    29M (     28796614 )  cycles total
................    29M (     28804154 )  cycles total
................    29M (     28797868 )  cycles total
................    29M (     28799171 )  cycles total
................    29M (     28795359 )  cycles total
................    29M (     28807877 )  cycles total
................    29M (     28797051 )  cycles total
................    29M (     28797954 )  cycles total
................    29M (     28799609 )  cycles total
................    29M (     28807120 )  cycles total   
    """
    parse_cycles_prints(s)
