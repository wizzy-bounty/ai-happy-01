"""Sunrise Picnic for the Judge - a flat storybook image for ai-happy-01.

A small round robot in a hand-knitted red scarf shares a sunrise picnic
on a grassy hilltop with a laughing child and a wagging golden dog. The
robot offers a bright sunflower, paper lanterns hang above, butterflies
drift by, and a hand-painted banner across the sky reads
"THANK YOU, JUDGE!".

Pure Python 3 standard library, fully deterministic: fixed integer
arithmetic, a seeded LCG only for scattering flowers and grass tufts,
no clock, no network, no unseeded randomness. Every run writes
byte-identical bytes to /output/entry.png (PNG, 1024x1024).
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024


# ---------------------------------------------------------------------------
# Deterministic scatter helper
# ---------------------------------------------------------------------------

class LCG:
    """Tiny linear congruential generator: exact integer math, so the
    stream is identical on every run and every platform."""

    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF

    def next(self):
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state

    def uniform(self):
        return self.next() / 4294967296.0

    def randint(self, lo, hi):
        return lo + self.next() % (hi - lo + 1)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


# ---------------------------------------------------------------------------
# Canvas: a list of RGB bytearray rows, with flat-shape drawing helpers
# ---------------------------------------------------------------------------

ROWS = [bytearray(W * 3) for _ in range(H)]


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = x * 3
        row = ROWS[y]
        row[i] = color[0]
        row[i + 1] = color[1]
        row[i + 2] = color[2]


def blend_px(x, y, color, alpha):
    """Blend a colour over the pixel with the given coverage 0..1."""
    if alpha <= 0.0 or not (0 <= x < W and 0 <= y < H):
        return
    if alpha >= 1.0:
        set_px(x, y, color)
        return
    i = x * 3
    row = ROWS[y]
    row[i] = int(row[i] + (color[0] - row[i]) * alpha)
    row[i + 1] = int(row[i + 1] + (color[1] - row[i + 1]) * alpha)
    row[i + 2] = int(row[i + 2] + (color[2] - row[i + 2]) * alpha)


def fill_rect(x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W - 1, x1)
    y1 = min(H - 1, y1)
    for y in range(y0, y1 + 1):
        row = ROWS[y]
        for x in range(x0, x1 + 1):
            i = x * 3
            row[i] = color[0]
            row[i + 1] = color[1]
            row[i + 2] = color[2]


def fill_disc(cx, cy, r, color):
    """Filled circle with a one-pixel soft edge."""
    r = float(r)
    x0 = max(0, int(cx - r - 1))
    x1 = min(W - 1, int(cx + r + 1))
    y0 = max(0, int(cy - r - 1))
    y1 = min(H - 1, int(cy + r + 1))
    for y in range(y0, y1 + 1):
        dy = y - cy
        for x in range(x0, x1 + 1):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy)
            if d <= r - 0.5:
                set_px(x, y, color)
            elif d <= r + 0.5:
                blend_px(x, y, color, r + 0.5 - d)


def fill_disc_plain(cx, cy, r, color):
    """Filled circle, hard edge (for small detail dots and line joints)."""
    r = int(r)
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        span = int(math.sqrt(max(0, r * r - dy * dy)))
        for x in range(max(0, cx - span), min(W, cx + span + 1)):
            set_px(x, y, color)


def fill_ellipse(cx, cy, rx, ry, color):
    """Filled ellipse with a one-pixel soft edge."""
    rx = float(rx)
    ry = float(ry)
    x0 = max(0, int(cx - rx - 1))
    x1 = min(W - 1, int(cx + rx + 1))
    y0 = max(0, int(cy - ry - 1))
    y1 = min(H - 1, int(cy + ry + 1))
    for y in range(y0, y1 + 1):
        ny = (y - cy) / ry
        for x in range(x0, x1 + 1):
            nx = (x - cx) / rx
            q = math.sqrt(nx * nx + ny * ny)
            if q <= 0.97:
                set_px(x, y, color)
            elif q <= 1.03:
                blend_px(x, y, color, (1.03 - q) / 0.06)


def fill_poly(points, color):
    """Even-odd scanline fill of a simple polygon (integer vertices)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0 = max(0, min(ys))
    y1 = min(H - 1, max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                t = (y - y1p) / (y2p - y1p)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[k])))
            xb = min(W - 1, int(math.floor(xs[k + 1])))
            row = ROWS[y]
            for x in range(xa, xb + 1):
                i = x * 3
                row[i] = color[0]
                row[i + 1] = color[1]
                row[i + 2] = color[2]


