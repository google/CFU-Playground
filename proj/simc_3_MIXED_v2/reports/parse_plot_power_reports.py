import os
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

power_reports_dir = "power/"

# design_to_power = {}

# for fname in os.listdir(power_reports_dir):
#     report_path = power_reports_dir + fname

#     for line in open(report_path, 'r'):
#         line = line.strip()
#         if "Total On-Chip Power (W)" not in line:
#             continue

#         power = float(line.split("|")[2].strip())
#         design_name = fname.replace(".txt", "")
#         design_to_power[design_name] = power

# pprint(design_to_power)

design_to_power = {
    "No CFU": 0.428,
    "V4.0": 0.443,
    "V5.0": 0.461,
    "V5.1": 0.462,
    "V6.1": 0.571,
    "V7.0": 0.592,
    "V8.0\nx1": 0.429,
    "V8.0\nx2": 0.428,
    "V8.0\nx4": 0.431,
    "V8.0\nx8": 0.441,
    "V8.0\nx16": 0.444,
    "V8.0\nx24": 0.477,
    "V8.0\nx32": 0.478,
}


generate_pgf = True

if generate_pgf:
    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        'font.family': 'serif',
        'font.size': 7,
        'text.usetex': True,
        'pgf.rcfonts': False,
    })


def main():
    versions = list(design_to_power.keys())
    powers = list(design_to_power.values())

    fig, ax = plt.subplots()

    # creating the bar plot
    width = 0.8
    bars = plt.bar(
        versions, powers, color="#ebbd34", width=width, label="Hardware"
    )

    # ax.set_xticklabels(meaned_simulation_data.keys())

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#DDDDDD")

    ax.tick_params(bottom=False, left=False)

    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#DDDDDD")
    ax.xaxis.grid(False)

    ax.set_ylim(0.4, 0.6)

    plt.xlabel("CFU versions")
    # plt.xlabel("CFU versions (number after ''X'' - number of multiply-accumulate operations per cycle)")
    plt.ylabel("Power consumption (Watt)")
    # plt.title("CNN1:generated_0-30 inference acceleration (clock cycles)")
    # plt.title("CNN1:generated\\_0-30 inference acceleration (clock cycles)")
    # plt.legend()

    bar_color = bars[0].get_facecolor()
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1e6,
            "%.1fM" % (bar.get_height() / 1e6),
            horizontalalignment="center",
            color=bar_color,
            weight="bold",
        )

    if generate_pgf:
        # plt.savefig("cycle_bars_evolution.pgf")
        plt.savefig("power_consumption.pgf")
    else:
        plt.show()


if __name__ == "__main__":
    main()
