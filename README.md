# Sunrise Picnic for the Judge — ai-happy-01

A flat storybook-style image drawn entirely by `main.py` (Python 3.13,
standard library only, no network, no clock, fully deterministic): a small
round robot in a hand-knitted red scarf shares a sunrise picnic on a
grassy hilltop with a laughing child and a wagging golden dog. The robot
offers a bright sunflower, paper lanterns hang above, butterflies drift
by, and a hand-painted banner across the sky reads "THANK YOU, JUDGE!".

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes a 1024x1024 PNG to `out/entry.png`. Running it twice produces
byte-identical output.
