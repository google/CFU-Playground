from typing import Any, Dict
from models.cnn.cnn_1d_v010 import make_cnn_1d_v010 as __make_cnn_1d_v010
from models.cnn.cnn_1d_v012 import make_cnn_1d_v012 as __make_cnn_1d_v012
from models.cnn.cnn_1d_v01x_common import Convolution01xConfiguration
from models.encoder_transformer.encoder_transformer_1d_v1 import (
    EncoderTransformerConfiguration,
    EncoderLayerConfiguration,
    make_encoder_transformer_1d_v1 as __make_encoder_transformer_1d_v1,
)
from enum import Enum


class ModelName(Enum):
    CNN_1D_V010 = (0,)
    CNN_1D_V012 = (1,)
    ENCODER_TRANSFORMER_1D_V010 = (2,)


__models = {
    ModelName.CNN_1D_V010: __make_cnn_1d_v010,
    ModelName.CNN_1D_V012: __make_cnn_1d_v012,
    ModelName.ENCODER_TRANSFORMER_1D_V010: __make_encoder_transformer_1d_v1,
}


def make_sigmod_model(name: str, config: Any):
    if name not in __models:
        raise ValueError(f"Unsupported model: {name}")
    return __models[name](config)


def load_model_configuration(model_configuration: Dict):
    name = model_configuration["name"]
    if name == "cnn_1d_v01x":
        return Convolution01xConfiguration.from_dict(model_configuration)
    if name == "encoder_transformer_1d_v01x":
        return EncoderTransformerConfiguration.from_dict(model_configuration)
    return ValueError(f"Unknown model name: {name}")


def list_available_models():
    return list(__models.keys())
