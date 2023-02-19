import numpy as np
from scipy import io
from pathlib import Path
import glob
import time
import pandas


saven_pam4_path = Path(__file__).parent / "seven_pam4.mat"
saven_pam4_data: np.ndarray = io.loadmat(saven_pam4_path)['unknownFrames']

train_data_path = Path(__file__).parent / "train_data"

def load_train_data(classes):
    before = time.time()
    train_data = {}

    n_data = 0
    for cl in classes:
        mat_files = glob.glob(f"{train_data_path}/*{cl}*.mat")
        train_data[cl] = []
        for mat_file in mat_files:
            np_data = io.loadmat(train_data_path / mat_file)['frame']
            n_data += len(np_data)
            train_data[cl].append(np_data)
    after = time.time()
    print(f"[debug] Loaded train data with size {n_data} in {after - before}s")
    return train_data

test_data_path = Path(__file__).parent / "test_data"

def load_test_data():
    test_data = {}
    before = time.time()
    labels = pandas.read_csv(test_data_path / "test_labels.csv")['Labels'].to_list()
    data: np.ndarray = io.loadmat(test_data_path / "test_frames.mat")['rxTestFrames']
    assert len(labels) == data.shape[-1]
    for i, label in enumerate(labels):
        if label not in test_data:
            test_data[label] = []
        test_data[label].append(data[:, :, :, i].astype(np.float32))
    after = time.time()
    print(f"[debug] Loaded train data with size {len(labels)} in {after - before}s")
    return test_data
