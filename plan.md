# Event Photo Token — Code Generator + QR Generator + Sheet Merger

## Context
This is a new, empty project directory. The goal is a small Python toolkit with independent, manually-triggered scripts:
1. Generate unique, human-readable alphanumeric codes to identify event attendees/photo-token holders.
2. Generate a QR code image for each such code, on demand (not auto-chained).
3. Merge those QR images into printable, letter-sized sheets (added later — see "Changes made after the initial plan").

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
- `generate_code(prefix: str = "") -> str`: build an 8-char code — `prefix` (0 or 1 char) fixed at the start, remaining `CODE_LENGTH - len(prefix)` chars from `secrets.choice(ALPHABET)`.
- `generate_unique_codes(count: int, prefix: str = "") -> list[str]`: loop calling `generate_code(prefix)`, add to a `set` until it holds `count` unique codes.
- `format_code(code: str) -> str`: insert `-` every `GROUP_SIZE` characters (e.g. `XJ7KQP3M` → `XJ7K-QP3M`; a series-prefixed code like `2ADC97XX` → `2ADC-97XX`).
- `main()`:
  - `argparse` with two optional positionals: `count` (int) and `series` (single "series character" prefixed onto every generated code, e.g. `generate_codes.py 100 2` → all codes start with `2`, like `2ADC-97XX`). If `count` is omitted, prompt interactively: `"How many codes do you need? "`, validate it's a positive integer (re-prompt or exit with error on bad input). `series` is optional — omitting it keeps the original fully-random 8-char behavior.
  - `series` is upper-cased and validated to be exactly one character present in `ALPHABET` (`parser.error(...)` otherwise, e.g. rejects `O`/`1`/`I`/`L`/`0` or multi-character input).
  - Generate codes via `generate_unique_codes(count, series or "")`, format each with dashes.
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
Follow-up requests changed `generate_qr.py` beyond the original "bare QR PNG" design above, and added a third module:

1. **Label the code under the QR, transparent background** — so each PNG is self-checkable without scanning, and prints cleanly on colored paper:
   - `qrcode.make(raw).convert("RGBA")` is color-keyed (white pixels → alpha 0) instead of kept as opaque white.
   - The label (original code, dashes intact) is drawn in opaque black beneath the QR on a fully transparent `RGBA` canvas, composited via `canvas.paste(qr_img, ..., qr_img)` so the QR's own alpha carries over.
2. **Monospace font, width-matched to the QR** — the label now renders in a real monospace font (Courier-New-style) sized so its rendered width equals the QR image's pixel width:
   - `find_monospace_font()` searches a short list of common install paths (Liberation Mono first, then DejaVu Sans Mono) and returns the first that exists; `liberation-mono-fonts` was installed on this machine via `sudo dnf install -y liberation-mono-fonts` (explicitly "a replacement for Microsoft Courier New"; not available as a pip package, so it needs to be present as a system font — Debian/Ubuntu equivalent path also included as a fallback candidate).
   - If no monospace font is found, `load_font()` falls back to `ImageFont.load_default(size=...)` and `main()` prints a one-time stderr warning — width-matching still works, just without the true monospace look.
   - `fit_font_to_width()` binary-searches font point size (4–400) for the largest size whose rendered label width is `<=` the QR's pixel width.
