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
................    45M (     44552519 )  cycles total
................    45M (     44543851 )  cycles total
................    45M (     44551391 )  cycles total
................    45M (     44545105 )  cycles total
................    45M (     44546408 )  cycles total
................    45M (     44542596 )  cycles total
................    45M (     44555114 )  cycles total
................    45M (     44544288 )  cycles total
................    45M (     44545191 )  cycles total
................    45M (     44546846 )  cycles total
................    45M (     44554357 )  cycles total    
    """
    parse_cycles_prints(s)
