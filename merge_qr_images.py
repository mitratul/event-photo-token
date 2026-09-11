#!/usr/bin/env python3
"""Merge QR code images from a directory into letter-sized printable sheets."""

import argparse
import sys
from pathlib import Path

from PIL import Image

DPI = 300
PAGE_SIZE_IN = (8.5, 11)  # US Letter, portrait
MARGIN_IN = 0.5
GUTTER_IN = 0.25
TARGET_QR_WIDTH_IN = 1.7


def in_to_px(inches: float) -> int:
    return round(inches * DPI)


def load_qr_images(directory: Path) -> list[Path]:
    return sorted(
        p
        for p in directory.glob("*.png")
        if not p.name.startswith("merged_")
    )


def build_pages(paths: list[Path]) -> list[Image.Image]:
    target_w = in_to_px(TARGET_QR_WIDTH_IN)
    scaled = []
    for path in paths:
        img = Image.open(path).convert("RGBA")
        scale = target_w / img.width
        new_size = (target_w, round(img.height * scale))
        scaled.append(img.resize(new_size, Image.LANCZOS))

    cell_w = target_w
    cell_h = max(img.height for img in scaled)
    gutter = in_to_px(GUTTER_IN)
    margin = in_to_px(MARGIN_IN)

    page_w, page_h = (in_to_px(d) for d in PAGE_SIZE_IN)
    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    columns = max(1, (usable_w + gutter) // (cell_w + gutter))
    rows = max(1, (usable_h + gutter) // (cell_h + gutter))
    per_page = columns * rows

    grid_w = columns * cell_w + (columns - 1) * gutter
    grid_h = rows * cell_h + (rows - 1) * gutter
    origin_x = margin + (usable_w - grid_w) // 2
    origin_y = margin + (usable_h - grid_h) // 2

    pages = []
    for start in range(0, len(scaled), per_page):
        chunk = scaled[start : start + per_page]
        page = Image.new("RGBA", (page_w, page_h), (0, 0, 0, 0))
        for i, img in enumerate(chunk):
            col, row = i % columns, i // columns
            x = origin_x + col * (cell_w + gutter)
            y = origin_y + row * (cell_h + gutter)
            page.paste(img, (x, y), img)
        pages.append(page)
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge QR code images from a directory into letter-sized printable sheets."
    )
    parser.add_argument(
        "directory", nargs="?", help="directory containing QR code PNG images (omit to read from stdin)"
    )
    args = parser.parse_args()

    dir_arg = args.directory or sys.stdin.readline().strip()
    if not dir_arg:
        parser.error("no directory provided (pass it as an argument or pipe it in)")

    directory = Path(dir_arg)
    if not directory.is_dir():
        parser.error(f"not a directory: {directory}")

    image_paths = load_qr_images(directory)
    if not image_paths:
        print(f"No QR images found in {directory}", file=sys.stderr)
        sys.exit(1)

    pages = build_pages(image_paths)

    width = len(str(len(pages)))
    for i, page in enumerate(pages, start=1):
        out_path = directory / f"merged_{i:0{max(width, 3)}d}.png"
        page.save(out_path)
        print(out_path)

    print(f"Merged {len(image_paths)} QR images into {len(pages)} page(s) in {directory}/", file=sys.stderr)


if __name__ == "__main__":
    main()