3. **`generate_qr.py` stdout/stderr swap, for piping into module 3** — per-file save-path lines moved to **stderr**; **stdout** now prints only the bare output directory name (`out_dir`, one line), so `generate_qr.py`'s stdout can be piped directly as the directory argument to `merge_qr_images.py`.
4. **New module: `merge_qr_images.py`** (module 3) — merges the QR images in a directory into letter-sized (8.5×11in @ 300 DPI), printable sheets:
   - Takes the directory as a positional CLI arg, **or reads one line from stdin** if omitted (`args.directory or sys.stdin.readline().strip()`) — this is what lets it sit at the end of the pipe: `generate_codes.py N | generate_qr.py | merge_qr_images.py`.
   - `load_qr_images()` globs `*.png` in that directory, sorted, excluding any pre-existing `merged_*.png` (so re-running on an already-merged directory doesn't re-merge its own output).
   - Each image is resized to a fixed target width (`TARGET_QR_WIDTH_IN = 1.7`in, aspect ratio preserved) — this yields a 3-column × 4-row grid (12 per page) within a letter page's 0.5in margins and 0.25in gutters at 300 DPI. (An initial 2.5in target only fit 2×3 = 6/page, since the code label makes each image notably taller than wide — sized down after confirming with the user.)
   - Images are chunked into pages of `columns * rows`; each page is a transparent `RGBA` canvas with the grid centered in the usable area.
   - Pages are saved as `merged_001.png`, `merged_002.png`, ... (zero-padded to at least 3 digits, or wider if there are ≥1000 pages) into a **sibling** output directory `<input_dir_name>_merged` (`directory.parent / f"{directory.name}_merged"`, created with `mkdir(parents=True, exist_ok=True)`) — not inside the input directory itself. E.g. input `qr_output_20260910_231336/` → output `qr_output_20260910_231336_merged/`. `exist_ok=True` means re-running the merge on the same input just overwrites the previous `merged_NNN.png` files.
   - Each saved page's path (`<input_dir_name>_merged/merged_NNN.png`) prints to stdout as it's written; a human-readable summary line goes to stderr.

## Manual chaining (by the user, not automatic)
```bash
python3 generate_codes.py 100 2>/dev/null | python3 generate_qr.py 2>/dev/null | python3 merge_qr_images.py
# or step by step
python3 generate_codes.py 100        # note filename printed on stderr
python3 generate_qr.py codes_20260910_153045.txt   # per-file paths on stderr, output dir on stdout
python3 merge_qr_images.py qr_output_20260910_153050   # writes to sibling qr_output_20260910_153050_merged/
```

## Verification
- `pip install -r requirements.txt` in a venv.
- Run `python3 generate_codes.py 20` — confirm 20 dash-grouped codes print to stdout, a `codes_*.txt` file is created with the same content, and its name is shown (on stderr/terminal).
- Confirm no code contains `0/O/1/I/L` and all codes in one run are unique (`sort -u` count matches).
- Run `python3 generate_codes.py 500 2>/dev/null | python3 generate_qr.py` — confirm a `qr_output_*/` directory is created containing one `.png` per code, filenames matching the dashed codes, and each QR decodes back to the dash-free code (spot check by scanning one).
- Run `python3 generate_qr.py codes_20260910_153045.txt` separately to confirm file-input mode also works.
- Post-label changes: open a saved PNG and confirm it's `RGBA` with alpha `0` on background pixels and `255` on QR modules/text (`PIL.Image.open(path).getpixel(...)`), and that the label's opaque-pixel x-range spans essentially the same width as the QR (checked to within a few px, since `fit_font_to_width` only guarantees `<=` target width).
- Module 3: run `generate_codes.py 30 2>/dev/null | generate_qr.py 2>/dev/null | merge_qr_images.py`, confirm it prints `merged_NNN.png` paths for `ceil(30/12) = 3` pages in a **sibling** `qr_output_*_merged/` directory (not inside the `qr_output_*/` input directory, which should have zero `merged_*.png` files), each page is `2550x3300` px (letter @ 300 DPI) `RGBA` with transparent corners (`getpixel((0,0))[3] == 0`), and a visual check (composite onto white) shows a centered, non-overlapping 3×4 grid with legible labels. Re-running `merge_qr_images.py` on the same input directory should overwrite the existing `_merged` directory's files without erroring.
- Confirm `generate_qr.py`'s stdout is *only* the directory name (no file-path lines mixed in) so the 3-stage pipe works end-to-end without extra parsing.
- Series character: `generate_codes.py 5 2` — confirm all 5 codes start with `2` (e.g. `2ADC-97XX`); `generate_codes.py 5 a` — confirm lowercase is upper-cased to `A...`; `generate_codes.py 5 O` and `generate_codes.py 5 AB` — confirm both are rejected with a `parser.error`; `generate_codes.py 50 Z 2>/dev/null | sort -u | wc -l` — confirm all 50 remain unique.
