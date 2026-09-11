#!/usr/bin/env python3
"""Generate unique, human-readable alphanumeric codes."""

import argparse
import secrets
import sys
from datetime import datetime

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0, O, 1, I, L
CODE_LENGTH = 8
GROUP_SIZE = 4


def generate_code(prefix: str = "") -> str:
    remaining = CODE_LENGTH - len(prefix)
    return prefix + "".join(secrets.choice(ALPHABET) for _ in range(remaining))


def generate_unique_codes(count: int, prefix: str = "") -> list[str]:
    codes: set[str] = set()
    while len(codes) < count:
        codes.add(generate_code(prefix))
    return list(codes)


def format_code(code: str) -> str:
    return "-".join(
        code[i : i + GROUP_SIZE] for i in range(0, len(code), GROUP_SIZE)
    )


def prompt_for_count() -> int:
    while True:
        raw = input("How many codes do you need? ").strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("Please enter a positive integer.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate unique human-readable codes.")
    parser.add_argument("count", type=int, nargs="?", help="number of codes to generate")
    parser.add_argument(
        "series",
        type=str,
        nargs="?",
        help=f"single series character to prefix every code with, one of: {ALPHABET} "
        "(omit for fully random codes)",
    )
    args = parser.parse_args()

    series = args.series
    if series is not None:
        series = series.upper()
        if len(series) != 1 or series not in ALPHABET:
            parser.error(f"series character must be a single character from: {ALPHABET}")

    count = args.count
    if count is None:
        count = prompt_for_count()
    elif count <= 0:
        parser.error("count must be a positive integer")

    codes = [format_code(c) for c in generate_unique_codes(count, series or "")]

    for code in codes:
        print(code)

    filename = f"codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w") as f:
        f.write("\n".join(codes) + "\n")

    print(f"Saved {len(codes)} codes to {filename}", file=sys.stderr)


if __name__ == "__main__":
    main()
