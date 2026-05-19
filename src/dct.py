import math

N = 8

# Compute dulu: cos_table[x][u] = cos(pi*(2x+1)*u / (2*N))
_cos_table = []
for _x in range(N):
    _row = []
    for _u in range(N):
        _row.append(math.cos(math.pi * (2 * _x + 1) * _u / (2 * N)))
    _cos_table.append(_row)

_ALPHA_0 = math.sqrt(1.0 / N)
_ALPHA_K = math.sqrt(2.0 / N)


def _alpha(k):
    return _ALPHA_0 if k == 0 else _ALPHA_K


def dct2(block):
    coeffs = [[0.0] * N for _ in range(N)]
    for u in range(N):
        au = _alpha(u)
        for v in range(N):
            av = _alpha(v)
            s = 0.0
            for x in range(N):
                cx = _cos_table[x][u]
                for y in range(N):
                    s += block[x][y] * cx * _cos_table[y][v]
            coeffs[u][v] = au * av * s
    return coeffs


def idct2(coeffs):
    block = [[0.0] * N for _ in range(N)]
    for x in range(N):
        for y in range(N):
            s = 0.0
            for u in range(N):
                au = _alpha(u)
                cu = _cos_table[x][u]
                for v in range(N):
                    s += au * _alpha(v) * coeffs[u][v] * cu * _cos_table[y][v]
            block[x][y] = s
    return block
