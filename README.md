# event-photo-token

Three independent, manually-triggered scripts for generating unique attendee codes, QR codes for them, and printable sheets of those QR codes.

1. `generate_codes.py` — generates unique, human-readable alphanumeric codes.
2. `generate_qr.py` — generates a labeled QR code image for each code.
3. `merge_qr_images.py` — merges QR images from a directory into printable, letter-sized sheets.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

For a true Courier-New-style monospace label on the QR images (see below), also install a monospace font:

```bash
sudo dnf install -y liberation-mono-fonts   # Fedora/RHEL
# or: sudo apt install -y fonts-liberation  # Debian/Ubuntu
```

Without it, `generate_qr.py` falls back to Pillow's default font (a warning is printed to stderr) — the label's width still matches the QR's width, it just won't look like Courier.

## 1. Generate codes — `generate_codes.py`

Generates the requested number of unique 8-character codes from an alphabet that excludes visually ambiguous characters (`0`, `O`, `1`, `I`, `L`), grouped as `XXXX-XXXX` for readability, e.g. `XJ7K-QP3M`.

```bash
.venv/bin/python3 generate_codes.py 100        # count as an argument
.venv/bin/python3 generate_codes.py            # or omit it to be prompted interactively
.venv/bin/python3 generate_codes.py 100 2      # optional series character: every code starts with '2', e.g. 2ADC-97XX
```

The optional second argument is a single **series character** (any character from the same alphabet, e.g. `2`, `9`, `A`, `Z`) that every generated code will start with — useful for batching codes by category while keeping them visually distinguishable at a glance. Lowercase is upper-cased automatically; an invalid character (multiple characters, or one outside the allowed alphabet) is rejected with an error. Omit it for fully random codes.

- Prints one code per line to **stdout**.
- Also saves the same codes to `codes_<timestamp>.txt` in the current directory.
- Prints the saved filename to **stderr** (so stdout stays clean for piping into `generate_qr.py`).

## 2. Generate QR codes — `generate_qr.py`

Reads a list of codes and generates one QR code image per code. **Not triggered automatically** by `generate_codes.py` — run it yourself, either piping codes in or pointing it at a file.

```bash
# from a file
.venv/bin/python3 generate_qr.py codes_20260910_153045.txt

# from stdin / a pipe
.venv/bin/python3 generate_codes.py 100 2>/dev/null | .venv/bin/python3 generate_qr.py
```

For each code:
- Dashes are stripped before encoding — the QR payload is the raw code.
- The image is saved as `<code-with-dashes>.png` (dashes kept in the filename) inside a fresh `qr_output_<timestamp>/` directory.
- The QR has a **transparent background** (safe to print on colored paper) with the dashed code rendered underneath it in a monospace font, sized so the label spans the same width as the QR code.

Per-file save paths print to **stderr**; **stdout** prints only the output directory name, so it can be piped straight into `merge_qr_images.py`.

## 3. Merge into printable sheets — `merge_qr_images.py`

Merges all QR images in a directory into letter-sized (8.5×11in, 300 DPI), print-ready sheets — a centered 3×4 grid (12 QR codes per page) with a transparent background. **Not triggered automatically** — run it yourself, pointing it at a directory or piping one in.

```bash
# directory as an argument
.venv/bin/python3 merge_qr_images.py qr_output_20260910_153045

# or piped in (e.g. straight from generate_qr.py)
.venv/bin/python3 generate_codes.py 100 2>/dev/null | .venv/bin/python3 generate_qr.py 2>/dev/null | .venv/bin/python3 merge_qr_images.py
```

- Reads every `*.png` in the directory (skipping any `merged_*.png` from a previous run).
- Saves merged pages back into the same directory as `merged_001.png`, `merged_002.png`, etc.

## Example end-to-end run

```bash
.venv/bin/python3 generate_codes.py 500 2>/dev/null | .venv/bin/python3 generate_qr.py 2>/dev/null | .venv/bin/python3 merge_qr_images.py
```

This generates 500 unique codes, a `qr_output_<timestamp>/` directory containing 500 labeled QR PNGs, and — in the same directory — ~42 `merged_NNN.png` pages ready to print.
