import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

import tensorflow as tf
from datasets.fabric import make_sigmod_ds, DatasetName
from models.fabric import make_sigmod_model, Convolution01xConfiguration, ModelName
from tools.utils import set_seed
from evaluation.metric_evaluation import metric_evaluation, snr_to_metric_evaluation
from evaluation.vizualization import plot_train, plot_snr_to_acc


from dataclasses import dataclass, field
from typing import Any, Dict, Union, Tuple

import numpy as np


@dataclass
class TrainConfiguration:
    dataset: DatasetName
    dataset_path: Union[str, Tuple[str, str]]

    model: ModelName
    model_config: Any

    n_epochs: int
    batch_size: int

    dataset_params: Dict = field(default_factory=lambda: dict())
    seed: int = 1234


def train_model(config: TrainConfiguration):
    set_seed(config.seed)
    
    dataset = make_sigmod_ds(config.dataset, **config.dataset_params)
    dataset.load(config.dataset_path)
    splitted_ds = dataset.split_train_val_test(0.8, 0.1)

    config.model_config.n_classes = len(dataset.get_modulations())
    model = make_sigmod_model(config.model, config.model_config)

    # TODO: remove this inconsistency
    splitted_ds.train.data = np.squeeze(splitted_ds.train.data)
    splitted_ds.val.data = np.squeeze(splitted_ds.val.data)
    splitted_ds.test.data = np.squeeze(splitted_ds.test.data)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    
    h = model.fit(
        splitted_ds.train.data,
        splitted_ds.train.labels,
        epochs=config.n_epochs,
        batch_size=config.batch_size,
        validation_data=(splitted_ds.val.data, splitted_ds.val.labels),
    )
    
    plot_train(h.history)

    metric_evaluation(
        model,
        splitted_ds.test.data,
        splitted_ds.test.labels,
        dataset.get_modulations(),
    )

    snr_to_acc = snr_to_metric_evaluation(
        model,
        splitted_ds.test.data,
        splitted_ds.test.labels,
        dataset.get_snrs()[dataset.get_split_indecies().test],
    )
    plot_snr_to_acc(snr_to_acc)


def string_to_ds(s: str) -> DatasetName:
    if s == "radioml_2016":
        return DatasetName.RADIOML_2016
    if s == "matlab_v2":
        return DatasetName.MATLAB_V2
    else:
        raise ValueError(f"Unknown dataset: {s}")