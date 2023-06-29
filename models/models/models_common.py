from tensorflow.keras import layers


def make_dense_relu_layer(inp: layers.Layer, dense_size: int, idx=0):
    """
    Dense -> Relu
    """
    dense = layers.Dense(dense_size, name=f"FC{idx}_")(inp)
    relu = layers.ReLU(name=f"FC_RELU{idx}_")(dense)
    return relu