import math
import os
from src.bmp_io import write_bmp

HOST_SIZE = 512
WM_SIZE = 32
ASSETS_DIR = "assets"


def generate_host_image(size):
    pixels = []
    for row in range(size):
        r_row = []
        for col in range(size):
            r = int(255 * col / (size - 1))
            g = int(255 * row / (size - 1))
            checker = ((row // 32) + (col // 32)) % 2
            b = 200 if checker else 55
            r_row.append((r, g, b))
        pixels.append(r_row)
    return pixels


def generate_watermark(size):
    """Generate a 32x32 binary watermark with letter 'W' pattern."""
    grid = [[0] * size for _ in range(size)]

    # Draw a thick border
    for r in range(size):
        for c in range(size):
            if r < 2 or r >= size - 2 or c < 2 or c >= size - 2:
                grid[r][c] = 1

    # Draw letter 'W' inside (hand-crafted on 28x28 inner grid, offset by 2)
    # W strokes: two V shapes side by side
    half = size // 2
    for row in range(4, size - 4):
        t = (row - 4) / (size - 8)  # 0..1
        # left stroke going down-right
        c1 = int(4 + t * (half - 4))
        # right stroke going down-left
        c2 = int(size - 4 - t * (half - 4))
        # middle strokes (the two inner diagonals)
        c3 = int(half - t * (half // 2 - 2))
        c4 = int(half + t * (half // 2 - 2))
        for dc in range(-1, 2):
            for c in [c1, c2, c3, c4]:
                cc = c + dc
                if 0 <= cc < size:
                    grid[row][cc] = 1

    pixels = []
    for row in range(size):
        r_row = []
        for c in range(size):
            v = 255 if grid[row][c] == 1 else 0
            r_row.append((v, v, v))
        pixels.append(r_row)
    return pixels


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    host = generate_host_image(HOST_SIZE)
    write_bmp(os.path.join(ASSETS_DIR, "host.bmp"), host, HOST_SIZE, HOST_SIZE)
    print(f"Generated assets/host.bmp ({HOST_SIZE}x{HOST_SIZE})")

    wm = generate_watermark(WM_SIZE)
    write_bmp(os.path.join(ASSETS_DIR, "watermark.bmp"), wm, WM_SIZE, WM_SIZE)
    print(f"Generated assets/watermark.bmp ({WM_SIZE}x{WM_SIZE})")


if __name__ == "__main__":
    main()
