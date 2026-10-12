#!/usr/bin/env python3
"""Align keyed frames on one pivot, pack them into a strip + JSON, and preview them as a GIF.

usage: pack.py OUT_BASENAME FRAME.png [FRAME.png ...] [--height 160] [--fps 8] [--anchor head|feet|bbox]
               [--bg 2a1e3a] [--scale-gif 2] [--pingpong]

Alignment (one rule for every frame, never a per-frame fudge):
  baseline  = the lowest opaque row (the feet stand on one line)
  x pivot   = head: centroid of opaque pixels in the top 35 % of the figure (stable through a turnaround and a
              swinging tail);  feet: centroid of the lowest 8 % (walk cycles);  bbox: box centre.
All frames keep their RELATIVE size — one scale factor for the whole set, chosen so the tallest frame is
--height px. A frame that is smaller in the sheet stays smaller (a crouch must not grow back to standing).
Writes OUT.png (strip of equal cells), OUT.json (cell size, pivot, fps, frames), OUT.gif (on --bg) and
OUT@game.gif at the real size."""
import argparse, json, numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("frames", nargs="+")
ap.add_argument("--height", type=int, default=160); ap.add_argument("--fps", type=float, default=8)
ap.add_argument("--anchor", default="head"); ap.add_argument("--bg", default="2a1e3a")
ap.add_argument("--scale-gif", type=int, default=2); ap.add_argument("--pingpong", action="store_true")
a = ap.parse_args()

fr = [np.array(Image.open(p).convert("RGBA")) for p in a.frames]


def pivot(f):
    al = f[..., 3] > 128
    ys, xs = np.nonzero(al)
    top, bot = ys.min(), ys.max()
    h = bot - top + 1
    if a.anchor == "head": sel = ys < top + 0.35 * h
    elif a.anchor == "feet": sel = ys > bot - 0.08 * h
    else: return (xs.min() + xs.max()) / 2, bot
    return xs[sel].mean(), bot


pv = [pivot(f) for f in fr]
L = max(px for px, _ in pv); R = max(f.shape[1] - px for f, (px, _) in zip(fr, pv))
T = max(by + 1 for _, by in pv)  # tallest frame above its baseline
W, H = int(np.ceil(L + R)) + 4, int(T) + 4
sc = a.height / H
cw, ch = max(1, round(W * sc)), a.height
cells = []
for f, (px, by) in zip(fr, pv):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.alpha_composite(Image.fromarray(f), (int(round(L - px)) + 2, int(H - 2 - (by + 1))))
    cells.append(c.resize((cw, ch), Image.LANCZOS))
strip = Image.new("RGBA", (cw * len(cells), ch), (0, 0, 0, 0))
for i, c in enumerate(cells): strip.alpha_composite(c, (i * cw, 0))
strip.save(a.out + ".png")
meta = {"frames": len(cells), "cell": [cw, ch], "pivot": [round((L + 2) * sc, 1), ch - round(2 * sc, 1)],
        "fps": a.fps, "loop": True, "pingpong": a.pingpong, "anchor": a.anchor, "sources": a.frames}
json.dump(meta, open(a.out + ".json", "w"), indent=1)

order = list(range(len(cells)))
if a.pingpong: order += order[-2:0:-1]
bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4))


def gif(path, s):
    out = []
    for i in order:
        b = Image.new("RGBA", (cw, ch), bg + (255,)); b.alpha_composite(cells[i])
        b = b.convert("RGB")
        if s != 1: b = b.resize((cw * s, ch * s), Image.NEAREST if s > 1 else Image.LANCZOS)
        out.append(b)
    out[0].save(path, save_all=True, append_images=out[1:], duration=round(1000 / a.fps), loop=0, disposal=2)


gif(a.out + ".gif", a.scale_gif)
gif(a.out + "@game.gif", 1)
print(json.dumps(meta))
