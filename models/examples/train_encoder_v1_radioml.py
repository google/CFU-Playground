import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from examples.utils import train_model, TrainConfiguration, string_to_ds
from datasets.fabric import DatasetName
from models.fabric import ModelName, EncoderLayerConfiguration, EncoderTransformerConfiguration


def main():
    train_model(
        TrainConfiguration(
            dataset=DatasetName.RADIOML_2016,
            dataset_path="data/radioml_2016/RML2016.10a_dict.pkl",
            model=ModelName.ENCODER_TRANSFORMER_1D_V010,
            model_config=EncoderTransformerConfiguration(
                input_shape=(128, 2),
                n_classes=-1,   # 'train_model' will substitue correct value
                cnn_output_channels=[32],
                cnn_kernel_sizes=[8],
                cnn_paddings=["same"],
                encoder_layer=EncoderLayerConfiguration(
                    h=4,
                    d_k=32,
                    d_v=32,
                    d_model=32,
                    d_ff=128,
                    n=4,
                ),
                avg_size=32,
                dense_sizes=[128],
            ),
            n_epochs=3,
            batch_size=256,
        )
    )


if __name__ == "__main__":
    main()
