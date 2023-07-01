from typing import List, Union
from dataclasses import dataclass


@dataclass
class Convolution01xConfiguration:
    input_shape: List[int]
    n_classes: int
    
    output_channels: List[int]
    kernel_sizes: List[int]
    paddings: List[Union[str, int]]
    max_pool_sizes: List[int]
    max_pool_strides: List[int]
    
    avg_size: int
    
    dense_sizes: List[int]