#!/usr/bin/env python3
"""Generate a QR code image for each code in a file or from stdin."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import qrcode


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

    out_dir = Path(f"qr_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    out_dir.mkdir(parents=True)

    for code in codes:
        raw = code.replace("-", "")
        img = qrcode.make(raw)
        out_path = out_dir / f"{code}.png"
        img.save(out_path)
        print(out_path)

    print(f"Saved {len(codes)} QR codes to {out_dir}/", file=sys.stderr)


if __name__ == "__main__":
    main()
