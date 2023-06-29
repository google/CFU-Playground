from typing import List
from dataclasses import dataclass
from tensorflow import keras
from tensorflow.keras import layers
from models.layers.encoder import SigModEncoder
from models.models_common import make_dense_relu_layer as __make_dense_relu_layer
from typing import Union


@dataclass
class EncoderLayerConfiguration:
    h: int
    d_k: int
    d_v: int
    d_model: int
    d_ff: int
    n: int 
    
@dataclass
class EncoderTransformerConfiguration:
    input_shape: List[int]

    cnn_output_channels: List[int]
    cnn_kernel_sizes: List[int]
    cnn_paddings: List[Union[str, int]]

    encoder_layer: EncoderLayerConfiguration

    dense_sizes: List[int]

    avg_size: int
    
    n_classes: int


def _create_convolution_layer(
    inp: layers.Layer,
    output_channels: int,
    kernel_size: int,
    padding: Union[str, int],
    idx=0,
):
    cnn = layers.Conv1D(
        output_channels,
        kernel_size,
        padding=padding,
        name=f"CNN{idx}_",
    )(inp)
    relu = layers.ReLU(name=f"RELU{idx}_")(cnn)
    return relu


def make_encoder_transformer_1d_v1(config: EncoderTransformerConfiguration):
    N_CNNs = len(config.cnn_output_channels)
    N_DNNs = len(config.dense_sizes)
    assert len(config.cnn_output_channels) == len(config.cnn_kernel_sizes) == len(config.cnn_paddings)
    assert N_CNNs > 0
    assert N_DNNs > 0

    InputLayer = keras.Input(shape=config.input_shape)
    
    cur_layer = InputLayer
    for i in range(N_CNNs):
        cur_layer = _create_convolution_layer(
            cur_layer,
            config.cnn_output_channels[i],
            config.cnn_kernel_sizes[i],
            config.cnn_paddings[i],
            idx=i
        )

    enc_conf_dict = config.encoder_layer.__dict__
    
    encoder1 = SigModEncoder(**enc_conf_dict, rate=0.1, name="ENC1_")(cur_layer, None, True)
    avg_pool1 = layers.AveragePooling1D(config.avg_size, padding="same", name="AVG1_")(encoder1)
    flatten1 = layers.Flatten(name="FLT1_")(avg_pool1)

    cur_layer = flatten1
    for i in range(N_DNNs):
        cur_layer = __make_dense_relu_layer(cur_layer, config.dense_sizes[i], idx=i)
        
    FC = layers.Dense(config.n_classes, name=f"FC_{N_DNNs+1}_")(cur_layer)
    Output = layers.Softmax()(FC)
    model = keras.Model(inputs=[InputLayer], outputs=[Output])
    return model
