import numpy as np


def parse_cycles_prints(prints: str):
    lines = prints.split("\n")
    cycless = []
    for line in lines:
        if not line.startswith("..."):
            continue
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
................  5971M (   5971026057 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  5944M (   5944417118 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6133M (   6133404028 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  5833M (   5833330973 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6138M (   6138185898 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  5911M (   5911456163 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6137M (   6137149382 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6050M (   6049811882 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6133M (   6133211906 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  6022M (   6022189573 )  cycles total
Copied 8192 bytes at 0x4024d430
Running simc_3_MIXED_v2_no_quant model classification
................  5870M (   5870294503 )  cycles total   
    """
    parse_cycles_prints(s)
