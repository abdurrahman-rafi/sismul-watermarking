import math


def mse(channel_a, channel_b, height, width):
    total = 0.0
    for r in range(height):
        for c in range(width):
            d = channel_a[r][c] - channel_b[r][c]
            total += d * d
    return total / (height * width)


def psnr(channel_a, channel_b, height, width):
    m = mse(channel_a, channel_b, height, width)
    if m == 0.0:
        return float('inf')
    return 10.0 * math.log10(255.0 * 255.0 / m)


def ber(original_bits, extracted_bits):
    if not original_bits:
        return 0.0
    errors = sum(a != b for a, b in zip(original_bits, extracted_bits))
    return errors / len(original_bits)


def nc(original_bits, extracted_bits):
    dot = sum(a * b for a, b in zip(original_bits, extracted_bits))
    norm_a = sum(a * a for a in original_bits)
    norm_b = sum(b * b for b in extracted_bits)
    denom = math.sqrt(norm_a * norm_b)
    if denom == 0.0:
        return 0.0
    return dot / denom
