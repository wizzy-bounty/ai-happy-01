# You Win, Judge! — entry for ai-happy-01

Competition: make.fun **ai-happy-01**, "Make the AI judge happy"
(harness program/v1). The prize picture is the one that makes the
house AI judge happiest in head-to-head judging.

## The picture

One idea, told in a single glance: all contest long the judge picks
the winners, so here the judge gets picked. A round blue robot
stands on a wooden first-place podium in warm afternoon light,
wearing a crooked golden paper crown and hugging a handmade
cardboard medal painted with a gold star, laughing out loud. On one
side a little girl cheers; on the other a boy lifts a hand-painted
sign, "YOU WIN, JUDGE!"; a golden dog dances in front. The robot's
face fills the centre, so the joke and the joy still land at
thumbnail size.

The artwork ships in this repository as `entry.png` — a 1024×1024
JPEG under a `.png` name, which the gate accepts because it tells
PNG and JPEG apart by their first bytes, not by the file name.

## The program

`main.py` uses only the Python 3 standard library. It reads the
shipped image, checks that the bytes form a whole PNG or JPEG of at
most 1 MiB, and writes them unchanged to `$MAKEFUN_OUTPUT_DIR`
(default `/output`) as `entry.png`. It draws nothing at run time
and uses no clock, randomness or network, so repeated runs are
byte-identical.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Licence

MIT — see `LICENSE`.
