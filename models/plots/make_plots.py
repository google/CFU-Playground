import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf

tf.get_logger().setLevel("ERROR")

from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
import json
from argparse import ArgumentParser
from pprint import pprint
import pandas as pd
import seaborn as sn
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


from evaluation.results_serialization import load_results
from datasets.fabric import make_sigmod_ds, DatasetName

import matplotlib

# Don't change, use --save_png
FIG_EXTENSION = "pgf"


def save_plot(save_path: str):
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path)


class __DatasetCache:
    dataset = None
    dataset_name = None
    dataset_path = None


ds_cache = __DatasetCache()


def get_modulations(results: Dict):
    dataset_name = results["dataset_name"]
    dataset_path = results["dataset_path"]
    print(f"Dataset: name: {dataset_name}, path: {dataset_path}")

    if ds_cache.dataset is not None and (
        ds_cache.dataset_name == dataset_name and ds_cache.dataset_path == dataset_path
    ):
        return ds_cache.dataset.get_modulations()

    dataset = make_sigmod_ds(DatasetName[dataset_name])
    dataset_params = {} if "dataset_params" not in results else results["dataset_params"]
    dataset.load(dataset_path, **dataset_params)

    ds_cache.dataset = dataset
    ds_cache.dataset_name = dataset_name
    ds_cache.dataset_path = dataset_path

    return dataset.get_modulations()


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
    save_plot(f"{save_path}/history.{FIG_EXTENSION}")


def make_confusion_matrix(results: Dict, save_path=None):
    cm_val = results["cm_val"]
    cm_test = results["cm_test"]

    modulations = get_modulations(results)
    print("Modulations:")
    pprint(modulations)

    df_cm_val = pd.DataFrame(cm_val, index=modulations, columns=modulations)
    plt.figure(figsize=(10, 7))
    sn.heatmap(df_cm_val, annot=True)
    plt.title("Confusion matrix - validation data")
    save_plot(f"{save_path}/confusion_matrix_validation.{FIG_EXTENSION}")

    df_cm_test = pd.DataFrame(cm_test, index=modulations, columns=modulations)
    plt.figure(figsize=(10, 7))
    sn.heatmap(df_cm_test, annot=True)
    plt.title("Confusion matrix - test data")
    save_plot(f"{save_path}/confusion_matrix_test.{FIG_EXTENSION}")


def make_snr_to_acc(results: Dict, save_path=None):
    plt.clf()
    snr_to_acc_val = results["snr_to_acc_val"]
    plt.plot(list(snr_to_acc_val.keys()), list(snr_to_acc_val.values()))
    plt.ylim([0, 1])
    plt.title("SNR to accuracy - validation data")
    plt.ylabel("Accuracy")
    plt.xlabel("Signal-to-Noise")
    save_plot(f"{save_path}/snr_to_acc_validation.{FIG_EXTENSION}")

    plt.clf()
    snr_to_acc_test = results["snr_to_acc_test"]
    plt.plot(list(snr_to_acc_test.keys()), list(snr_to_acc_test.values()))
    plt.ylim([0, 1])
    plt.title("SNR to accuracy - test data")
    plt.ylabel("Accuracy")
    plt.xlabel("Signal-to-Noise")
    save_plot(f"{save_path}/snr_to_acc_test.{FIG_EXTENSION}")


def update_results(results: Dict, save_path=None):
    snr_to_acc_test = results["snr_to_acc_test"]
    results["Accuracy Average"] = results["cls_to_acc_test"]["Overall"]
    results["Accuracy snr 0"] = snr_to_acc_test["0.0"]
    results["Accuracy snr 18"] = snr_to_acc_test["18.0"]
    results["Accuracy Maximum"] = max(list(snr_to_acc_test.values()))
    results["Accuracy snr 0+ Average"] = np.mean(
        [snr_to_acc_test[v] for v in snr_to_acc_test if float(v) > 0]
    )

    # if save_path is not None:
    #     with open(f"{save_path}/results.json", 'w') as res_file:
    #         json.dump(results, res_file, indent=4)


def make_plots(result_dir: str, save_path: str, save_png: bool):
    results = load_results(result_dir, load_model=True)

    print(f"Model configuration:")
    pprint(results["model_configuration"].to_dict())

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
            global FIG_EXTENSION
            FIG_EXTENSION = "png"
        os.makedirs(save_path, exist_ok=True)

    make_history(results, save_path=save_path)
    make_confusion_matrix(results, save_path=save_path)
    make_snr_to_acc(results, save_path=save_path)
    update_results(results, save_path=save_path)


if __name__ == "__main__":
    parser = ArgumentParser("Make model plots")
    parser.add_argument("--result_dir", "-r", required=True, type=str)
    parser.add_argument("--save_path", "-s", required=False, default=None)
    parser.add_argument("--save_png", action="store_const", const=True, default=False)
    args = parser.parse_args()
    make_plots(args.result_dir, args.save_path, args.save_png)
