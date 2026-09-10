#!/usr/bin/env python3
"""Generate a QR code image for each code in a file or from stdin."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

# Metric-compatible replacements for Courier New, checked in order of preference.
MONOSPACE_FONT_CANDIDATES = [
    "/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf",
    "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]


def find_monospace_font() -> str | None:
    for path in MONOSPACE_FONT_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default(size=size)


def fit_font_to_width(font_path: str | None, text: str, target_width: int) -> ImageFont.FreeTypeFont:
    lo, hi = 4, 400
    best = load_font(font_path, lo)
    while lo <= hi:
        mid = (lo + hi) // 2
        font = load_font(font_path, mid)
        width = font.getbbox(text)[2]
        if width <= target_width:
            best = font
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def make_labeled_qr(raw: str, label: str) -> Image.Image:
    qr_img = qrcode.make(raw).convert("RGBA")
    pixels = qr_img.load()
    for y in range(qr_img.height):
        for x in range(qr_img.width):
            if pixels[x, y][:3] == (255, 255, 255):
                pixels[x, y] = (255, 255, 255, 0)  # white -> transparent

    font_path = find_monospace_font()
    font = fit_font_to_width(font_path, label, qr_img.width)
    draw = ImageDraw.Draw(qr_img)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padding = 12

    canvas_w = max(qr_img.width, text_w)
    canvas = Image.new("RGBA", (canvas_w, qr_img.height + text_h + padding * 2), (0, 0, 0, 0))
    canvas.paste(qr_img, ((canvas_w - qr_img.width) // 2, 0), qr_img)
    draw = ImageDraw.Draw(canvas)
    x = (canvas_w - text_w) / 2 - bbox[0]
    y = qr_img.height + padding
    draw.text((x, y), label, fill=(0, 0, 0, 255), font=font)
    return canvas


def read_codes(path: str | None) -> list[str]:
    if path:
        with open(path) as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    return [line.strip() for line in lines if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate QR code images for a list of codes (file arg or stdin)."
    )
    parser.add_argument(
        "file", nargs="?", help="file containing one code per line (omit to read stdin)"
    )
    args = parser.parse_args()

    codes = read_codes(args.file)
    if not codes:
        print("No codes provided.", file=sys.stderr)
        sys.exit(1)

    if find_monospace_font() is None:
        print(
            "Warning: no monospace font found (tried liberation-mono-fonts / "
            "dejavu-sans-mono-fonts); falling back to Pillow's default font. "
            "Install one of those packages for a true Courier-style label.",
            file=sys.stderr,
        )

    out_dir = Path(f"qr_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    out_dir.mkdir(parents=True)

    for code in codes:
        raw = code.replace("-", "")
        img = make_labeled_qr(raw, code)
        out_path = out_dir / f"{code}.png"
        img.save(out_path)
        print(out_path)

    print(f"Saved {len(codes)} QR codes to {out_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
