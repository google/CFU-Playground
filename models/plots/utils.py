import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import tensorflow as tf

tf.get_logger().setLevel("ERROR")

from typing import Dict
import matplotlib.pyplot as plt
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")


from datasets.fabric import make_sigmod_ds, DatasetName

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