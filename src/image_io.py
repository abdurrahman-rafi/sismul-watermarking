
# Unified image I/O: BMP handled natively, JPEG/PNG via Pillow.
# BMP dihandle native, JPEG/PNG menggunakan library pillow

import os
from src.bmp_io import read_bmp, write_bmp, write_bmp_grayscale

_SUPPORTED_EXT = {'.bmp', '.jpg', '.jpeg', '.png'}


def _pillow_to_pixels(img):
    img = img.convert('RGB')
    w, h = img.size
    data = list(img.getdata())
    pixels = [data[row * w:(row + 1) * w] for row in range(h)]
    return pixels, w, h


def read_image(filepath):
    
    # Read JPEG, PNG, atau BMP. Return (pixels, width, height).
    # pixels[row][col] = (R, G, B) int tuples, top-down.
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.bmp':
        return read_bmp(filepath)
    if ext not in _SUPPORTED_EXT:
        raise ValueError(f"Unsupported format: {ext}. Supported: {_SUPPORTED_EXT}")
    from PIL import Image
    img = Image.open(filepath)
    return _pillow_to_pixels(img)


def read_image_grayscale_resized(filepath, target_w, target_h):
    
    # Read image, convert ke grayscale, resize ke dimensi yang sesuai.
    # Return(pixels, target_w, target_h), pixels[row][col] = (v, v, v).
    
    ext = os.path.splitext(filepath)[1].lower()
    from PIL import Image
    if ext == '.bmp':
        # Use native reader then convert via Pillow in-memory
        raw, w, h = read_bmp(filepath)
        img = Image.new('RGB', (w, h))
        img.putdata([(r, g, b) for row in raw for r, g, b in row])
    else:
        img = Image.open(filepath)

    img = img.convert('L').resize((target_w, target_h), Image.LANCZOS)
    data = list(img.getdata())
    pixels = [
        [(data[row * target_w + col],) * 3 for col in range(target_w)]
        for row in range(target_h)
    ]
    return pixels, target_w, target_h


def write_image(filepath, pixels, width, height, jpeg_quality=95):
    # Write pixel ke BMP, JPEG, or PNG.
    # pixels[row][col] = (R, G, B) tuple int.
    
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.bmp':
        write_bmp(filepath, pixels, width, height)
        return
    from PIL import Image
    img = Image.new('RGB', (width, height))
    img.putdata([(r, g, b) for row in pixels for r, g, b in row])
    if ext in ('.jpg', '.jpeg'):
        img.save(filepath, 'JPEG', quality=jpeg_quality)
    else:
        img.save(filepath)


def write_image_grayscale(filepath, matrix, width, height, jpeg_quality=95):
    # Write 2D float ke image grayscale
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.bmp':
        write_bmp_grayscale(filepath, matrix, width, height)
        return
    from PIL import Image
    img = Image.new('L', (width, height))
    flat = []
    for row in matrix:
        for val in row:
            v = int(val)
            flat.append(max(0, min(255, v)))
    img.putdata(flat)
    if ext in ('.jpg', '.jpeg'):
        img.save(filepath, 'JPEG', quality=jpeg_quality)
    else:
        img.save(filepath)
