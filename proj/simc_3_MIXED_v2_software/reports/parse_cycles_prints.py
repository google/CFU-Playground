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
................    44M (     44066395 )  cycles total
................    44M (     44050925 )  cycles total
................    44M (     44065681 )  cycles total
................    44M (     44039586 )  cycles total
................    44M (     44052470 )  cycles total
................    44M (     44046530 )  cycles total
................    44M (     44062859 )  cycles total
................    44M (     44044245 )  cycles total
................    44M (     44050134 )  cycles total
................    44M (     44066152 )  cycles total
................    44M (     44060297 )  cycles total   
    """
    parse_cycles_prints(s)
