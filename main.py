import os
import sys

from src.image_io import read_image, write_image, write_image_grayscale
from src.watermark import load_watermark_bits, embed_watermark, extract_watermark, DELTA
from src.jpeg_sim import simulate_jpeg_rgb
from src.color import image_rgb_to_ycbcr
from src.metrics import psnr, ber, nc
from src.utils import reshape_1d

OUTPUT_DIR = "output"
ASSETS_DIR = "assets"
QF_LIST = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]

BER_THRESHOLD = 0.25
NC_THRESHOLD  = 0.70

_HOST_CANDIDATES = ["host.jpg", "host.jpeg", "host.png", "host.bmp"]
_WM_CANDIDATES   = ["watermark.jpg", "watermark.jpeg", "watermark.png", "watermark.bmp"]


def find_asset(candidates, label):
    for name in candidates:
        path = os.path.join(ASSETS_DIR, name)
        if os.path.exists(path):
            return path
    tried = ", ".join(candidates)
    raise FileNotFoundError(
        f"{label} not found in '{ASSETS_DIR}/'. "
        f"Tried: {tried}. See README for input requirements."
    )


def ensure_assets():
    host_ok = any(os.path.exists(os.path.join(ASSETS_DIR, n)) for n in _HOST_CANDIDATES)
    wm_ok   = any(os.path.exists(os.path.join(ASSETS_DIR, n)) for n in _WM_CANDIDATES)
    if not host_ok and not wm_ok:
        print("Assets not found. Running generate_assets.py to create samples...")
        import generate_assets
        generate_assets.main()


def print_table(rows):
    print("┌─────┬────────┬───────┬───────┐")
    print("│ QF  │  PSNR  │  BER  │  NC   │")
    print("├─────┼────────┼───────┼───────┤")
    for qf, p, b, n in rows:
        p_str = f"{p:6.2f}" if p != float('inf') else "  inf "
        print(f"│ {qf:3d} │ {p_str} │ {b:.3f} │ {n:.3f} │")
    print("└─────┴────────┴───────┴───────┘")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ensure_assets()

    host_path = find_asset(_HOST_CANDIDATES, "Host image")
    wm_path   = find_asset(_WM_CANDIDATES,   "Watermark image")
    print(f"Host:      {host_path}")
    print(f"Watermark: {wm_path}")

    host_pixels, host_w, host_h = read_image(host_path)
    print(f"Host size: {host_w}×{host_h} px")

    if host_w < 8 or host_h < 8:
        raise ValueError("Host image must be at least 8×8 pixels.")

    wm_bits, wm_w, wm_h = load_watermark_bits(wm_path)
    wm_length = wm_w * wm_h
    print(f"Watermark: {wm_w}×{wm_h} = {wm_length} bits")

    # Embed
    print(f"\nEmbedding watermark (delta={DELTA})...")
    watermarked = embed_watermark(host_pixels, host_w, host_h, wm_bits)
    out_wm = os.path.join(OUTPUT_DIR, "watermarked.bmp")
    write_image(out_wm, watermarked, host_w, host_h)

    # PSNR host vs watermarked (Y channel)
    host_y, _, _  = image_rgb_to_ycbcr(host_pixels)
    wm_y,   _, _  = image_rgb_to_ycbcr(watermarked)

    # image_rgb_to_ycbcr returns full-size channels already
    embed_psnr = psnr(host_y, wm_y, host_h, host_w)
    print(f"Embed PSNR (host vs watermarked): {embed_psnr:.2f} dB")

    # Verify BER=0 without compression
    extracted_clean = extract_watermark(watermarked, host_w, host_h, wm_length)
    clean_ber = ber(wm_bits, extracted_clean)
    clean_nc  = nc(wm_bits, extracted_clean)
    print(f"Clean extraction — BER={clean_ber:.3f}, NC={clean_nc:.3f}")
    if clean_ber != 0.0:
        print("WARNING: BER is not 0 for clean extraction — check delta value.")

    # Loop over QFs
    print("\nRunning JPEG simulation...\n")
    table_rows = []
    critical_qf = None

    for qf in QF_LIST:
        print(f"  QF={qf:3d} ...", end=" ", flush=True)

        compressed = simulate_jpeg_rgb(watermarked, host_w, host_h, qf)
        comp_path = os.path.join(OUTPUT_DIR, f"compressed_QF{qf:03d}.bmp")
        write_image(comp_path, compressed, host_w, host_h)

        extracted = extract_watermark(compressed, host_w, host_h, wm_length)
        ext_ber = ber(wm_bits, extracted)
        ext_nc  = nc(wm_bits, extracted)

        comp_y, _, _ = image_rgb_to_ycbcr(compressed)
        comp_psnr = psnr(wm_y, comp_y, host_h, host_w)

        ext_matrix = reshape_1d([float(b * 255) for b in extracted], wm_h, wm_w)
        ext_path = os.path.join(OUTPUT_DIR, f"extracted_QF{qf:03d}.bmp")
        write_image_grayscale(ext_path, ext_matrix, wm_w, wm_h)

        table_rows.append((qf, comp_psnr, ext_ber, ext_nc))
        print(f"PSNR={comp_psnr:.2f} dB, BER={ext_ber:.3f}, NC={ext_nc:.3f}")

        if critical_qf is None and (ext_ber > BER_THRESHOLD or ext_nc < NC_THRESHOLD):
            critical_qf = qf

    print()
    print_table(table_rows)

    if critical_qf is not None:
        print(f"\nKesimpulan: QF kritis = {critical_qf}")
        print(f"  Watermark mulai gagal diekstrak pada QF={critical_qf}")
        print(f"  (BER > {BER_THRESHOLD} atau NC < {NC_THRESHOLD})")
    else:
        print("\nKesimpulan: Watermark bertahan di semua QF yang diuji.")

    results_path = os.path.join(OUTPUT_DIR, "results.txt")
    with open(results_path, 'w') as f:
        f.write("DCT Watermarking Evaluation\n")
        f.write(f"Host: {host_w}x{host_h}  Watermark: {wm_w}x{wm_h}  Delta: {DELTA}\n")
        f.write(f"Embed PSNR: {embed_psnr:.2f} dB\n")
        f.write(f"Clean extraction: BER={clean_ber:.3f}, NC={clean_nc:.3f}\n\n")
        f.write("QF    PSNR      BER     NC\n")
        for qf, p, b, n in table_rows:
            p_str = f"{p:.2f}" if p != float('inf') else "inf"
            f.write(f"{qf:4d}  {p_str:8}  {b:.3f}  {n:.3f}\n")
        if critical_qf is not None:
            f.write(f"\nKritical QF: {critical_qf}\n")
        else:
            f.write("\nWatermark bertahan di semua QF.\n")
    print(f"\nHasil disimpan ke {results_path}")


if __name__ == "__main__":
    main()
