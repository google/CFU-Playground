from datasets.dataset import SignalModulationDataset, Dataset
from datasets.matlab_v2_dataset import MatlabV2
from datasets.radio_ml_2016 import RadioML2016

def make_sigmod_ds(name: str, *args, **kwargs) -> SignalModulationDataset:
    datasets_map = {"matlab_v2": MatlabV2, "radioml_2016": RadioML2016}
    if name not in datasets_map:
        raise ValueError(f"Unknown dataset: {name}")
    return datasets_map[name](*args, **kwargs) 
