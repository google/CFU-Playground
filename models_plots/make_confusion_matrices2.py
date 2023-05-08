import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib

matplotlib.use("pgf")
matplotlib.rcParams.update(
    {
        "pgf.texsystem": "pdflatex",
        "font.family": "serif",
        # 'font.size': 4,
        "text.usetex": True,
        "pgf.rcfonts": False,
    }
)


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

labels = [
    "CNN_1:radioML_2016.10a",
    "CNN_9:radioML_2016.10a",
    "ENC_3:radioML_2016.10a",
    "ENC_9:radioML_2016.10a",
]

labels_latex = [
    "CNN\\_1:radioML\\_2016.10a",
    "CNN\\_9:radioML\\_2016.10a",
    "ENC\\_3:radioML\\_2016.10a",
    "ENC\\_9:radioML\\_2016.10a",
]


for i, experiment in enumerate(experiments):
    result_filepath = os.path.join(experiment, "results.json")
    with open(result_filepath, "r") as result_filepath:
        results = json.load(result_filepath)

    confusion_matrix = np.array(results["cm_test"])

    # fig = plt.figure(figsize=(2.5, 2.5))
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(labels_latex[i])

    sns.heatmap(
        confusion_matrix,
        # annot=False,
        annot=True,
        cmap="Blues",
        xticklabels=modulations,
        yticklabels=modulations,
        fmt="g",
    )

    # Add labels to the x-axis and y-axis
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    plt.savefig(f"confusion_matrix_{labels[i]}.pgf")

    # plt.show()
