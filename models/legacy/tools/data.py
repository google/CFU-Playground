from dataclasses import dataclass, field
import glob
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os
import pickle

import numpy as np
from scipy import io
from tqdm import tqdm
from .logger import logger
import time
from tools.matlab_helpers import get_engine
import matlab
from tqdm import trange


@dataclass
class DataSIM_v1_Config:
    frames_per_mod_type: int = 200

    SNR: float = 30.0
    # max_offset: float
    # fc: float
    fs: float = 200e3  # Sample rate
    sps: float = 8.0  # Samples per symbol
    spf: int = 1024  # Samples per frame

    # rcos_beta: float
    # rcos_span: int
    # rcos_sps: int
    trans_delay: int = 50

    rician_path_delays: List[float] = field(
        default_factory=lambda: [0.0 / 200e3, 1.8 / 200e3, 3.4 / 200e3]
    )
    rician_averate_path_gains: List[float] = field(default_factory=lambda: [0, -2, -10])
    rician_maximum_clockoffset: float = 5.0
    rician_k_factor: float = 4.0
    rician_maximum_doppler_shift: float = 4.0


# direct rewrite of 'Waveform Generation' code in simc 1 model
def generate_data_simc_v1(cnf: DataSIM_v1_Config, modulations: List[str], save_path: Path, eng=None):
    begin = time.time()
    if eng is None:
        eng = get_engine(Path(__file__).parent / "matlab" / "simc_1_functions")
    filename_root = "frame"

    data_files_exist = False
    if save_path.exists():
        n_files = os.listdir(save_path)
        if n_files == len(modulations) * cnf.frames_per_mod_type:
            data_files_exist = True

    if data_files_exist:
        return
    logger.info(f"Generating data and saving in data files...")
    if not save_path.exists():
        save_path.mkdir()

    n_data = 0
    for mod_type, mod in enumerate(modulations):
        before = time.time()
        print(f"Generating {mod} frames...", end="")

        eng.workspace["label"] = "mod"
        # print(f"helperModClassGetSource(\"{mod}\", {cnf.sps}, {2 * cnf.spf}, {cnf.fs})")
        eng.workspace["dataSrc"] = eng.eval(f"helperModClassGetSource(\"{mod}\", {cnf.sps}, {2 * cnf.spf}, {cnf.fs})")
        eng.workspace["modulator"] = eng.helperModClassGetModulator(mod, cnf.sps, cnf.fs)

        channel = eng.helperModClassTestChannel(
            "SampleRate",
            cnf.fs,
            "SNR",
            cnf.SNR,
            "PathDelays",
            matlab.double(cnf.rician_path_delays),
            "AveragePathGains",
            matlab.double(cnf.rician_averate_path_gains),
            "KFactor",
            cnf.rician_k_factor,
            "MaximumDopplerShift",
            cnf.rician_maximum_doppler_shift,
            "MaximumClockOffset",
            cnf.rician_maximum_clockoffset,
            # Analog modulation types use a center frequency of 100 MHz, Digital - 902 MHz
            "CenterFrequency",
            100e6 if mod in {"B-FM", "DSB-AM", "SSB-AM"} else 902e6,
        )
        eng.workspace["channel"] = channel

        for p in trange(cnf.frames_per_mod_type):
            n_data += 1
            # Generate random data
            eng.workspace["x"] = eng.eval("dataSrc()")

            # Modulte
            eng.workspace["y"] = eng.eval("modulator(x)")

            # Pass through independent channels
            eng.workspace["rx_samples"] = eng.eval("channel(y)")

            # Remove transients from the beginning, trim to size, and normalize
            eng.workspace["frame"] = eng.eval(
                f"helperModClassFrameGenerator(rx_samples, {cnf.spf}, {cnf.spf}, {cnf.trans_delay}, {cnf.sps})"
            )

            filename = (save_path / f"{filename_root}{mod}{p}").absolute()
            eng.save(str(filename), "frame", "label", nargout=0)
            # fileName = fullfile(dataDirectory,...
            # sprintf("%s%s%03d",fileNameRoot,modulationTypes(modType),p));
            # save(fileName,"frame","label")

        print(f"[debug] Done in {time.time() - before}s")
    print(f"[debug] Data generation with size {n_data} done in {time.time() - begin}s")

