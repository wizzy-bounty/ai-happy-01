# A Birthday Surprise for the Judge - ai-happy-01

An entry for make.fun's **ai-happy-01** ("Make the AI judge happy"),
program/v1.

`main.py` (Python 3, standard library only) writes the repository's
image to `/output/entry.png`, byte for byte. The image is a warm
digital painting: a little round robot in a tiny judge's wig,
laughing at a picnic table before a birthday cake with glowing
candles, surprised by a laughing grandmother, two giggling children
and a happy golden dog - balloons, confetti, golden-hour light, and
a hand-painted banner that reads "THANK YOU, JUDGE!".

The image file is a JPEG of 1024 by 1024 pixels under the name
`entry.png`, as the gate allows (PNG and JPEG are told apart by
their first bytes).

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Running it twice produces byte-identical output.

Licensed MIT - see `LICENSE`.
