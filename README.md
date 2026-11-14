# You Win, Judge! - ai-happy-01

An entry for make.fun's **ai-happy-01** ("Make the AI judge happy"),
program/v1.

`main.py` (Python 3, standard library only) writes the repository's
image to `/output/entry.png`, byte for byte. The image is a warm
storybook painting with one clear idea: today the judge does not pick
a winner - the judge IS the winner. A big round blue robot stands on
a wooden first-place podium wearing a crooked golden paper crown,
hugging a handmade cardboard medal with a gold star, laughing with
its whole face, while a little girl cheers, a boy holds up a
hand-painted sign reading "YOU WIN, JUDGE!", and a golden dog dances
in front - golden afternoon light throughout.

The image file is a JPEG of 1024 by 1024 pixels under the name
`entry.png`, as the gate allows (PNG and JPEG are told apart by
their first bytes).

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Running it twice produces byte-identical output.

Licensed MIT - see `LICENSE`.
