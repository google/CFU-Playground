def is_str(v):
    return isinstance(v, str)


def is_tuple(value, leng=2, typ=str):
    res = isinstance(value, tuple) and len(value) == leng
    if not res:
        return res
    for i in range(leng):
        res = res and isinstance(value[i], typ)
    return res
