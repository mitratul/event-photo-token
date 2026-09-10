# Event Photo Token — Code Generator + QR Generator

## Context
This is a new, empty project directory. The goal is a small Python toolkit with two independent, manually-triggered scripts:
1. Generate unique, human-readable alphanumeric codes to identify event attendees/photo-token holders.
2. Generate a QR code image for each such code, on demand (not auto-chained).

The codes must avoid visually-confusing characters (0/O, 1/I/L, etc.) since they'll likely be printed/read by humans, and must be unique enough that a mistyped code never collides with a different real user's code.

Clarified with user:
- Code length: **8 characters**, grouped in **two 4-character blocks** separated by `-` (e.g. `XJ7K-QP3M`).
- Count input: accept **both** a CLI argument and an interactive prompt fallback.
- QR generation: use the **`qrcode`** package with the `[pil]` extra (Pillow) — approved as a pip dependency.

## Alphabet
Uppercase letters and digits, excluding visually ambiguous characters `0, O, 1, I, L`:
```
ABCDEFGHJKMNPQRSTUVWXYZ23456789   (31 characters)
```
31^8 (~8.5×10^11) possible codes — with `secrets`-based random generation and a dedup set, collisions within any realistic batch are effectively impossible, and the space is far too large to brute-force guess from a typo.

## Files to create

### `requirements.txt`
```
qrcode[pil]
```

### `generate_codes.py` (module 1)
- Constants: `ALPHABET`, `CODE_LENGTH = 8`, `GROUP_SIZE = 4`.
- `generate_code() -> str`: build one random 8-char code using `secrets.choice(ALPHABET)` per character.
- `generate_unique_codes(count: int) -> list[str]`: loop calling `generate_code()`, add to a `set` until it holds `count` unique codes.
- `format_code(code: str) -> str`: insert `-` every `GROUP_SIZE` characters (e.g. `XJ7KQP3M` → `XJ7K-QP3M`).
- `main()`:
  - `argparse` with an optional positional `count` (int). If omitted, prompt interactively: `"How many codes do you need? "`, validate it's a positive integer (re-prompt or exit with error on bad input).
  - Generate codes, format each with dashes.
  - Print each formatted code to **stdout**, one per line (kept clean/pure so it can be piped straight into module 2).
  - Build filename `codes_<YYYYmmdd_HHMMSS>.txt`, write the same formatted codes (one per line) to it in the current directory.
  - Print a status line with the filename to **stderr** (e.g. `Saved 500 codes to codes_20260910_153045.txt`) — keeps stdout pipeable while still surfacing the filename to the user's terminal.

### `generate_qr.py` (module 2)
- `read_codes(source) -> list[str]`: reads lines from either a given file path (CLI arg) or stdin (pipe/interactive), strips whitespace, skips blank lines, returns the raw lines **as given** (dashes intact).
- `make_labeled_qr(raw, label) -> Image.Image`: builds the actual saved image (see "Changes made after the initial plan" below) — QR with a transparent background, labeled underneath with the dashed code in a width-fitted monospace font.
- `main()`:
  - `argparse` with an optional positional `file` path. If provided, read codes from that file; otherwise read from stdin (supports both piped input and manually pasted/typed input followed by EOF).
  - Create output directory `qr_output_<YYYYmmdd_HHMMSS>/` (timestamp = script execution time), via `pathlib.Path.mkdir(parents=True)`.
  - For each input line (the original code, dashes intact, used as the filename stem):
    - Strip `-` to get the raw code → this is the QR payload data.
    - Generate the labeled image via `make_labeled_qr(raw_code, code)`.
    - Save as `<output_dir>/<original_code_with_dashes>.png`.
  - Print each saved file path to stdout as it's written, and a final summary line with the output directory path.

## Changes made after the initial plan
Two follow-up requests changed `generate_qr.py` beyond the original "bare QR PNG" design above:

1. **Label the code under the QR, transparent background** — so each PNG is self-checkable without scanning, and prints cleanly on colored paper:
   - `qrcode.make(raw).convert("RGBA")` is color-keyed (white pixels → alpha 0) instead of kept as opaque white.
   - The label (original code, dashes intact) is drawn in opaque black beneath the QR on a fully transparent `RGBA` canvas, composited via `canvas.paste(qr_img, ..., qr_img)` so the QR's own alpha carries over.
2. **Monospace font, width-matched to the QR** — the label now renders in a real monospace font (Courier-New-style) sized so its rendered width equals the QR image's pixel width:
   - `find_monospace_font()` searches a short list of common install paths (Liberation Mono first, then DejaVu Sans Mono) and returns the first that exists; `liberation-mono-fonts` was installed on this machine via `sudo dnf install -y liberation-mono-fonts` (explicitly "a replacement for Microsoft Courier New"; not available as a pip package, so it needs to be present as a system font — Debian/Ubuntu equivalent path also included as a fallback candidate).
   - If no monospace font is found, `load_font()` falls back to `ImageFont.load_default(size=...)` and `main()` prints a one-time stderr warning — width-matching still works, just without the true monospace look.
   - `fit_font_to_width()` binary-searches font point size (4–400) for the largest size whose rendered label width is `<=` the QR's pixel width.

## Manual chaining (by the user, not automatic)
```bash
python3 generate_codes.py 100 2>/dev/null | python3 generate_qr.py
# or
python3 generate_codes.py 100        # note filename printed on stderr
python3 generate_qr.py codes_20260910_153045.txt
```

## Verification
- `pip install -r requirements.txt` in a venv.
- Run `python3 generate_codes.py 20` — confirm 20 dash-grouped codes print to stdout, a `codes_*.txt` file is created with the same content, and its name is shown (on stderr/terminal).
- Confirm no code contains `0/O/1/I/L` and all codes in one run are unique (`sort -u` count matches).
- Run `python3 generate_codes.py 500 2>/dev/null | python3 generate_qr.py` — confirm a `qr_output_*/` directory is created containing one `.png` per code, filenames matching the dashed codes, and each QR decodes back to the dash-free code (spot check by scanning one).
- Run `python3 generate_qr.py codes_20260910_153045.txt` separately to confirm file-input mode also works.
- Post-label changes: open a saved PNG and confirm it's `RGBA` with alpha `0` on background pixels and `255` on QR modules/text (`PIL.Image.open(path).getpixel(...)`), and that the label's opaque-pixel x-range spans essentially the same width as the QR (checked to within a few px, since `fit_font_to_width` only guarantees `<=` target width).
