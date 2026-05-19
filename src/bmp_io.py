import struct


def read_bmp(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    if data[0:2] != b'BM':
        raise ValueError("Not a BMP file")

    pixel_offset = struct.unpack_from('<I', data, 10)[0]
    width = struct.unpack_from('<i', data, 18)[0]
    height = struct.unpack_from('<i', data, 22)[0]
    bpp = struct.unpack_from('<H', data, 28)[0]

    if bpp != 24:
        raise ValueError(f"Only 24-bit BMP supported, got {bpp}-bit")

    flip = height > 0
    height = abs(height)

    row_stride = (width * 3 + 3) & ~3
    pixels = []
    for row in range(height):
        src_row = (height - 1 - row) if flip else row
        offset = pixel_offset + src_row * row_stride
        r_row = []
        for col in range(width):
            b = data[offset + col * 3]
            g = data[offset + col * 3 + 1]
            r = data[offset + col * 3 + 2]
            r_row.append((r, g, b))
        pixels.append(r_row)

    return pixels, width, height


def write_bmp(filepath, pixels, width, height):
    row_stride = (width * 3 + 3) & ~3
    row_padding = row_stride - width * 3
    pixel_data_size = row_stride * height
    file_size = 54 + pixel_data_size

    header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
    dib = struct.pack('<IiiHHIIiiII',
                      40, width, height, 1, 24, 0,
                      pixel_data_size, 0, 0, 0, 0)

    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(dib)
        for row in range(height - 1, -1, -1):
            for col in range(width):
                r, g, b = pixels[row][col]
                f.write(bytes([int(b), int(g), int(r)]))
            if row_padding:
                f.write(b'\x00' * row_padding)


def write_bmp_grayscale(filepath, matrix, width, height):
    pixels = []
    for row in range(height):
        r_row = []
        for col in range(width):
            v = int(matrix[row][col])
            if v < 0:
                v = 0
            elif v > 255:
                v = 255
            r_row.append((v, v, v))
        pixels.append(r_row)
    write_bmp(filepath, pixels, width, height)
