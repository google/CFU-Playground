import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class DataLabelsPair:
    data: np.ndarray
    labels: np.ndarray


@dataclass
class SplittedDataset:
    train: DataLabelsPair
    val: DataLabelsPair
    test: DataLabelsPair


def get_split_indecies(
    data: np.ndarray, labels: np.ndarray, train_perc: float, val_perc: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    assert train_perc + val_perc < 1.0
    assert len(data) == len(labels)

    ds_size = len(data)
    random_indecies = np.arange(ds_size)
    np.random.shuffle(random_indecies)

    train_indecies, validation_indecies, test_indecies, _ = np.split(
        random_indecies,
        [int(ds_size * train_perc), int(ds_size * (train_perc + val_perc)), ds_size],
    )
    return train_indecies, validation_indecies, test_indecies


def split_train_val_test(
    data: np.ndarray, labels: np.ndarray, train_perc: float, val_perc: float
) -> Tuple[SplittedDataset, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    train_indecies, validation_indecies, test_indecies = get_split_indecies(
        data, labels, train_perc, val_perc
    )

    train_data, train_labels = data[train_indecies], labels[train_indecies]
    validation_data, validation_labels = data[validation_indecies], labels[validation_indecies]
    test_data, test_labels = data[test_indecies], labels[test_indecies]

    return SplittedDataset(
        DataLabelsPair(train_data, train_labels),
        DataLabelsPair(validation_data, validation_labels),
        DataLabelsPair(test_data, test_labels),
    ), (train_indecies, validation_indecies, test_indecies)
