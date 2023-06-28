from typing import List
from dataset import SignalModulationDataset
from models.data_generation.matlab_v2 import load_data_simc_v2
from models.tools.utils import is_tuple, is_str
import numpy as np

__MODULATIONS = [
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
        frames_per_mod_per_snr = (self._frames_per_mod // len(self._snrs))
        snr_idx = (idx % self._frames_per_mod) // frames_per_mod_per_snr
        return self._snrs[snr_idx]
        
    def load(self, val, *args, **kwargs):
        if is_str(val):
            self._labels, self._data = load_data_simc_v2(
                self.get_modulations(), val, *args, **kwargs
            )
            return
        else:
            super().load(val, *args, **kwargs)
            
    def get_snrs(self, *args, **kwargs) -> np.ndarray:
        assert self._labels is not None, "Can't get snrs: labels are not loaded"
        return np.array([self.__snr_by_idx(idx) for idx in range(len(self._labels))])

    def get_modulations(self, *args, **kwargs) -> List:
        return __MODULATIONS
