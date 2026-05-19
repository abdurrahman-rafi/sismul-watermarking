"""
step_by_step.py — Visualisasi tahap demi tahap pipeline watermarking DCT.
Output: folder steps/ berisi gambar PNG bernomor urut.

Waktu estimasi (~512x512): 5-10 menit (pure Python DCT).
"""

import os
import math

from src.image_io import read_image, write_image, write_image_grayscale
from src.watermark import load_watermark_bits, embed_watermark, extract_watermark, DELTA
from src.jpeg_sim import simulate_jpeg_rgb
from src.color import image_rgb_to_ycbcr
from src.dct import dct2
from src.utils import clamp, pad_to_multiple, extract_block

STEPS_DIR = "steps"
ASSETS_DIR = "assets"

DEMO_QFS = [100, 80, 50, 20]
WM_SCALE = 8   # 32×32 → 256×256

_HOST_CANDIDATES = ["host.jpg", "host.jpeg", "host.png", "host.bmp"]
_WM_CANDIDATES   = ["watermark.jpg", "watermark.jpeg", "watermark.png", "watermark.bmp"]


# ── helpers ────────────────────────────────────────────────────────────────────

def find_asset(candidates):
    for name in candidates:
        path = os.path.join(ASSETS_DIR, name)
        if os.path.exists(path):
            return path
    return None


def save(name, pixels, w, h):
    path = os.path.join(STEPS_DIR, name)
    write_image(path, pixels, w, h)
    print(f"  → {path}")


def save_gray(name, matrix, w, h):
    path = os.path.join(STEPS_DIR, name)
    write_image_grayscale(path, matrix, w, h)
    print(f"  → {path}")


