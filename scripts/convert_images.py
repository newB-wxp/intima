#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intima Wellness — WebP Image Converter
Scans static/images/ for .jpg/.png/.jpeg files and generates .webp copies.
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "static", "images")


def convert_to_webp():
    """Main conversion routine. Returns list of conversion report dicts."""
    try:
        from PIL import Image
    except ImportError:
        print("[SKIP] Pillow not installed. Install with: pip install Pillow")
        return []

    if not os.path.isdir(IMAGES_DIR):
        print(f"[SKIP] Images directory not found: {IMAGES_DIR}")
        return []

    supported_exts = {".jpg", ".jpeg", ".png"}
    reports = []

    for root, dirs, files in os.walk(IMAGES_DIR):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in supported_exts:
                continue

            src_path = os.path.join(root, filename)
            webp_name = os.path.splitext(filename)[0] + ".webp"
            dst_path = os.path.join(root, webp_name)

            # Skip if .webp already exists and is newer than source
            if os.path.exists(dst_path):
                if os.path.getmtime(dst_path) >= os.path.getmtime(src_path):
                    continue

            try:
                src_size = os.path.getsize(src_path)

                with Image.open(src_path) as img:
                    # Convert RGBA to RGB if needed (webp handles both, but some modes cause issues)
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")

                    img.save(dst_path, "WEBP", quality=80, method=6)

                dst_size = os.path.getsize(dst_path)
                ratio = (1 - dst_size / src_size) * 100 if src_size > 0 else 0

                report = {
                    "source": os.path.relpath(src_path, PROJECT_ROOT),
                    "webp": os.path.relpath(dst_path, PROJECT_ROOT),
                    "original_size": src_size,
                    "webp_size": dst_size,
                    "compression_ratio": round(ratio, 1),
                }
                reports.append(report)

                print(f"  [OK] {report['source']} → {report['webp']} "
                      f"({_fmt_size(src_size)} → {_fmt_size(dst_size)}, -{ratio:.1f}%)")

            except Exception as e:
                print(f"  [FAIL] {os.path.relpath(src_path, PROJECT_ROOT)}: {e}")

    return reports


def _fmt_size(size_bytes):
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_summary(reports):
    """Print conversion summary report."""
    if not reports:
        print("\nNo images converted.")
        return

    total_src = sum(r["original_size"] for r in reports)
    total_dst = sum(r["webp_size"] for r in reports)
    total_ratio = (1 - total_dst / total_src) * 100 if total_src > 0 else 0

    print(f"\n{'='*60}")
    print(f"WebP Conversion Report")
    print(f"{'='*60}")
    print(f"  Total files converted : {len(reports)}")
    print(f"  Original total size   : {_fmt_size(total_src)}")
    print(f"  WebP total size       : {_fmt_size(total_dst)}")
    print(f"  Total space saved     : {_fmt_size(total_src - total_dst)} (-{total_ratio:.1f}%)")
    print(f"{'='*60}")


def main():
    print(f"Scanning: {IMAGES_DIR}")
    start = time.time()
    reports = convert_to_webp()
    elapsed = time.time() - start
    print_summary(reports)
    print(f"\nCompleted in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
