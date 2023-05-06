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
................    29M (     28745877 )  cycles total
................    29M (     28737209 )  cycles total
................    29M (     28744749 )  cycles total
................    29M (     28738463 )  cycles total
................    29M (     28739766 )  cycles total
................    29M (     28735954 )  cycles total
................    29M (     28748472 )  cycles total
................    29M (     28737646 )  cycles total
................    29M (     28738549 )  cycles total
................    29M (     28740204 )  cycles total
................    29M (     28747715 )  cycles total    
    """
    parse_cycles_prints(s)
