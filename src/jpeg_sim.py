from src.dct import dct2, idct2
from src.utils import clamp, pad_to_multiple, extract_block, insert_block
from src.color import image_rgb_to_ycbcr, image_ycbcr_to_rgb

Q_LUMINANCE_BASE = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
]

Q_CHROMINANCE_BASE = [
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
]


def get_q_table(qf, base):
    if qf <= 0:
        qf = 1
    if qf >= 100:
        scale = 0.0
    elif qf >= 50:
        scale = (100 - qf) / 50.0
    else:
        scale = 50.0 / qf

    table = []
    for row in base:
        t_row = []
        for val in row:
            if scale == 0.0:
                q = 1
            else:
                q = max(1, round(val * scale))
            t_row.append(q)
        table.append(t_row)
    return table


def simulate_jpeg(channel, height, width, qf, q_base):
    q_table = get_q_table(qf, q_base)

    # Level shift
    shifted = [[channel[r][c] - 128.0 for c in range(width)] for r in range(height)]

    padded = pad_to_multiple(shifted, 8)
    pad_rows = len(padded)
    pad_cols = len(padded[0])

    for br in range(0, pad_rows, 8):
        for bc in range(0, pad_cols, 8):
            block = extract_block(padded, br, bc, 8)
            coeffs = dct2(block)
            # Quantize + dequantize
            for u in range(8):
                for v in range(8):
                    coeffs[u][v] = round(coeffs[u][v] / q_table[u][v]) * q_table[u][v]
            restored = idct2(coeffs)
            insert_block(padded, restored, br, bc)

    # Level shift back and unpad
    result = [[0.0] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            result[r][c] = clamp(padded[r][c] + 128.0, 0.0, 255.0)

    return result


def simulate_jpeg_rgb(pixels, width, height, qf):
    y_ch, cb_ch, cr_ch = image_rgb_to_ycbcr(pixels)
    y_out  = simulate_jpeg(y_ch,  height, width, qf, Q_LUMINANCE_BASE)
    cb_out = simulate_jpeg(cb_ch, height, width, qf, Q_CHROMINANCE_BASE)
    cr_out = simulate_jpeg(cr_ch, height, width, qf, Q_CHROMINANCE_BASE)
    return image_ycbcr_to_rgb(y_out, cb_out, cr_out)
