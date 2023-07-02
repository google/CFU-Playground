import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})


dataset = "radioML"
# dataset = "mixed_v2"

if dataset == "radioML":
    modulations = [
        "WBFM",
        "QAM64",
        "QAM16",
        "CPFSK",
        "QPSK",
        "BPSK",
        "AM-DSB",
        "8PSK",
        "AM-SSB",
        "PAM4",
        "GFSK",
    ]
elif dataset == "mixed_v2":
    modulations = [
        "16QAM",
        "64QAM",
        "8PSK",
        "B-FM",
        "BPSK",
        "CPFSK",
        "DSB-AM",
        "GFSK",
        "PAM4",
        "QPSK",
        "SSB-AM",
    ]
else:
    raise ValueError("Unknown dataset")

experiments = [
    "CNN_radio_ML/experiment_0/",
    "CNN_radio_ML/experiment_8/",
    "encoder_radio_ML/experiment_2/",
    "encoder_radio_ML/experiment_8/",
]

# labels = [
#     "CNN_1:radioML_2016.10a",
#     "CNN_9:radioML_2016.10a",
#     "ENC_3:radioML_2016.10a",
#     "ENC_9:radioML_2016.10a",
# ]

labels = [
    "CNN\\_1:radioML\\_2016.10a",
    "CNN\\_9:radioML\\_2016.10a",
    "ENC\\_3:radioML\\_2016.10a",
    "ENC\\_9:radioML\\_2016.10a",
]


# fig = plt.figure()
# axes = fig.add_subplot(2, 2)
fig, axes = plt.subplots(2, 2)

for i, experiment in enumerate(experiments):
    result_filepath = os.path.join(experiment, "results.json")
    with open(result_filepath, "r") as result_filepath:
        results = json.load(result_filepath)

    confusion_matrix = np.array(results["cm_test"])

    # Create a heatmap using seaborn
    axes[i // 2, i % 2].set_title(labels[i])

    ConfusionMatrixDisplay(confusion_matrix=confusion_matrix, display_labels=modulations).plot(
        include_values=False,
        cmap="Blues",
        ax=axes[i // 2, i % 2],
        colorbar=True,
        values_format="0.0f",
        xticks_rotation="vertical",
    )

    # axes[i // 2, i % 2].heatmap(
    #     confusion_matrix, annot=True, cmap="Blues", xticklabels=labels, yticklabels=labels, fmt="g"
    # )

    # Add labels to the x-axis and y-axis
    axes[i // 2, i % 2].set_xlabel("Predicted")
    axes[i // 2, i % 2].set_ylabel("True")

# plt.show()
plt.savefig("confusion_matrix_top_4.pgf")
