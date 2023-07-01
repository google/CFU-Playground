from typing import Dict, List, Optional

from datasets.dataset import SignalModulationDataset
from tools.utils import is_str, some_are_nones
import numpy as np
import pickle


class RadioML2016(SignalModulationDataset):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._modulations = None
        self._snrs = None

    def load(self, val, *args, force=False, **kwargs):
        """
        Additional parameters:
            to_1024 = False      - merge 8 consecutive frames into 1, legacy, works badly
            transpose = True     - swap last 2 dimensions
            minimum_snr = -10000 - filter result by minimum snr
        """
        if not force and not some_are_nones(
            self._labels, self._data, self._modulations, self._snrs
        ):
            return

        if is_str(val):
            (
                self._labels,
                self._data,
                self._modulations,
                self._snrs,
            ) = self.Detail.load_data_radioml_v1(val, *args, postprocess=True, **kwargs)
            return

        raise TypeError(f"load argument has bad type: {type(val)}")

    def get_snrs(self, *args, **kwargs) -> np.ndarray:
        assert self._snrs is not None, "Can't get snrs: dataset is not loaded"
        return self._snrs

    def get_modulations(self, *args, **kwargs) -> List:
        assert self._modulations is not None, "Can't get modulations: dataset is not loaded"
        return self._modulations

    class Detail:
        @staticmethod
        def _postprocess_radioml_v1(raw_ds: Dict, to_1024: bool, transpose: bool, minimum_snr: int):
            ds_keys = [k for k in raw_ds.keys() if k[1] >= minimum_snr]
            classes = list(set(map(lambda v: v[0], ds_keys)))
            classes.sort()  # make sure order is always the same
            class_name_to_class_idx = {name: idx for idx, name in enumerate(classes)}

            frames_per_modulation = raw_ds[ds_keys[0]].shape[0]  # 1000

            # 220 * 1000 // 8
            ds_size = len(ds_keys) * frames_per_modulation
            if to_1024:
                ds_size //= 8

            if transpose:
                data = (
                    np.empty((ds_size, 1024, 2)) if to_1024 else np.empty((ds_size, 128, 2))
                )
            else:
                data = (
                    np.empty((ds_size, 2, 1024)) if to_1024 else np.empty((ds_size, 2, 128))
                )

            labels = np.empty((ds_size,), dtype=np.uint8)
            snrs = np.empty_like(labels, dtype=np.int8)

            cur_idx = 0
            for (class_name, snr), raw_data in raw_ds.items():
                if snr < minimum_snr:
                    continue
                if to_1024:
                    for frame_idx in range(0, len(raw_data), 8):
                        frame_1024 = np.hstack(
                            [raw_data[idx] for idx in range(frame_idx, frame_idx + 8)]
                        )
                        # print(frame_1024.shape)
                        data[cur_idx] = (
                            np.transpose(frame_1024).reshape((1024, 2))
                            if transpose
                            else frame_1024.reshape(2, 1024)
                        )
                        # data[cur_idx] = frame_1024.reshape((1, 1024, 2))
                        labels[cur_idx] = class_name_to_class_idx[class_name]
                        snrs[cur_idx] = snr
                        cur_idx += 1
                        # break
                else:
                    for frame_idx in range(0, len(raw_data)):
                        frame = raw_data[frame_idx]
                        data[cur_idx] = (
                            np.transpose(frame).reshape((128, 2))
                            if transpose
                            else frame.reshape(2, 128)
                        )
                        labels[cur_idx] = class_name_to_class_idx[class_name]
                        snrs[cur_idx] = snr
                        cur_idx += 1
            return labels, data, classes, snrs

        # Returns {(modulation, snr): frames}               if not postprocess
        #         (labels, frames, classes)                 if postprocess
        @staticmethod
        def load_data_radioml_v1(
            ds_path: str,
            postprocess=True,
            to_1024=False,
            transpose=True,
            minimum_snr: Optional[int] = None,
        ):
            with open(ds_path, "rb") as crmrn_file:
                raw_ds = pickle.load(crmrn_file, encoding="bytes")
            decoded_raw_ds = {}
            for (class_name_bytes, snr), raw_data in raw_ds.items():
                decoded_raw_ds[(class_name_bytes.decode("utf-8"), snr)] = raw_data
            raw_ds = decoded_raw_ds

            if not postprocess:
                return raw_ds
            if minimum_snr is None:
                minimum_snr = -10000

            return RadioML2016.Detail._postprocess_radioml_v1(
                raw_ds, to_1024, transpose, minimum_snr
            )
