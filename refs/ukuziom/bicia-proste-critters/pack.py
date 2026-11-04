#!/usr/bin/env python3
"""Pack the cut critters of sheet-critters-16.png into the ONE small atlas MusicGames ships:
ukulele-warmup/art/jungle/critters.webp (+ the frame table printed as JSON for AMB in ukulele-warmup/phone.js).

Groups share one scale and one cell size, so swapping frames inside a group never jumps:
  head  (4 faces, bottom-centre aligned)    clump (the fern clump, bottom-centre)
  snail (2 frames, bottom-left aligned)     spider (2 frames, centre aligned)
usage: python3 pack.py OUT.webp"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = os.path.join(HERE, "cut")
GROUPS = [  # name, frames, width of the FIRST frame in the atlas (2x of its largest on-screen size), alignment
    ("head", ["monkey-front", "monkey-left", "monkey-right", "monkey-baby"], 84, "bc"),
    ("clump", ["leaves-b"], 136, "bc"),
    ("snail", ["snail", "snail-stretch"], 60, "bl"),
    ("spider", ["spider", "spider-tucked"], 50, "cc"),
]
def despill(im, everywhere):
    """The magenta key left a purple cast where a leaf is thin or an edge is soft: a pixel with both red and blue
    above green (magenta's signature) gets them pulled under green. On the fern everywhere (nothing in it is purple);
    elsewhere only on soft edges (the spider's plum body is purple inside on purpose)."""
    import numpy as np
    a = np.asarray(im).astype(np.float32)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    m = (np.minimum(r, b) > g + 6) & (al > 0)
    if not everywhere: m &= al < 250
    a[..., 0] = np.where(m, np.minimum(r, g * 0.95), r)
    a[..., 2] = np.where(m, np.minimum(b, g * 0.6), b)
    return Image.fromarray(a.clip(0, 255).astype("uint8"), "RGBA")


out = sys.argv[1]
cells, x, y, rowh, W = [], 0, 0, 0, 512
frames = {}
for name, fr, w0, al in GROUPS:
    ims = [Image.open(os.path.join(CUT, f + ".webp")).convert("RGBA") for f in fr]
    k = w0 / ims[0].width
    ims = [despill(im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS), name == "clump") for im in ims]
    cw, ch = max(i.width for i in ims), max(i.height for i in ims)
    for f, im in zip(fr, ims):
        if x + cw > W: x, y, rowh = 0, y + rowh + 2, 0
        cell = Image.new("RGBA", (cw, ch))
        ox = 0 if al[1] == "l" else (cw - im.width) // 2
        oy = ch - im.height if al[0] == "b" else (ch - im.height) // 2
        cell.alpha_composite(im, (ox, oy))
        cells.append((cell, x, y)); frames[f] = [x, y, cw, ch]
        x += cw + 2; rowh = max(rowh, ch)
H = y + rowh
atlas = Image.new("RGBA", (W, H))
for c, cx, cy in cells: atlas.alpha_composite(c, (cx, cy))
atlas.save(out, "WEBP", quality=82, method=6, alpha_quality=90)
print(json.dumps({"size": [W, H], "frames": frames}))
print(os.path.getsize(out), "bytes", file=sys.stderr)
