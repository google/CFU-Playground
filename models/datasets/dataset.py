import numpy as np
from abc import abstractmethod, ABC, abstractstaticmethod, abstractclassmethod
from typing import List, Optional, Tuple
from .utils import SplittedDataset, split_train_val_test


class Dataset(ABC):
    _splitted_ds: Optional[SplittedDataset] = None
    _splitted_indecies: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
    _data: Optional[np.ndarray] = None
    _labels: Optional[np.ndarray] = None

    @abstractclassmethod
    def load(cls, path: str):
        raise NotImplementedError

    @abstractclassmethod
    def unload(cls, path: str):
        raise NotImplementedError

    def get_labels(self):
        if self._labels is None:
            raise RuntimeError("Can't get labels: labels were not loaded")
        return self._labels

    def get_data(self):
        if self._data is None:
            raise RuntimeError("Can't get data: data was not loaded")
        return self._data

    def split_train_val_test(self, train_perc: float, val_perc: float, force_resplit=False):
        if self._data is None or self._labels is None:
            raise RuntimeError("Can't splt: data or labels were not loaded")
        if self._splitted_ds is None or force_resplit:
            self._splitted_ds, self._splitted_indecies = split_train_val_test(
                self._data, self._labels, train_perc, val_perc
            )
        return self._splitted_ds

    def get_split_indecies(self):
        if self._splitted_indecies is None:
            raise RuntimeError("dataset is not splitted")
        return self._splitted_indecies


class SignalModulationDataset(Dataset):
    @abstractmethod
    def get_modulations(self) -> List:
        """
        List of modulations. List index == label
        """
        raise NotImplementedError

    @abstractclassmethod
    def get_snrs(self) -> np.ndarray:
        """
        List of snrs for each sample
        """
        raise NotImplementedError
