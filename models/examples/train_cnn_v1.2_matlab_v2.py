import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from examples.utils import train_model, TrainConfiguration, string_to_ds
from datasets.fabric import DatasetName
from models.fabric import ModelName, Convolution01xConfiguration


def main():
    train_model(
        TrainConfiguration(
            dataset=DatasetName.MATLAB_V2,
            # dataset_path="data/simc_v2_30k_fpm_0_30_snr/",
            dataset_path=(
                "data/simc_v2_30k_fpm_0_30_snrs_labels.npy",
                "data/simc_v2_30k_fpm_0_30_snrs_data.npy",
            ),
            model=ModelName.CNN_1D_V012,
            model_config=Convolution01xConfiguration(
                input_shape=(1024, 2),
                n_classes=-10,  # train_model will substitue correct value
                output_channels=[32, 48, 64, 96, 128, 192],
                kernel_sizes=[8, 8, 8, 8, 8, 8],
                paddings=["same", "same", "same", "same", "same", "same"],
                max_pool_sizes=[2, 2, 2, 2, 2, 1],
                max_pool_strides=[2, 2, 2, 2, 2, 1],
                avg_size=32,
                dense_sizes=[],
            ),
            n_epochs=3,
            batch_size=256,
            dataset_params={"frames_per_modulation": 30_000, "snrs": list(range(0, 30))},
        ),
    )


if __name__ == "__main__":
    main()