@dataclass
class DataSIM_v2_Config:
    frames_per_mod_type: int = 200

    SNR_RANGE: Tuple[float, float] = (0.0, 30.0)
    # max_offset: float
    # fc: float
    fs: float = 200e3  # Sample rate
    sps: float = 8.0  # Samples per symbol
    spf: int = 1024  # Samples per frame

    # rcos_beta: float
    # rcos_span: int
    # rcos_sps: int
    trans_delay: int = 50

    rician_path_delays: List[float] = field(
        default_factory=lambda: [0.0 / 200e3, 1.8 / 200e3, 3.4 / 200e3]
    )
    rician_averate_path_gains: List[float] = field(default_factory=lambda: [0, -2, -10])
    rician_maximum_clockoffset: float = 5.0
    rician_k_factor: float = 4.0
    rician_maximum_doppler_shift: float = 4.0

def generate_data_simc_v2(cnf: DataSIM_v2_Config, modulations: List[str], save_path: Path, eng=None):
    begin = time.time()
    if eng is None:
        eng = get_engine(Path(__file__).parent / "matlab" / "simc_1_functions")
    filename_root = "frame"

    data_files_exist = False
    if save_path.exists():
        n_files = os.listdir(save_path)
        if n_files == len(modulations) * cnf.frames_per_mod_type:
            data_files_exist = True

    if data_files_exist:
        return
    logger.info(f"Generating data and saving in data files...")
    if not save_path.exists():
        save_path.mkdir()

    n_snrs = len(range(int(cnf.SNR_RANGE[0]), int(cnf.SNR_RANGE[1])))
    n_data = 0
    for mod_type, mod in enumerate(modulations):
        cur_frame_mod_idx = 0
        for snr in trange(int(cnf.SNR_RANGE[0]), int(cnf.SNR_RANGE[1])):
            snr = float(snr)
            before = time.time()
            print(f"Generating {mod} frames...", end="")

            eng.workspace["label"] = "mod"
            # print(f"helperModClassGetSource(\"{mod}\", {cnf.sps}, {2 * cnf.spf}, {cnf.fs})")
            eng.workspace["dataSrc"] = eng.eval(f"helperModClassGetSource(\"{mod}\", {cnf.sps}, {2 * cnf.spf}, {cnf.fs})")
            eng.workspace["modulator"] = eng.helperModClassGetModulator(mod, cnf.sps, cnf.fs)

            channel = eng.helperModClassTestChannel(
                "SampleRate",
                cnf.fs,
                "SNR",
                snr,
                "PathDelays",
                matlab.double(cnf.rician_path_delays),
                "AveragePathGains",
                matlab.double(cnf.rician_averate_path_gains),
                "KFactor",
                cnf.rician_k_factor,
                "MaximumDopplerShift",
                cnf.rician_maximum_doppler_shift,
                "MaximumClockOffset",
                cnf.rician_maximum_clockoffset,
                # Analog modulation types use a center frequency of 100 MHz, Digital - 902 MHz
                "CenterFrequency",
                100e6 if mod in {"B-FM", "DSB-AM", "SSB-AM"} else 902e6,
            )
            eng.workspace["channel"] = channel

            for p in range(cnf.frames_per_mod_type // n_snrs):
                n_data += 1
                # Generate random data
                eng.workspace["x"] = eng.eval("dataSrc()")

                # Modulte
                eng.workspace["y"] = eng.eval("modulator(x)")

                # Pass through independent channels
                eng.workspace["rx_samples"] = eng.eval("channel(y)")

                # Remove transients from the beginning, trim to size, and normalize
                eng.workspace["frame"] = eng.eval(
                    f"helperModClassFrameGenerator(rx_samples, {cnf.spf}, {cnf.spf}, {cnf.trans_delay}, {cnf.sps})"
                )

                filename = (save_path / f"{filename_root}{mod}{cur_frame_mod_idx}").absolute()
                eng.save(str(filename), "frame", "label", nargout=0)
                # fileName = fullfile(dataDirectory,...
                # sprintf("%s%s%03d",fileNameRoot,modulationTypes(modType),p));
                # save(fileName,"frame","label")
                cur_frame_mod_idx+=1

            print(f"[debug] Done in {time.time() - before}s")
    print(f"[debug] Data generation with size {n_data} done in {time.time() - begin}s")


def preprocess_raw_data(samples: np.ndarray, model_dtype=np.float32) -> np.ndarray:
    I = np.real(samples)
    Q = np.imag(samples)
    return np.hstack([I, Q]).astype(model_dtype)


def load_data_simc_v1(classes, path=Path("train_data"), model_dtype=np.float32, max_frames_per_mod=-1) -> Tuple[np.ndarray, np.ndarray]:
    before = time.time()
    # train_data = {}
    labels = []
    data = []

    n_data = 0
    for cl_idx, cl in enumerate(tqdm(classes)):
        mat_files = glob.glob(f"{path}/*{cl}*.mat")
        for mat_idx, mat_file in enumerate(mat_files):
            np_data = io.loadmat(mat_file)["frame"]
            np_data = preprocess_raw_data(np_data, model_dtype)
            n_data += len(np_data)

            labels.append(cl_idx)
            data.append(np_data)
            if max_frames_per_mod == mat_idx:
                break
    after = time.time()
    print(f"[debug] Loaded train data with size {n_data} in {after - before}s")
    return np.array(labels), np.expand_dims(np.array(data), axis=1)

def load_data_simc_v2(classes, path=Path("train_data"), model_dtype=np.float32, frames_per_mod=-1) -> Tuple[np.ndarray, np.ndarray]:
    before = time.time()
    # train_data = {}
    labels = []
    data = []

    n_data = 0
    for cl_idx, cl in enumerate(tqdm(classes)):
        # mat_files = glob.glob(f"{path}/*{cl}*.mat")
        for idx in range(frames_per_mod):
            mat_file = path / f"frame{cl}{idx}.mat"
        # for mat_idx, mat_file in enumerate(mat_files):
            np_data = io.loadmat(str(mat_file))["frame"]
            np_data = preprocess_raw_data(np_data, model_dtype)
            n_data += len(np_data)

            labels.append(cl_idx)
            data.append(np_data)
    after = time.time()
    print(f"[debug] Loaded train data with size {n_data} in {after - before}s")
    return np.array(labels), np.expand_dims(np.array(data), axis=1)


def _postprocess_radioml_v1(raw_ds: Dict, to_1024: bool, transpose: bool, minimum_snr: int):
    ds_keys = [k for k in raw_ds.keys() if k[1] >= minimum_snr]
    classes = list(set(map(lambda v: v[0], ds_keys)))
    class_name_to_class_idx = {name: idx for idx, name in enumerate(classes)}

    frames_per_modulation = raw_ds[ds_keys[0]].shape[0]     # 100

    # 220 * 1000 // 8
    ds_size = len(ds_keys) * frames_per_modulation
    if to_1024: ds_size //= 8

    if transpose:
        data = np.empty((ds_size, 1, 1024, 2)) if to_1024 else np.empty((ds_size, 1, 128, 2))
    else:
        data = np.empty((ds_size, 1, 2, 1024)) if to_1024 else np.empty((ds_size, 1, 2, 128))

    labels = np.empty((ds_size,), dtype=np.uint8)


    cur_idx = 0
    for (class_name, snr), raw_data in raw_ds.items():
        if snr < minimum_snr:
            continue
        if to_1024:
            for frame_idx in range(0, len(raw_data), 8):
                frame_1024 = np.hstack([raw_data[idx] for idx in range(frame_idx, frame_idx+8)])
                # print(frame_1024.shape)
                data[cur_idx] = np.transpose(frame_1024).reshape((1, 1024, 2)) if transpose else frame_1024.reshape(1, 2, 1024)
                # data[cur_idx] = frame_1024.reshape((1, 1024, 2))
                labels[cur_idx] = class_name_to_class_idx[class_name]
                cur_idx += 1
                # break
        else:
            for frame_idx in range(0, len(raw_data)):
                frame = raw_data[frame_idx]
                data[cur_idx] = np.transpose(frame).reshape((1, 128, 2)) if transpose else frame.reshape(1, 2, 128)
                labels[cur_idx] = class_name_to_class_idx[class_name]
                cur_idx += 1
    return labels, data, classes



# Returns {(modulation, snr): frames}               if not postprocess
#         (labels, frames, classes)                 if postprocess
def load_data_radioml_v1(ds_path: str, postprocess=True, to_1024=True, transpose=True, minimum_snr: Optional[int]=None):
    with open(ds_path, 'rb') as crmrn_file:
        raw_ds = pickle.load(crmrn_file, encoding="bytes")
    decoded_raw_ds = {}
    for (class_name_bytes, snr), raw_data in raw_ds.items():
        decoded_raw_ds[(class_name_bytes.decode("utf-8"), snr)] = raw_data
    raw_ds = decoded_raw_ds

    if not postprocess:
        return raw_ds
    if minimum_snr is None:
        minimum_snr = -100
    return _postprocess_radioml_v1(raw_ds, to_1024, transpose, minimum_snr)
