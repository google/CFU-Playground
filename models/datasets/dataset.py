import numpy as np
from abc import abstractmethod, ABC
from tools.utils import is_tuple
from typing import List, Optional, Tuple
from .utils import SplittedDataset, SplittedIndecies, split_train_val_test


class Dataset(ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self._splitted_ds: Optional[SplittedDataset] = None
        self._splitted_indecies: Optional[SplittedIndecies] = None
        self._data: Optional[np.ndarray] = None
        self._labels: Optional[np.ndarray] = None

    def load(self, how_or_where, *args, force=False, **kwargs):
        if not force and self._labels is not None and self._data is not None:
            return
        if is_tuple(how_or_where, 2, str):
            self._labels, self._data = np.load(how_or_where[0]), np.load(how_or_where[1])
            return
        raise TypeError(f"load argument has bad type: {type(how_or_where)}")

    def dump(self, how_or_where, *args, **kwargs):
        if is_tuple(how_or_where, 2, str):
            np.save(how_or_where[0], self._labels)
            np.save(how_or_where[1], self._data)
            return
        raise TypeError(f"dump argument has bad type: {type(how_or_where)}")

    def unload(self, *args, **kwargs):
        del self._data
        del self._labels

    def get_labels(self, *args, **kwargs) -> np.ndarray:
        if self._labels is None:
            raise RuntimeError("Can't get labels: labels were not loaded")
        return self._labels

    def get_data(self, *args, **kwargs) -> np.ndarray:
        if self._data is None:
            raise RuntimeError("Can't get data: data was not loaded")
        return self._data

    def split_train_val_test(
        self, train_perc: float, val_perc: float, force_resplit=False, *args, **kwargs
    ) -> SplittedDataset:
        if self._data is None or self._labels is None:
            raise RuntimeError("Can't splt: data or labels were not loaded")
        if self._splitted_ds is None or force_resplit:
            self._splitted_ds, self._splitted_indecies = split_train_val_test(
                self._data, self._labels, train_perc, val_perc
            )
        return self._splitted_ds

    def get_split_indecies(self, *args, **kwargs) -> SplittedIndecies:
        if self._splitted_indecies is None:
            raise RuntimeError("dataset is not splitted")
        return self._splitted_indecies


class SignalModulationDataset(Dataset, ABC):
    @abstractmethod
    def get_modulations(self, *args, **kwargs) -> List:
        """
        List of modulations. List index == label
        """
        raise NotImplementedError

    @abstractmethod
    def get_snrs(self, *args, **kwargs) -> np.ndarray:
        """
        List of snrs for each sample
        """
        raise NotImplementedError
