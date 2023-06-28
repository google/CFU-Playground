import os
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

utilization_reports_dir = "utilization/"

# design_to_utilization = {}

# for fname in os.listdir(utilization_reports_dir):
#     design_name = fname.replace(".txt", "")
#     report_path = utilization_reports_dir + fname
#     design_to_utilization[design_name] = {}

#     for line in open(report_path, "r"):
#         line = line.strip()

#         try:
#             value = float(line.split("|")[-2].strip())
#         except:
#             continue

#         if line.startswith("| Slice LUTs                 |"):
#             design_to_utilization[design_name]["LUT"] = value
#         if line.startswith("| LUT as Memory                              |"):
#             design_to_utilization[design_name]["LUT_RAM"] = value
#         if line.startswith("| Slice Registers            |"):
#             design_to_utilization[design_name]["FF"] = value
#         if line.startswith("| Block RAM Tile    |"):
#             design_to_utilization[design_name]["BRAM"] = value
#         if line.startswith("| DSPs           |"):
#             design_to_utilization[design_name]["DSP"] = value

# pprint(design_to_utilization)

design_to_utilization = {
    "NO_CFU": {"BRAM": 11.48, "DSP": 1.67, "FF": 2.89, "LUT": 7.15, "LUT_RAM": 0.77},
    "V4.0": {"BRAM": 11.48, "DSP": 9.58, "FF": 3.08, "LUT": 14.02, "LUT_RAM": 16.94},
    "V5.0": {"BRAM": 11.48, "DSP": 12.5, "FF": 3.24, "LUT": 15.24, "LUT_RAM": 16.94},
    "V5.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.42, "LUT": 15.31, "LUT_RAM": 16.94},
    "V6.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 16.49, "LUT": 58.92, "LUT_RAM": 0.77},
    "V7.0": {"BRAM": 11.48, "DSP": 16.67, "FF": 17.3, "LUT": 65.4, "LUT_RAM": 0.77},
    "V8.0\nx1": {"BRAM": 12.22, "DSP": 10.83, "FF": 3.41, "LUT": 8.9, "LUT_RAM": 0.77},
    "V8.0\nx2": {"BRAM": 12.22, "DSP": 11.67, "FF": 3.41, "LUT": 8.96, "LUT_RAM": 0.77},
    "V8.0\nx4": {"BRAM": 12.22, "DSP": 13.33, "FF": 3.41, "LUT": 9.11, "LUT_RAM": 0.77},
    "V8.0\nx16": {"BRAM": 11.48, "DSP": 23.33, "FF": 3.42, "LUT": 13.2, "LUT_RAM": 9.11},
    "V8.0\nx24": {"BRAM": 11.48, "DSP": 30.0, "FF": 3.42, "LUT": 15.39, "LUT_RAM": 13.27},
    "V8.0\nx32": {"BRAM": 11.48, "DSP": 36.67, "FF": 3.43, "LUT": 17.56, "LUT_RAM": 17.44},
    "V8.0\nx8": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.41, "LUT": 10.99, "LUT_RAM": 4.94},
}

generate_pgf = False

if generate_pgf:
    matplotlib.use("pgf")
    matplotlib.rcParams.update(
        {
            "pgf.texsystem": "pdflatex",
            "font.family": "serif",
            "font.size": 7,
            "text.usetex": True,
            "pgf.rcfonts": False,
        }
    )


def main():
    versions = ["cucumber", "tomato", "lettuce", "asparagus", "potato", "wheat", "barley"]
    resources = [
        "Farmer Joe",
        "Upland Bros.",
        "Smith Gardening",
        "Agrifun",
        "Organiculture",
        "BioGoods Ltd.",
        "Cornylee Corp.",
    ]

    utilization = np.array(
        [
            [0.8, 2.4, 2.5, 3.9, 0.0, 4.0, 0.0],
            [2.4, 0.0, 4.0, 1.0, 2.7, 0.0, 0.0],
            [1.1, 2.4, 0.8, 4.3, 1.9, 4.4, 0.0],
            [0.6, 0.0, 0.3, 0.0, 3.1, 0.0, 0.0],
            [0.7, 1.7, 0.6, 2.6, 2.2, 6.2, 0.0],
            [1.3, 1.2, 0.0, 0.0, 0.0, 3.2, 5.1],
            [0.1, 2.0, 0.0, 1.4, 0.0, 1.9, 6.3],
        ]
    )

    fig, ax = plt.subplots()
    im = ax.imshow(utilization)

    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(resources)), labels=resources)
    ax.set_yticks(np.arange(len(versions)), labels=versions)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(versions)):
        for j in range(len(resources)):
            text = ax.text(j, i, utilization[i, j], ha="center", va="center", color="w")

    # ax.set_title("Harvest of local farmers (in tons/year)")
    fig.tight_layout()

    if generate_pgf:
        plt.savefig("resources_utilization.pgf")
    else:
        plt.show()


if __name__ == "__main__":
    main()
