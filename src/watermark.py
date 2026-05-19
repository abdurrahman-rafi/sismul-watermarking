from src.color import image_rgb_to_ycbcr, image_ycbcr_to_rgb
from src.dct import dct2, idct2
from src.utils import clamp, copy_matrix, pad_to_multiple, extract_block, insert_block
from src.image_io import read_image

DELTA = 30
COEF_POS = (4, 1)
BLOCK_SIZE = 8


WM_TARGET_W = 32
WM_TARGET_H = 32


def load_watermark_bits(filepath):
    
    # Load watermark dari image (BMP, JPEG, PNG).
    # Kalau gak 32x32, resize
    # Return (bits_list, wm_width, wm_height).
    
    from src.image_io import read_image_grayscale_resized
    pixels, wm_width, wm_height = read_image(filepath)
    if wm_width != WM_TARGET_W or wm_height != WM_TARGET_H:
        print(f"  [watermark] resizing {wm_width}×{wm_height} → {WM_TARGET_W}×{WM_TARGET_H}")
        pixels, wm_width, wm_height = read_image_grayscale_resized(
            filepath, WM_TARGET_W, WM_TARGET_H
        )
    bits = []
    for row in pixels:
        for r, g, b in row:
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            bits.append(1 if gray > 127 else 0)
    return bits, wm_width, wm_height


def _embed_bit(coeffs, bit, delta):
    u, v = COEF_POS
    coef = coeffs[u][v]
    q = round(coef / delta)
    parity = q % 2
    # Normalize parity to 0 or 1 (handle negatives)
    parity = parity if parity >= 0 else parity + 2
    if bit == 0:
        if parity != 0:
            # need even q: try q-1 and q+1
            if abs((q - 1) * delta - coef) <= abs((q + 1) * delta - coef):
                q -= 1
            else:
                q += 1
    else:
        if parity == 0:
            if abs((q - 1) * delta - coef) <= abs((q + 1) * delta - coef):
                q -= 1
            else:
                q += 1
    coeffs[u][v] = q * delta
    return coeffs


def embed_watermark(host_pixels, width, height, wm_bits, delta=DELTA):
    y_ch, cb_ch, cr_ch = image_rgb_to_ycbcr(host_pixels)

    # Level shift
    for r in range(height):
        for c in range(width):
            y_ch[r][c] -= 128.0

    y_padded = pad_to_multiple(y_ch, BLOCK_SIZE)
    pad_rows = len(y_padded)
    pad_cols = len(y_padded[0])

    bit_idx = 0
    num_bits = len(wm_bits)

    for br in range(0, pad_rows, BLOCK_SIZE):
        for bc in range(0, pad_cols, BLOCK_SIZE):
            if bit_idx >= num_bits:
                break
            block = extract_block(y_padded, br, bc, BLOCK_SIZE)
            coeffs = dct2(block)
            coeffs = _embed_bit(coeffs, wm_bits[bit_idx], delta)
            restored = idct2(coeffs)
            insert_block(y_padded, restored, br, bc)
            bit_idx += 1
        if bit_idx >= num_bits:
            break

    # Copy lagi balik ke y_ch (unpadded)
    for r in range(height):
        for c in range(width):
            y_ch[r][c] = clamp(y_padded[r][c] + 128.0, 0, 255)

    pixels_out = image_ycbcr_to_rgb(y_ch, cb_ch, cr_ch)
    return pixels_out


def extract_watermark(wm_pixels, width, height, wm_length, delta=DELTA):
    y_ch, _, _ = image_rgb_to_ycbcr(wm_pixels)

    for r in range(height):
        for c in range(width):
            y_ch[r][c] -= 128.0

    y_padded = pad_to_multiple(y_ch, BLOCK_SIZE)
    pad_rows = len(y_padded)
    pad_cols = len(y_padded[0])

    bits = []
    for br in range(0, pad_rows, BLOCK_SIZE):
        for bc in range(0, pad_cols, BLOCK_SIZE):
            if len(bits) >= wm_length:
                break
            block = extract_block(y_padded, br, bc, BLOCK_SIZE)
            coeffs = dct2(block)
            u, v = COEF_POS
            coef = coeffs[u][v]
            q = round(coef / delta)
            bits.append(0 if q % 2 == 0 else 1)
        if len(bits) >= wm_length:
            break

    return bits
