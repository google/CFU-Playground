import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib
import sys
from utils import get_modulations, save_plot
from argparse import ArgumentParser

# TODO: ugly
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from evaluation.results_serialization import load_results


# Don't change, use --save_png
EXT = "pgf"

experiments = [
    "examples/cnn_test_results/",
    "examples/cnn_test_results/",
    "examples/cnn_test_results/",
    "examples/cnn_test_results/",
    # "CNN_radio_ML/experiment_0/",
    # "CNN_radio_ML/experiment_8/",
    # "encoder_radio_ML/experiment_2/",
    # "encoder_radio_ML/experiment_8/",
]

labels = [
    "CNN\\_1:radioML\\_2016.10a",
    "CNN\\_9:radioML\\_2016.10a",
    "ENC\\_3:radioML\\_2016.10a",
    "ENC\\_9:radioML\\_2016.10a",
]


# fig = plt.figure()
# axes = fig.add_subplot(2, 2)
def confusion_matrices_1_plot(save_path: str):
    fig, axes = plt.subplots(2, 2)

    for i, experiment in enumerate(experiments):
        results = load_results(experiment)
        modulations = get_modulations(results)

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

        # Add labels to the x-axis and y-axis
        axes[i // 2, i % 2].set_xlabel("Predicted")
        axes[i // 2, i % 2].set_ylabel("True")

    save_filepath = (
        os.path.join(save_path, f"confusion_matrix_top_4.{EXT}") if save_path is not None else None
    )
    save_plot(save_filepath)


def confusion_matrices_n_plots(save_path: str):
    for i, experiment in enumerate(experiments):
        results = load_results(experiment)
        modulations = get_modulations(results)

        confusion_matrix = np.array(results["cm_test"])

        # fig = plt.figure(figsize=(5, 4))
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        # ax.set_title(labels_latex[i])

        sns.heatmap(
            confusion_matrix,
            # annot=False,
            annot=True,
            cmap="Blues",
            xticklabels=modulations,
            yticklabels=modulations,
            fmt="g",
        )

        plt.xticks(rotation=45)

        # Add labels to the x-axis and y-axis
        # ax.set_xlabel("Predicted")
        # ax.set_ylabel("True")
        save_filepath = (
            os.path.join(save_path, f"confusion_matrix_{labels[i]}.{EXT}")
            if save_path is not None
            else None
        )
        save_plot(save_filepath)


plt.show()
# plt.savefig()

if __name__ == "__main__":
    parser = ArgumentParser("Make model plots")
    parser.add_argument("--save_path", "-s", required=False, default=None)
    parser.add_argument("--save_png", action="store_const", const=True, default=False)
    parser.add_argument("--merge_plots", "-m", action="store_const", const=True, default=False)
    args = parser.parse_args()

    save_path, save_png, merge_plots = args.save_path, args.save_png, args.merge_plots

    if save_path is not None:
        if not save_png:
            matplotlib.use("pgf")
            matplotlib.rcParams.update(
                {
                    "pgf.texsystem": "pdflatex",
                    "font.family": "serif",
                    "text.usetex": True,
                    "pgf.rcfonts": False,
                }
            )
        else:
            EXT = "png"
        os.makedirs(save_path, exist_ok=True)

    if merge_plots:
        confusion_matrices_1_plot(save_path)
    else:
        confusion_matrices_n_plots(save_path)
