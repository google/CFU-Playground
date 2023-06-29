"""
CNN that consists of:
    (Convolution -> MaxPool -> BatNorm -> Relu) x n -> 
    AveragePool -> Flatten -> 
    (Dense -> Relu) x k -> SoftMax
"""
import tensorflow as tf
from typing import List, Union
from dataclasses import dataclass
from tensorflow.keras import layers
from tensorflow import keras
from models.layers.custom_batch_norm import CustomBatchNorm
from models.models_common import make_dense_relu_layer as __make_dense_relu_layer


@dataclass
class ConvolutionConfiguration:
    input_shape: List[int]
    n_classes: int
    
    output_channels: List[int]
    kernel_sizes: List[int]
    paddings: List[Union[str, int]]
    max_pool_sizes: List[int]
    max_pool_strides: List[int]
    
    avg_size: int
    
    dense_sizes: List[int]


def _make_convolutional_layer(
    inp: layers.Layer,
    output_channels: int,
    kernel_size: int,
    padding: Union[int, str],
    max_pool_size: int,
    max_pool_stride: int,
    idx=0,
):
    """
    CNN -> Maxpool -> BatchNorm -> Relu
    """
    cnn = layers.Conv2D(
        output_channels,
        (1, kernel_size),
        padding=padding,
        name=f"CNN{idx}_",
    )(inp)

    # TODO: Verify if pool size 1 is OK
    max_pool = layers.MaxPool2D(
        pool_size=(1, max_pool_size), strides=(1, max_pool_stride), name=f"MAX_POOL_{idx}_"
    )(cnn)

    batch_norm = CustomBatchNorm(name=f"BN{idx}_")(max_pool)
    relu = layers.ReLU(name=f"CNN_REL{idx}_")(batch_norm)
    return relu





def make_cnn_1d_v1(
    cnn_conf: ConvolutionConfiguration,
    *args,
    **kwargs,
):
    InputLayer = keras.Input(shape=(1, 128, 2))
    assert (
        len(cnn_conf.output_channels)
        == len(cnn_conf.kernel_sizes)
        == len(cnn_conf.paddings)
        == len(cnn_conf.max_pool_sizes)
        == len(cnn_conf.max_pool_strides)
    ), "make_cnn_1d_v1: Convolution layers parameters hace inconsistent sizes"
    
    N_CNNs = len(cnn_conf.output_channels)
    N_DNNS = len(cnn_conf.dense_sizes)
    
    assert N_CNNs > 0
    
    cur_layer = InputLayer
    for i in range(N_CNNs):
        cur_layer = _make_convolutional_layer(
            cur_layer,
            cnn_conf.output_channels[i],
            cnn_conf.kernel_sizes[i],
            cnn_conf.paddings[i],
            cnn_conf.max_pool_sizes[i],
            cnn_conf.max_pool_strides[i],
            idx=i
        )
        
    cur_layer = layers.AveragePooling2D((1, cnn_conf.avg_size), name="AVG1_")(cur_layer)
    cur_layer = layers.Flatten(name="FLT1_")(cur_layer)

    for i in range(N_DNNS):
        cur_layer = __make_dense_relu_layer(
            cur_layer, 
            cnn_conf.dense_sizes[i],
            idx=i
        )
        
    cur_layer = layers.Dense(cnn_conf.n_classes, name=f"FC_{N_DNNS+1}_")(cur_layer)
    SoftMax = layers.Softmax()(cur_layer)
    Output = layers.Flatten()(SoftMax)

    model = keras.Model(inputs=[InputLayer], outputs=[Output])
    return model
