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
................    41M (     40583695 )  cycles total
................    41M (     40567002 )  cycles total
................    41M (     40582041 )  cycles total
................    41M (     40555946 )  cycles total
................    41M (     40563943 )  cycles total
................    41M (     40563547 )  cycles total
................    41M (     40579219 )  cycles total
................    41M (     40560135 )  cycles total
................    41M (     40560902 )  cycles total
................    41M (     40575462 )  cycles total
................    41M (     40577624 )  cycles total   
    """
    parse_cycles_prints(s)
