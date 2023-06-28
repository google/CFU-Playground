from models.datasets.dataset import SignalModulationDataset, Dataset

def make_sigmod_ds(name: str, *args, **kwargs) -> SignalModulationDataset:
    if name == "matlab_v2":
        return SignalModulationDataset(*args, **kwargs)
    else:
        raise ValueError(f"Unknown dataset: {name}")