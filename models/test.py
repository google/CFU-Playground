def fun(a, b, c):
    d = locals()
    e = d
    print(e)
    print(locals())

fun(1, 2, 3)