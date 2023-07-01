from typing import Any
from models.cnn.cnn_1d_v010 import make_cnn_1d_v010 as __make_cnn_1d_v010
from models.cnn.cnn_1d_v012 import make_cnn_1d_v012 as __make_cnn_1d_v012
from models.cnn.cnn_1d_v01x_common import Convolution01xConfiguration
from models.encoder_transformer.encoder_transformer_1d_v1 import (
    EncoderTransformerConfiguration,
    EncoderLayerConfiguration,
    make_encoder_transformer_1d_v1 as __make_encoder_transformer_1d_v1,
)

__models = {
    "cnn_1d_v1.0": __make_cnn_1d_v010,
    "cnn_1d_v1.2": __make_cnn_1d_v012,
    "encoder_transformer_1d_v1": __make_encoder_transformer_1d_v1,
}


def make_sigmod_model(name: str, config: Any):
    if name not in __models:
        raise ValueError(f"Unsupported model: {name}")
    return __models[name](config)


def list_available_models():
    return list(__models.keys())