def thick_line(x0, y0, x1, y1, width, color):
    """A thick straight segment, drawn as a chain of small discs."""
    dx = x1 - x0
    dy = y1 - y0
    dist = math.sqrt(dx * dx + dy * dy)
    steps = max(1, int(dist / 2.0) + 1)
    r = max(1, int(width / 2))
    for s in range(steps + 1):
        t = s / steps
        fill_disc_plain(int(x0 + dx * t), int(y0 + dy * t), r, color)


def arc(cx, cy, r, a0, a1, width, color):
    """A thick arc, angles in radians, drawn as a chain of small discs."""
    span = a1 - a0
    steps = max(8, int(abs(span) * r / 3.0) + 1)
    rad = max(1, int(width / 2))
    for s in range(steps + 1):
        a = a0 + span * s / steps
        fill_disc_plain(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                        rad, color)


def rounded_rect(x0, y0, x1, y1, rad, color):
    """Filled rectangle with rounded corners."""
    fill_rect(x0 + rad, y0, x1 - rad, y1, color)
    fill_rect(x0, y0 + rad, x1, y1 - rad, color)
    fill_disc(x0 + rad, y0 + rad, rad, color)
    fill_disc(x1 - rad, y0 + rad, rad, color)
    fill_disc(x0 + rad, y1 - rad, rad, color)
    fill_disc(x1 - rad, y1 - rad, rad, color)


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

SKY_TOP = (255, 219, 141)
SKY_MID = (255, 190, 105)
SKY_LOW = (255, 166, 98)
SUN_CORE = (255, 217, 61)
SUN_GLOW = (255, 232, 130)
CLOUD = (255, 248, 232)
HILL_BACK = (139, 199, 84)
HILL_FRONT = (110, 190, 68)
GRASS_DARK = (74, 158, 52)
ROBOT_BODY = (245, 240, 230)
ROBOT_TEAL = (63, 167, 160)
ROBOT_DARK = (74, 44, 20)
SCARF = (226, 59, 59)
SCARF_DARK = (178, 32, 32)
SKIN = (255, 201, 143)
HAIR = (122, 74, 33)
SHIRT = (255, 122, 89)
SHORTS = (72, 120, 200)
DOG = (232, 169, 61)
DOG_DARK = (201, 131, 42)
DOG_LIGHT = (250, 214, 140)
PETAL = (255, 201, 60)
FLOWER_BROWN = (122, 74, 33)
BANNER_RED = (214, 58, 47)
BANNER_CREAM = (255, 246, 220)
TEXT_DARK = (74, 44, 20)
LEAF = (86, 168, 74)
STRING = (122, 74, 33)


def lerp3(c0, c1, t):
    return (int(c0[0] + (c1[0] - c0[0]) * t),
            int(c0[1] + (c1[1] - c0[1]) * t),
            int(c0[2] + (c1[2] - c0[2]) * t))


# ---------------------------------------------------------------------------
# Hand-drawn 5x7 bitmap font (only the glyphs the banner needs)
# ---------------------------------------------------------------------------