def scale_nearest(pixels, w, h, factor):
    nw, nh = w * factor, h * factor
    out = []
    for r in range(nh):
        row = []
        sr = r // factor
        for c in range(nw):
            row.append(pixels[sr][c // factor])
        out.append(row)
    return out, nw, nh


def diff_amplified(a_pix, b_pix, w, h, factor=10):
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            ar, ag, ab = a_pix[r][c]
            br, bg, bb = b_pix[r][c]
            row.append((
                clamp((br - ar) * factor + 128),
                clamp((bg - ag) * factor + 128),
                clamp((bb - ab) * factor + 128),
            ))
        out.append(row)
    return out


def dct_spectrum(y_ch, h, w):
    print("    Menghitung DCT spectrum (bisa 1-2 menit)...")
    padded = pad_to_multiple(y_ch, 8)
    ph, pw = len(padded), len(padded[0])

    log_mag = [[0.0] * pw for _ in range(ph)]
    for br in range(0, ph, 8):
        for bc in range(0, pw, 8):
            block = extract_block(padded, br, bc, 8)
            coeffs = dct2(block)
            for u in range(8):
                for v in range(8):
                    log_mag[br + u][bc + v] = math.log1p(abs(coeffs[u][v]))

    flat = [log_mag[r][c] for r in range(ph) for c in range(pw)]
    mx = max(flat) or 1.0
    out = [[log_mag[r][c] / mx * 255.0 for c in range(w)] for r in range(h)]
    return out


def dct_spectrum_highlighted(spectrum, h, w):
    """DCT spectrum dengan titik merah di koefisien (4,1) tiap blok 8×8."""
    out = [[(clamp(int(spectrum[r][c])),) * 3 for c in range(w)] for r in range(h)]
    for br in range(0, h, 8):
        for bc in range(0, w, 8):
            r, c = br + 4, bc + 1
            if r < h and c < w:
                out[r][c] = (255, 80, 80)
    return out


def active_blocks_map(img_w, img_h, wm_bits_count, block_size=8, scale=8):
    """
    Peta blok aktif: satu piksel per blok 8×8.
    Putih = blok yang menyimpan bit watermark (wm_bits_count blok pertama).
    Abu gelap = blok tidak dimodifikasi.
    """
    blocks_x = img_w // block_size
    blocks_y = img_h // block_size
    total_blocks = blocks_x * blocks_y

    pixels = []
    idx = 0
    for by in range(blocks_y):
        row = []
        for bx in range(blocks_x):
            if idx < wm_bits_count:
                row.append((255, 255, 255))   # aktif
            else:
                row.append((40, 40, 40))      # tidak aktif
            idx += 1
        pixels.append(row)

    out, ow, oh = scale_nearest(pixels, blocks_x, blocks_y, scale)
    return out, ow, oh


def single_block_diagram(cell_size=32):
    """
    Diagram satu blok 8×8 DCT coefficient grid.
    Warna setiap sel: gradien abu dari terang (DC, pojok kiri-atas) ke gelap (frekuensi tinggi).
    Sel (4,1) berwarna merah = posisi embed watermark.
    Border tipis hitam di setiap sel.
    """
    N = 8
    img_size = N * cell_size
    pixels = [[(0, 0, 0)] * img_size for _ in range(img_size)]

    for u in range(N):
        for v in range(N):
            # Kecerahan berdasarkan frekuensi: DC (0,0) paling terang
            brightness = round(200 - (u + v) / 14 * 160)
            if u == 4 and v == 1:
                cell_color = (220, 50, 50)   # merah = posisi embed
            else:
                b = brightness
                cell_color = (b, b, b)

            r0 = u * cell_size
            c0 = v * cell_size
            for pr in range(cell_size):
                for pc in range(cell_size):
                    # Border 1px hitam di tepi sel
                    if pr == 0 or pc == 0 or pr == cell_size - 1 or pc == cell_size - 1:
                        pixels[r0 + pr][c0 + pc] = (0, 0, 0)
                    else:
                        pixels[r0 + pr][c0 + pc] = cell_color

    return pixels, img_size, img_size


def bits_to_matrix(bits, wh, ww):
    return [[float(bits[r * ww + c] * 255) for c in range(ww)] for r in range(wh)]


# ── main ────────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(STEPS_DIR, exist_ok=True)

    host_path = find_asset(_HOST_CANDIDATES)
    wm_path   = find_asset(_WM_CANDIDATES)
    if not host_path or not wm_path:
        print("ERROR: Assets tidak ditemukan. Jalankan generate_assets.py dulu.")
        return

    print(f"Host:      {host_path}")
    print(f"Watermark: {wm_path}")

    host_pixels, W, H = read_image(host_path)
    wm_bits, WW, WH   = load_watermark_bits(wm_path)
    wm_length          = WW * WH

    # ── Tahap 1: Input asli ────────────────────────────────────────────────────
    print("\n[Tahap 1] Input asli")
    save("01_host.png", host_pixels, W, H)

    from src.image_io import read_image_grayscale_resized
    wm_raw, rw, rh = read_image(wm_path)
    if rw != WW or rh != WH:
        wm_raw, rw, rh = read_image_grayscale_resized(wm_path, WW, WH)
    wm_big, bw, bh = scale_nearest(wm_raw, WW, WH, WM_SCALE)
    save("02_watermark_original.png", wm_big, bw, bh)

    # ── Tahap 2: Konversi ruang warna ──────────────────────────────────────────
    print("\n[Tahap 2] Konversi RGB → YCbCr")
    y_ch, cb_ch, cr_ch = image_rgb_to_ycbcr(host_pixels)

    save_gray("03_Y_luminance.png",    y_ch,  H, W)
    save_gray("04_Cb_chroma_blue.png", cb_ch, H, W)
    save_gray("05_Cr_chroma_red.png",  cr_ch, H, W)

    # ── Tahap 3: Domain DCT ────────────────────────────────────────────────────
    print("\n[Tahap 3] Domain DCT")
    spectrum = dct_spectrum(y_ch, H, W)
    save_gray("06_dct_spectrum.png", spectrum, W, H)

    highlighted = dct_spectrum_highlighted(spectrum, H, W)
    path = os.path.join(STEPS_DIR, "07_dct_embed_position.png")
    write_image(path, highlighted, W, H)
    print(f"  → {path}  (titik merah = koefisien (4,1) di setiap blok)")

    # Peta blok aktif: mana yang benar-benar dimodifikasi
    act_pix, act_w, act_h = active_blocks_map(W, H, wm_length, scale=8)
    save("07b_active_blocks.png", act_pix, act_w, act_h)
    print(f"    putih = {wm_length} blok aktif, abu gelap = blok tidak disentuh")

    # Diagram satu blok DCT
    blk_pix, blk_w, blk_h = single_block_diagram(cell_size=32)
    save("07c_single_block_coef.png", blk_pix, blk_w, blk_h)
    print(f"    sel merah = koefisien (baris 4, kolom 1) tempat 1 bit disisipkan")

    # ── Tahap 4: Embedding ─────────────────────────────────────────────────────
    print("\n[Tahap 4] Embedding watermark")
    print("  Menyisipkan watermark... (bisa 1-2 menit)")
    watermarked = embed_watermark(host_pixels, W, H, wm_bits)
    save("08_watermarked.png", watermarked, W, H)

    diff = diff_amplified(host_pixels, watermarked, W, H, factor=20)
    save("09_difference_x20.png", diff, W, H)
    print("    abu-abu=tidak berubah, terang/gelap=delta piksel × 20")

    # ── Tahap 5: Kompresi JPEG ─────────────────────────────────────────────────
    print("\n[Tahap 5] Simulasi kompresi JPEG")
    compressed_by_qf = {}
    for i, qf in enumerate(DEMO_QFS, start=10):
        print(f"  QF={qf} ...", end=" ", flush=True)
        comp = simulate_jpeg_rgb(watermarked, W, H, qf)
        compressed_by_qf[qf] = comp
        save(f"{i:02d}_compressed_QF{qf:03d}.png", comp, W, H)

    # ── Tahap 6: Ekstraksi watermark ───────────────────────────────────────────
    print("\n[Tahap 6] Ekstraksi watermark")
    from src.metrics import ber as calc_ber
    idx = 10 + len(DEMO_QFS)
    for qf in DEMO_QFS:
        print(f"  Ekstrak dari QF={qf} ...", end=" ", flush=True)
        bits_out = extract_watermark(compressed_by_qf[qf], W, H, wm_length)

        mat = bits_to_matrix(bits_out, WH, WW)
        mat_big = [[mat[r // WM_SCALE][c // WM_SCALE]
                    for c in range(WW * WM_SCALE)]
                   for r in range(WH * WM_SCALE)]

        b = calc_ber(wm_bits, bits_out)
        path = os.path.join(STEPS_DIR, f"{idx:02d}_extracted_QF{qf:03d}.png")
        write_image_grayscale(path, mat_big, WW * WM_SCALE, WH * WM_SCALE)
        print(f"→ {path}  (BER={b:.3f})")
        idx += 1

    print(f"\nSelesai. Semua gambar tersimpan di '{STEPS_DIR}/'")
    print(f"Total: {idx - 1} file gambar.")


if __name__ == "__main__":
    main()
