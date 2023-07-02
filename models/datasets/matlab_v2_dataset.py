from typing import List, Tuple
import time
from datasets.dataset import SignalModulationDataset
from tools.utils import is_str, some_are_nones
import numpy as np
from tqdm import tqdm
from scipy import io
import os


_MODULATIONS = [
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


class MatlabV2(SignalModulationDataset):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        assert "frames_per_modulation" in kwargs, "MatlabV2 requires 'frames_per_modulation'"
        assert "snrs" in kwargs, "MatlabV2 requires 'snrs'"

        self._frames_per_mod = kwargs["frames_per_modulation"]
        self._snrs = kwargs["snrs"]

    def __snr_by_idx(self, idx):
        frames_per_mod_per_snr = self._frames_per_mod // len(self._snrs)
        snr_idx = (idx % self._frames_per_mod) // frames_per_mod_per_snr
        return self._snrs[snr_idx]

    def load(self, val, *args, force=None, **kwargs):
        """
        Additional parameters:
            model_dtype: data type
        """
        if not force and not some_are_nones(self._labels, self._data):
            return
        if is_str(val):
            self._labels, self._data = self.Details.load_data_simc_v2(
                self.get_modulations(), val, *args, frames_per_mod=self._frames_per_mod, **kwargs
            )
            return
        else:
            super().load(val, *args, **kwargs)

    def get_snrs(self, *args, **kwargs) -> np.ndarray:
        assert self._labels is not None, "Can't get snrs: dataset is not loaded"
        return np.array([self.__snr_by_idx(idx) for idx in range(len(self._labels))])

    def get_modulations(self, *args, **kwargs) -> List:
        return _MODULATIONS

    class Details:
        @staticmethod
        def _preprocess_raw_data(samples: np.ndarray, model_dtype=np.float32) -> np.ndarray:
            I = np.real(samples)
            Q = np.imag(samples)
            return np.hstack([I, Q]).astype(model_dtype)

        @staticmethod
        def load_data_simc_v2(
            classes,
            path="train_data",
            model_dtype=np.float32,
            frames_per_mod=-1,
            *args,
            **kwargs,
        ) -> Tuple[np.ndarray, np.ndarray]:
            before = time.time()
            # train_data = {}
            labels = []
            data = []

            n_data = 0
            for cl_idx, cl in enumerate(tqdm(classes)):
                # mat_files = glob.glob(f"{path}/*{cl}*.mat")
                for idx in range(frames_per_mod):
                    mat_file = os.path.join(path, f"frame{cl}{idx}.mat")
                    # for mat_idx, mat_file in enumerate(mat_files):
                    np_data = io.loadmat(str(mat_file))["frame"]
                    np_data = MatlabV2.Details._preprocess_raw_data(np_data, model_dtype)
                    n_data += len(np_data)

                    labels.append(cl_idx)
                    data.append(np_data)
            after = time.time()
            print(f"[debug] Loaded train data with size {n_data} in {after - before}s")
            return np.array(labels), np.squeeze(np.array(data))
