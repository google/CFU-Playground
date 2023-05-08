import os
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
import json
from argparse import ArgumentParser
from pprint import pprint
import pandas as pd
import seaborn as sn

import matplotlib

FIG_EXTENSION="pgf"


def make_history(results: Dict, save_path=None):
    history = results["train_history"]
    acc = history["accuracy"]
    val_acc = history["val_accuracy"]
    loss = history["loss"]
    val_loss = history["val_loss"]

    epochs_range = range(len(acc))
    plt.figure(figsize=(8, 8))
    plt.subplot(2, 1, 1)
    plt.plot(epochs_range, acc, label="Training Accuracy")
    plt.plot(epochs_range, val_acc, label="Validation Accuracy")
    plt.legend(loc="lower right")
    plt.title("Training and Validation Accuracy")
    plt.subplot(2, 1, 2)

    plt.plot(epochs_range, loss, label="Training Loss")
    plt.plot(epochs_range, val_loss, label="Validation Loss")
    plt.legend(loc="upper right")
    plt.title("Training and Validation Loss")
    if save_path is None:
        plt.show()
    else:
        plt.savefig(f'{save_path}/history.{FIG_EXTENSION}')


def make_confusion_matrix(results: Dict, save_path=None):
    cm_val = results["cm_val"]
    cm_test = results["cm_test"]

    if results["dataset"] == "radioML":
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
    elif results["dataset"] == "mixed_v2":
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
        raise ValueError(f"Unknown dataset: {results['dataset']}")

    df_cm_val = pd.DataFrame(cm_val, index=modulations, columns=modulations)
    plt.figure(figsize=(10, 7))
    sn.heatmap(df_cm_val, annot=True)
    if save_path is None:
        plt.show()
    else:
        plt.savefig(f'{save_path}/confusion_matrix_validation.{FIG_EXTENSION}')

    df_cm_test = pd.DataFrame(cm_test, index=modulations, columns=modulations)
    plt.figure(figsize=(10, 7))
    sn.heatmap(df_cm_test, annot=True)
    if save_path is None:
        plt.show()
    else:
        plt.savefig(f'{save_path}/confusion_matrix_test.{FIG_EXTENSION}')


def make_snr_to_acc(results: Dict, save_path=None):
    snr_to_acc_val = results["snr_to_acc_val"]
    plt.plot(list(snr_to_acc_val.keys()), list(snr_to_acc_val.values()))
    plt.ylim([0, 1])
    if save_path is None:
        plt.show()
    else:
        plt.savefig(f'{save_path}/snr_to_acc_validation.{FIG_EXTENSION}')

    snr_to_acc_test = results["snr_to_acc_test"]
    plt.plot(list(snr_to_acc_test.keys()), list(snr_to_acc_test.values()))
    plt.ylim([0, 1])
    if save_path is None:
        plt.show()
    else:
        plt.savefig(f'{save_path}/snr_to_acc_test.{FIG_EXTENSION}')


def update_results(results: Dict, save_path=None):
    snr_to_acc_test = results["snr_to_acc_test"]
    results["Accuracy Average"] = results["cls_to_acc_test"]["Overall"]
    results["Accuracy snr 0"] = snr_to_acc_test["0"]
    results["Accuracy snr 18"] = snr_to_acc_test["18"]
    results["Accuracy Maximum"] = max(list(snr_to_acc_test.values()))
    results["Accuracy snr 0+ Average"] = np.mean([snr_to_acc_test[v] for v in snr_to_acc_test if int(v) > 0])
    
    if save_path is not None:
        with open(f"{save_path}/results.json", 'w') as res_file:
            json.dump(results, res_file, indent=4)
    


def make_plots(result_dir: str, dataset: str, save_path: str):
    with open(result_dir) as res_file:
        results = json.load(res_file)

    results["dataset"] = dataset
    print(f"Model configuration:")
    pprint(results["model_configuration"])

    if save_path is not None:
        matplotlib.use("pgf")
        matplotlib.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })
        os.makedirs(save_path, exist_ok=True)

    make_history(results, save_path=save_path)
    make_confusion_matrix(results, save_path=save_path)
    make_snr_to_acc(results, save_path=save_path)
    update_results(results, save_path=save_path)


if __name__ == "__main__":
    parser = ArgumentParser("Make model plots")
    parser.add_argument("--result_dir", "-r", required=True, type=str)
    parser.add_argument("--dataset", "-d", default="radioML")
    parser.add_argument("--save_path", "-s")
    args = parser.parse_args()
    make_plots(args.result_dir, args.dataset, args.save_path)