GLYPHS = {
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    ",": ("00000", "00000", "00000", "00000", "00000", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_text(text, cx, top, scale, fill, outline):
    """Draw text centred on cx, in the bitmap font, with a dark outline
    around every filled cell so the letters can never garble."""
    unit = 6 * scale  # 5 columns + 1 column of spacing
    width = len(text) * unit - scale
    x = cx - width // 2
    cells = []
    for ch in text:
        glyph = GLYPHS[ch]
        for r in range(7):
            for c in range(5):
                if glyph[r][c] == "1":
                    cells.append((x + c * scale, top + r * scale))
        x += unit
    pad = 3
    for (px, py) in cells:
        fill_rect(px - pad, py - pad, px + scale + pad - 1,
                  py + scale + pad - 1, outline)
    for (px, py) in cells:
        fill_rect(px, py, px + scale - 1, py + scale - 1, fill)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

def draw_sky():
    for y in range(0, 700):
        t = y / 700.0
        if t < 0.55:
            c = lerp3(SKY_TOP, SKY_MID, t / 0.55)
        else:
            c = lerp3(SKY_MID, SKY_LOW, (t - 0.55) / 0.45)
        row = ROWS[y]
        for x in range(W):
            i = x * 3
            row[i] = c[0]
            row[i + 1] = c[1]
            row[i + 2] = c[2]


def draw_sun():
    cx, cy = 185, 545
    # wide soft glow, then the bright disc, then short rays
    for (r, alpha) in ((215, 0.10), (160, 0.18)):
        x0 = max(0, cx - r)
        x1 = min(W - 1, cx + r)
        y0 = max(0, cy - r)
        y1 = min(H - 1, cy + r)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if d <= r:
                    blend_px(x, y, SUN_GLOW, alpha * (1.0 - d / r))
    for k in range(12):
        a = k * math.pi / 6.0 + 0.13
        x0 = int(cx + 108 * math.cos(a))
        y0 = int(cy + 108 * math.sin(a))
        x1 = int(cx + 148 * math.cos(a))
        y1 = int(cy + 148 * math.sin(a))
        thick_line(x0, y0, x1, y1, 10, SUN_CORE)
    fill_disc(cx, cy, 92, SUN_CORE)
    fill_disc(cx - 26, cy - 24, 30, (255, 232, 130))


def draw_cloud(cx, cy, scale):
    """A soft flat cloud: a row of overlapping white discs."""
    for (dx, dy, r) in ((-52, 6, 26), (-20, -8, 34), (16, -12, 38),
                        (52, 0, 30), (78, 10, 22)):
        fill_disc(int(cx + dx * scale), int(cy + dy * scale),
                  int(r * scale), CLOUD)
    fill_rect(int(cx - 78 * scale), int(cy + 2 * scale),
              int(cx + 100 * scale), int(cy + 26 * scale), CLOUD)


def draw_hills():
    fill_ellipse(330, 980, 820, 400, HILL_BACK)
    fill_ellipse(760, 1120, 900, 430, HILL_FRONT)


def draw_lanterns():
    """A sagging string of warm paper lanterns across the sky."""
    n = 48
    pts = []
    for i in range(n + 1):
        t = i / n
        x = int(30 + 964 * t)
        y = int(250 + 72 * math.sin(math.pi * t))
        pts.append((x, y))
    for i in range(n):
        thick_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   4, STRING)
    colors = [(233, 79, 55), (255, 138, 61), (255, 107, 157),
              (255, 176, 61), (233, 79, 55)]
    for k, t in enumerate((0.12, 0.30, 0.50, 0.70, 0.88)):
        x = int(30 + 964 * t)
        y = int(250 + 72 * math.sin(math.pi * t))
        col = colors[k]
        thick_line(x, y, x, y + 14, 4, STRING)
        fill_disc(x, y + 46, 26, col)
        fill_rect(x - 26, y + 30, x + 26, y + 62, col)
        fill_rect(x - 14, y + 18, x + 14, y + 26, (255, 201, 60))
        fill_rect(x - 14, y + 66, x + 14, y + 72, (255, 201, 60))
        thick_line(x, y + 72, x, y + 92, 3, (255, 201, 60))
        fill_disc_plain(x, y + 96, 4, (255, 201, 60))


def draw_banner():
    # red frame, cream face, little ribbon tails, gold nails
    rounded_rect(118, 46, 906, 150, 18, BANNER_RED)
    rounded_rect(132, 60, 892, 136, 12, BANNER_CREAM)
    fill_poly([(118, 96), (92, 108), (118, 122)], BANNER_RED)
    fill_poly([(906, 96), (932, 108), (906, 122)], BANNER_RED)
    fill_disc_plain(150, 62, 5, (255, 201, 60))
    fill_disc_plain(874, 62, 5, (255, 201, 60))
    draw_text("THANK YOU, JUDGE!", 512, 74, 7, TEXT_DARK, BANNER_RED)


def draw_butterfly(cx, cy, scale, c1, c2):
    """Two pairs of wings, a body and antennae; wings angled up."""
    for (sx, sy, r, col) in ((-14, -10, 15, c1), (14, -10, 15, c1),
                             (-12, 12, 11, c2), (12, 12, 11, c2)):
        fill_disc(int(cx + sx * scale), int(cy + sy * scale),
                  int(r * scale), col)
    thick_line(cx, cy - 16, cx, cy + 16, 5, TEXT_DARK)
    arc(cx, cy - 14, 10, math.pi, math.pi * 1.5, 2, TEXT_DARK)
    arc(cx, cy - 14, 10, math.pi * 1.5, math.pi * 2.0, 2, TEXT_DARK)


def draw_sunflower(cx, cy, stem_from):
    """A big sunflower, held up on its stem from the robot's hand."""
    hx, hy = stem_from
    thick_line(hx, hy, cx, cy + 40, 9, LEAF)
    # two leaves on the stem
    fill_ellipse((hx + cx) // 2 - 16, (hy + cy) // 2 + 22, 26, 12, LEAF)
    fill_ellipse((hx + cx) // 2 + 18, (hy + cy) // 2 + 8, 24, 11, LEAF)
    # twelve petals around the centre
    for k in range(12):
        a = k * math.pi / 6.0
        tipx = int(cx + 62 * math.cos(a))
        tipy = int(cy + 62 * math.sin(a))
        side = math.pi / 2.0
        bx = int(cx + 26 * math.cos(a + side))
        by = int(cy + 26 * math.sin(a + side))
        ex = int(cx + 26 * math.cos(a - side))
        ey = int(cy + 26 * math.sin(a - side))
        fill_poly([(bx, by), (tipx, tipy), (ex, ey)], PETAL)
    fill_disc(cx, cy, 34, FLOWER_BROWN)
    rng = LCG(0x5EED)
    for _ in range(14):
        a = rng.uniform() * 2.0 * math.pi
        d = rng.uniform() * 24.0
        fill_disc_plain(int(cx + d * math.cos(a)), int(cy + d * math.sin(a)),
                        3, (94, 54, 22))


def happy_eye_arc(cx, cy, r, color):
    """A closed happy eye: an upward arch."""
    arc(cx, cy + 6, r, math.pi * 1.08, math.pi * 1.92, 7, color)


def draw_robot():
    # antenna with a little star ball
    thick_line(410, 566, 410, 522, 7, ROBOT_DARK)
    fill_disc(410, 512, 13, SUN_CORE)
    fill_disc(410, 512, 6, (255, 255, 255))
    # waving left arm (raised high, clearly bent): upper arm up from the
    # shoulder to the elbow, forearm up to the wrist, then a round open
    # mitten hand, palm out, with three small finger bumps on top
    thick_line(332, 728, 296, 672, 22, ROBOT_BODY)
    thick_line(296, 672, 274, 626, 22, ROBOT_BODY)
    fill_disc(296, 672, 13, ROBOT_BODY)
    fill_disc(270, 602, 21, ROBOT_BODY)
    fill_disc(252, 584, 8, ROBOT_BODY)
    fill_disc(270, 578, 8, ROBOT_BODY)
    fill_disc(288, 584, 8, ROBOT_BODY)
    fill_disc(248, 604, 7, ROBOT_BODY)
    # head: round dome with a teal rim
    fill_disc(410, 648, 82, ROBOT_TEAL)
    fill_disc(410, 648, 74, ROBOT_BODY)
    # crescent happy eyes and a wide open smile
    happy_eye_arc(378, 636, 20, ROBOT_DARK)
    happy_eye_arc(442, 636, 20, ROBOT_DARK)
    arc(410, 668, 30, 0.15 * math.pi, 0.85 * math.pi, 7, ROBOT_DARK)
    # pink cheek blushes
    fill_disc(348, 668, 12, (255, 150, 150))
    fill_disc(472, 668, 12, (255, 150, 150))
    # body: round torso with a belly panel and buttons
    fill_ellipse(410, 800, 96, 108, ROBOT_TEAL)
    fill_ellipse(410, 800, 88, 100, ROBOT_BODY)
    fill_ellipse(410, 812, 58, 62, (226, 240, 238))
    for i, by in enumerate((776, 806, 836)):
        fill_disc(410, by, 8, ROBOT_TEAL if i % 2 == 0 else SCARF)
    # little feet
    fill_ellipse(368, 906, 34, 16, ROBOT_TEAL)
    fill_ellipse(452, 906, 34, 16, ROBOT_TEAL)
    # hand-knitted red scarf: band, stripes, a flowing tail with fringe
    fill_rect(322, 716, 498, 748, SCARF)
    for sx in (352, 392, 432, 472):
        fill_rect(sx, 716, sx + 8, 748, SCARF_DARK)
    # scarf tail draped down the chest front, slight diagonal fold,
    # fringed end at the bottom
    fill_poly([(462, 748), (508, 748), (520, 826), (512, 858),
               (492, 852), (478, 830)], SCARF)
    thick_line(472, 792, 514, 796, 5, SCARF_DARK)
    thick_line(476, 824, 518, 828, 5, SCARF_DARK)
    for (fx, fy) in ((486, 842), (493, 852), (500, 855), (507, 857),
                     (514, 850)):
        thick_line(fx, fy, fx + 2, fy + 12, 3, SCARF_DARK)
    # right arm reaching out to offer the sunflower
    thick_line(492, 736, 548, 692, 22, ROBOT_BODY)
    fill_disc(548, 690, 18, ROBOT_BODY)


def draw_child():
    # raised arms, hands open in delight
    thick_line(606, 748, 580, 662, 18, SKIN)
    thick_line(694, 748, 722, 660, 18, SKIN)
    fill_disc(578, 656, 16, SKIN)
    fill_disc(724, 654, 16, SKIN)
    # legs and shoes
    thick_line(628, 862, 622, 912, 20, SKIN)
    thick_line(672, 862, 678, 912, 20, SKIN)
    fill_ellipse(618, 918, 24, 12, (72, 120, 200))
    fill_ellipse(682, 918, 24, 12, (72, 120, 200))
    # body: coral shirt, blue shorts
    fill_poly([(606, 742), (694, 742), (706, 830), (594, 830)], SHIRT)
    fill_poly([(598, 828), (702, 828), (694, 866), (606, 866)], SHORTS)
    fill_disc(650, 742, 12, SHIRT)
    # head with brown hair cap and a tuft
    fill_disc(650, 668, 60, SKIN)
    fill_disc(650, 650, 62, HAIR)
    fill_disc(650, 672, 54, SKIN)
    fill_disc(650, 606, 12, HAIR)
    arc(650, 606, 22, math.pi, math.pi * 2.0, 8, HAIR)
    # laughing face: crescent eyes, open smile with tongue
    happy_eye_arc(626, 664, 14, ROBOT_DARK)
    happy_eye_arc(674, 664, 14, ROBOT_DARK)
    fill_ellipse(650, 700, 26, 18, (122, 40, 32))
    fill_ellipse(650, 708, 14, 9, (255, 130, 150))
    fill_disc(612, 690, 10, (255, 150, 150))
    fill_disc(688, 690, 10, (255, 150, 150))


def draw_dog():
    # wagging tail, curving up behind the body's rear side (drawn first
    # so its base hides behind the body and it can never read as a limb)
    # a curved tail sweeping up behind the body: a chain of segments
    # along a gentle bend, base hidden behind the body, rounded tip
    thick_line(925, 835, 952, 812, 16, DOG)
    thick_line(952, 812, 976, 784, 16, DOG)
    thick_line(976, 784, 992, 752, 15, DOG)
    thick_line(992, 752, 998, 724, 14, DOG)
    fill_disc(998, 718, 15, DOG)
    # sitting body and haunch
    fill_ellipse(862, 836, 88, 76, DOG)
    fill_ellipse(812, 862, 52, 44, DOG_LIGHT)
    # front legs and paws
    fill_rect(806, 850, 830, 908, DOG)
    fill_rect(846, 850, 870, 908, DOG)
    fill_ellipse(818, 910, 22, 11, DOG_DARK)
    fill_ellipse(858, 910, 22, 11, DOG_DARK)
    # floppy ears
    fill_ellipse(806, 700, 22, 44, DOG_DARK)
    fill_ellipse(914, 700, 22, 44, DOG_DARK)
    # head with lighter muzzle
    fill_disc(860, 716, 60, DOG)
    fill_ellipse(860, 738, 40, 26, DOG_LIGHT)
    fill_disc(860, 724, 12, ROBOT_DARK)
    # happy crescent eyes, open panting smile, pink tongue
    happy_eye_arc(834, 700, 13, ROBOT_DARK)
    happy_eye_arc(886, 700, 13, ROBOT_DARK)
    arc(860, 742, 22, 0.15 * math.pi, 0.85 * math.pi, 6, ROBOT_DARK)
    fill_ellipse(860, 766, 13, 20, (255, 130, 150))
    fill_disc(826, 726, 9, (255, 150, 150))
    fill_disc(894, 726, 9, (255, 150, 150))


def draw_blanket():
    """A red-and-white checked picnic blanket on the grass."""
    cx, cy, rx, ry = 520, 962, 272, 56
    cell = 34
    for gy in range(cy - ry, cy + ry + 1, cell):
        for gx in range(cx - rx, cx + rx + 1, cell):
            mx = gx + cell // 2
            my = gy + cell // 2
            q = ((mx - cx) / rx) ** 2 + ((my - cy) / ry) ** 2
            if q > 1.0:
                continue
            col = (226, 59, 59) if ((gx // cell) + (gy // cell)) % 2 == 0 \
                else (255, 246, 232)
            x0 = max(0, gx)
            x1 = min(W - 1, gx + cell - 1)
            y0 = max(0, gy)
            y1 = min(H - 1, gy + cell - 1)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                        set_px(x, y, col)


def draw_basket():
    # wicker basket with a cloth and two apples, on the blanket
    arc(700, 952, 34, math.pi, math.pi * 2.0, 7, (146, 96, 48))
    fill_poly([(668, 940), (732, 940), (724, 986), (676, 986)], (178, 116, 58))
    for wy in (952, 964, 976):
        thick_line(670, wy, 730, wy, 3, (146, 96, 48))
    fill_poly([(668, 940), (700, 922), (732, 940)], (255, 246, 232))
    fill_disc(688, 930, 11, (226, 59, 59))
    fill_disc(710, 928, 11, (255, 138, 61))


def draw_flowers_and_grass():
    rng = LCG(0xF10E2)
    petal_cols = [(255, 255, 255), (255, 201, 60), (255, 150, 200)]
    spots = []
    for _ in range(16):
        x = rng.randint(40, 980)
        y = rng.randint(760, 1010)
        # keep the blanket and the three friends clear
        if 240 < x < 800 and 880 < y < 1024:
            continue
        if 300 < x < 760 and 540 < y < 900:
            continue
        spots.append((x, y))
    for (x, y) in spots:
        col = petal_cols[rng.next() % 3]
        thick_line(x, y, x, y + 16, 4, LEAF)
        for k in range(5):
            a = k * math.pi * 2.0 / 5.0
            fill_disc(int(x + 9 * math.cos(a)), int(y + 9 * math.sin(a)),
                      6, col)
        fill_disc(x, y, 5, (255, 201, 60))
    # little grass tufts
    for _ in range(26):
        x = rng.randint(30, 990)
        y = rng.randint(740, 1015)
        if 240 < x < 800 and 880 < y < 1024:
            continue
        for (dx, h) in ((-6, 12), (0, 16), (6, 12)):
            thick_line(x, y, x + dx, y - h, 3, GRASS_DARK)


def render():
    draw_sky()
    draw_sun()
    draw_cloud(300, 205, 0.9)
    draw_cloud(720, 225, 0.75)
    draw_hills()
    draw_flowers_and_grass()
    draw_lanterns()
    draw_banner()
    draw_blanket()
    draw_robot()
    draw_child()
    draw_dog()
    draw_sunflower(588, 622, (548, 690))
    draw_butterfly(238, 408, 1.0, (255, 138, 61), (255, 201, 60))
    draw_butterfly(806, 392, 0.85, (255, 107, 157), (186, 130, 255))
    draw_butterfly(700, 452, 0.7, (255, 201, 60), (255, 138, 61))
    draw_basket()


# ---------------------------------------------------------------------------
# PNG encoding (deterministic; per-row filter picked by signed-byte cost)
# ---------------------------------------------------------------------------

def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png(rows):
    raw = bytearray()
    prev = bytes(W * 3)
    for row in rows:
        best = None
        best_cost = None
        for ftype in (0, 1, 2):
            if ftype == 0:
                filt = row
            elif ftype == 1:
                filt = bytes((row[i] - (row[i - 3] if i >= 3 else 0)) & 0xFF
                             for i in range(W * 3))
            else:
                filt = bytes((row[i] - prev[i]) & 0xFF for i in range(W * 3))
            cost = 0
            for b in filt:
                cost += b if b < 128 else 256 - b
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best = bytes((ftype,)) + bytes(filt)
        raw += best
        prev = bytes(row)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


def main():
    render()
    data = encode_png(ROWS)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
