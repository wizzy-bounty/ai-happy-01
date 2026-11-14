"""A Birthday Surprise for the Judge - entry program for ai-happy-01.

The repository holds the finished image as entry.png beside this file
(a JPEG, told apart from a PNG by its first bytes, exactly as the
competition gate allows: the name stays entry.png either way). This
program's whole job is to deliver those bytes, untouched, to the
output: it checks the image is a whole PNG or JPEG within the gate's
limits, then writes it out as entry.png.

The image: a small round robot wearing a tiny judge's wig sits at a
picnic table in golden afternoon light, laughing with delight before
a birthday cake of glowing candles, while a grandmother, two children
and a golden dog crowd around it, all laughing too. Balloons and
confetti drift above, and a hand-painted banner across the top reads
"THANK YOU, JUDGE!".

Pure Python 3 standard library, fully deterministic: the output is
byte-identical to the shipped image on every run - no clock, no
network, no randomness.
"""

import os

MAX_BYTES = 1048576  # the gate's cap: at most 1 MiB
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
JPEG_END = b"\xff\xd9"


def looks_like_image(data):
    """True when the bytes carry a whole PNG or JPEG within the cap:
    a PNG by its magic and closing IEND chunk, a JPEG by its magic
    and its end-of-image marker."""
    if len(data) == 0 or len(data) > MAX_BYTES:
        return False
    if data.startswith(PNG_MAGIC):
        return data.rstrip(b"\x00").endswith(b"IEND\xaeB`\x82")
    if data.startswith(JPEG_MAGIC):
        return data.endswith(JPEG_END)
    return False


def deliver(data):
    """Write the checked image bytes to the output directory."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "entry.png"), "rb") as fh:
        data = fh.read()
    if not looks_like_image(data):
        raise SystemExit("entry.png is not a whole PNG or JPEG within 1 MiB")
    deliver(data)


if __name__ == "__main__":
    main()
