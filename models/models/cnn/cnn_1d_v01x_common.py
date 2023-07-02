from typing import List, Union
from dataclasses import dataclass
from ..configuration_utils import ConfigurationUtils


@dataclass
class Convolution01xConfiguration(ConfigurationUtils):
    input_shape: List[int]
    n_classes: int

    output_channels: List[int]
    kernel_sizes: List[int]
    paddings: List[Union[str, int]]
    max_pool_sizes: List[int]
    max_pool_strides: List[int]

    avg_size: int

    dense_sizes: List[int]

    # name: str
    name: str = "cnn_1d_v01x"
