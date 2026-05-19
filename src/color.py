from src.utils import clamp

# Menggunakakan persamaan matematika
def rgb_to_ycbcr(r, g, b):
    y  =  0.299 * r + 0.587 * g + 0.114 * b
    cb = -0.169 * r - 0.331 * g + 0.500 * b + 128.0
    cr =  0.500 * r - 0.419 * g - 0.081 * b + 128.0
    return y, cb, cr


# Reverse dari persamaan diatas
def ycbcr_to_rgb(y, cb, cr):
    r = y + 1.402 * (cr - 128.0)
    g = y - 0.344 * (cb - 128.0) - 0.714 * (cr - 128.0)
    b = y + 1.772 * (cb - 128.0)
    return clamp(round(r)), clamp(round(g)), clamp(round(b))


def image_rgb_to_ycbcr(pixels):
    height = len(pixels)
    width = len(pixels[0])
    y_ch  = [[0.0] * width for _ in range(height)]
    cb_ch = [[0.0] * width for _ in range(height)]
    cr_ch = [[0.0] * width for _ in range(height)]
    for row in range(height):
        for col in range(width):
            r, g, b = pixels[row][col]
            y, cb, cr = rgb_to_ycbcr(r, g, b)
            y_ch[row][col]  = y
            cb_ch[row][col] = cb
            cr_ch[row][col] = cr
    return y_ch, cb_ch, cr_ch


def image_ycbcr_to_rgb(y_ch, cb_ch, cr_ch):
    height = len(y_ch)
    width = len(y_ch[0])
    pixels = []
    for row in range(height):
        r_row = []
        for col in range(width):
            r, g, b = ycbcr_to_rgb(y_ch[row][col], cb_ch[row][col], cr_ch[row][col])
            r_row.append((r, g, b))
        pixels.append(r_row)
    return pixels
