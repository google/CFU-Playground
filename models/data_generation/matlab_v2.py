""" 
    Differs from v1 by generating data with different snrs, not fixed
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from pathlib import Path
import os

import numpy as np
from scipy import io
from tqdm import tqdm
from models.tools.logger import logger

import time
from tools.matlab_helpers import get_engine
import matlab
from tqdm import trange


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


def generate_data_simc_v2(
    cnf: DataSIM_v2_Config, modulations: List[str], save_path: Path, eng=None
):
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
            eng.workspace["dataSrc"] = eng.eval(
                f'helperModClassGetSource("{mod}", {cnf.sps}, {2 * cnf.spf}, {cnf.fs})'
            )
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
                cur_frame_mod_idx += 1

            print(f"[debug] Done in {time.time() - before}s")
    print(f"[debug] Data generation with size {n_data} done in {time.time() - begin}s")


def preprocess_raw_data(samples: np.ndarray, model_dtype=np.float32) -> np.ndarray:
    I = np.real(samples)
    Q = np.imag(samples)
    return np.hstack([I, Q]).astype(model_dtype)


def load_data_simc_v2(
    classes, path=Path("train_data"), model_dtype=np.float32, frames_per_mod=-1, *args, **kwargs
) -> Tuple[np.ndarray, np.ndarray]:
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
