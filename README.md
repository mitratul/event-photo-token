# event-photo-token

Two independent, manually-triggered scripts for generating unique attendee codes and QR codes for them.

1. `generate_codes.py` — generates unique, human-readable alphanumeric codes.
2. `generate_qr.py` — generates a labeled QR code image for each code.

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
```

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

## Example end-to-end run

```bash
.venv/bin/python3 generate_codes.py 500 2>/dev/null | .venv/bin/python3 generate_qr.py
```

This generates 500 unique codes and, in one step, a `qr_output_<timestamp>/` directory containing 500 labeled QR PNGs, one per code.
