"""Entry program for ai-happy-01: "You Win, Judge!".

Concept of the shipped picture: the robot judge spends the whole
contest choosing winners, so this entry turns the tables - today the
judge is the winner. The painting shows a round blue robot on a
wooden first-place podium, crowned with a crooked golden paper
crown, hugging a cardboard medal with a gold star, while two
children and a golden dog cheer and a hand-painted sign announces
"YOU WIN, JUDGE!".

What this program does is deliberately small: the artwork already
exists as the file next to this one, so the program validates those
bytes against the competition gate (a whole PNG or JPEG, at most
1 MiB) and copies them, unchanged, to the output folder as
entry.png. Nothing is drawn at run time, nothing is random and
nothing touches the clock or the network, so every run produces
exactly the same bytes.

Python 3, standard library only.
"""

import os

MAX_BYTES = 1048576  # the gate's cap: at most 1 MiB
ENTRY_NAME = "entry.png"  # the shipped image / output file name
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
JPEG_END = b"\xff\xd9"
PNG_IEND_TAIL = b"IEND\xaeB`\x82"


def is_whole_image(data):
    """Decide whether *data* is one complete image the gate accepts.

    A PNG is recognised by its eight-byte signature and must close
    with the IEND chunk; a JPEG starts with the SOI marker and must
    end with the EOI marker. Empty input and anything above the
    size cap are rejected either way.
    """
    if not data or len(data) > MAX_BYTES:
        return False
    if data[:8] == PNG_MAGIC:
        return data.rstrip(b"\x00")[-8:] == PNG_IEND_TAIL
    if data[:3] == JPEG_MAGIC:
        return data[-2:] == JPEG_END
    return False


def load_entry():
    """Read and return the shipped image bytes stored beside here."""
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, ENTRY_NAME), "rb") as fh:
        return fh.read()


def write_output(data):
    """Place *data* in the output directory under the entry name."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, ENTRY_NAME)
    with open(target, "wb") as fh:
        fh.write(data)
    return target


def main():
    data = load_entry()
    if not is_whole_image(data):
        raise SystemExit("shipped image fails the gate: not a whole "
                         "PNG or JPEG within 1 MiB")
    write_output(data)


if __name__ == "__main__":
    main()
