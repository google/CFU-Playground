import json
import matplotlib.pyplot as plt
import os
import matplotlib
import numpy as np
from argparse import ArgumentParser
from utils import save_plot
import sys
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

# TODO: ugly
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from evaluation.results_serialization import load_results

# Don't change, use --save_png
EXT = "pgf"


def main(save_path: str, save_png: bool):
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
            global EXT
            EXT = "png"
        os.makedirs(save_path, exist_ok=True)

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

    # fig = plt.figure(figsize=(20,20))
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    snr_to_accs = []
    for i, experiment in enumerate(experiments):
        results = load_results(experiment)
        snr_to_acc = results["snr_to_acc_test"]
        snr_to_accs.append(snr_to_acc)

        ax.plot(list(snr_to_acc.keys()), list(snr_to_acc.values()), label=labels_latex[i])

    plt.ylim([0, 1])
    ax.set_xlabel("SNR")
    ax.set_ylabel("Accuracy")
    ax.legend(loc="upper left")
    ax.grid()
    plt.setp(ax.get_xticklabels()[::2], visible=False)
    plt.yticks(np.arange(0, 1, 0.1).tolist())

    x1, x2 = 7, 13
    y1, y2 = 0.65, 0.95

    axins = zoomed_inset_axes(ax, 1.7, loc=4)  # zoom = 2
    for i, snr_to_acc in enumerate(snr_to_accs):
        # axins.plot(list(snr_to_acc.keys()), list(snr_to_acc.values()), label=labels_latex[i])
        axins.plot(list(snr_to_acc.keys()), list(snr_to_acc.values()), label=labels_latex[i])

    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    plt.xticks(visible=False)
    plt.yticks(visible=False)
    mark_inset(ax, axins, loc1=3, loc2=1, fc="0.9", ec="0.5")

    # ax.legend()
    plt.draw()

    # plt.show()
    save_filepath = os.path.join(save_path, f"snr_to_acc.{EXT}") if save_path is not None else None
    save_plot(save_filepath)


if __name__ == "__main__":
    parser = ArgumentParser("Make model plots")
    parser.add_argument("--save_path", "-s", required=False, default=None)
    parser.add_argument("--save_png", action="store_const", const=True, default=False)
    args = parser.parse_args()
    main(args.save_path, args.save_png)
