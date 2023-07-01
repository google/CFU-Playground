import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from examples.utils import train_model, TrainConfiguration, string_to_ds
from datasets.fabric import DatasetName
from models.fabric import ModelName, Convolution01xConfiguration


def main():
    train_model(
        TrainConfiguration(
            dataset=DatasetName.RADIOML_2016,
            dataset_path="data/radioml_2016/RML2016.10a_dict.pkl",
            model=ModelName.CNN_1D_V012,
            model_config=Convolution01xConfiguration(
                input_shape=(128, 2),
                n_classes=-10,  # train_model will substitue correct value
                output_channels=[32, 48, 64, 96, 128, 192],
                kernel_sizes=[8, 8, 8, 8, 8, 8],
                paddings=["same", "same", "same", "same", "same", "same"],
                max_pool_sizes=[1, 1, 2, 1, 2, 1],
                max_pool_strides=[1, 1, 2, 1, 2, 1],
                avg_size=32,
                dense_sizes=[],
            ),
            n_epochs=3,
            batch_size=256,
        )
    )


if __name__ == "__main__":
    main()
