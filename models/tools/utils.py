def is_str(v):
    return isinstance(v, str)


def is_tuple(value, leng=2, typ=str):
    res = isinstance(value, tuple) and len(value) == leng
    if not res:
        return res
    for i in range(leng):
        res = res and isinstance(value[i], typ)
    return res

def all_are_nones(*args):
    result = True
    for v in args:
        result = result and (v is None)
    return result

def some_are_nones(*args):
    result = False
    for v in args:
        result = result or (v is None)
    return result

def set_seed(SEED):
    import random
    import numpy as np
    import tensorflow as tf

    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def reload_module(m):
    import sys
    import importlib

    if isinstance(m, str):
        importlib.reload(sys.modules[m])
    else:
        importlib.reload(m)
