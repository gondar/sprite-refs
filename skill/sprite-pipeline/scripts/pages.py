#!/usr/bin/env python3
"""Pack a gesture atlas for PHONES: one static base picture + pages of only the region that ever changes.

usage: pages.py IN_ATLAS.json OUT_DIR NAME [--max 4096] [--webp 70] [--pad 2] [--skip name,name]

Why: a full-cell atlas is fine to DOWNLOAD and fatal to DECODE. The Mountain King's 386-frame cutout atlas was
16286×5328 px = 87 Mpx ≈ 350 MB decoded; headless Chromium refused it (EncodingError) and iOS Safari refuses images
over ~16.7 Mpx. After the static lock (lock.py) or a cutout render, every pixel outside the moving region IS the home
frame, so: base = frame 0 at full cell size, crop = the bounding box of every pixel that differs from it in any frame
(+ --pad), pages = the cropped frames row-major, each page at most --max × --max px (≤ 16.7 Mpx).
Writes OUT_DIR/NAME-base.webp, NAME-p0.webp, NAME-p1.webp …, and NAME.json:
  {cell, pivot, fps, base, crop:[x,y,w,h], cols, rows, per_page, pages:[…], gestures:[{name, at, frames}]}
Draw: the base, then frame i from page i // per_page: cell j = i % per_page sits at
((j % cols) * (w + 2g) + g, (j // cols) * (h + 2g) + g) on the page, w × h, placed at (crop x, crop y). The gutter g
repeats each frame's edge pixels: without it a scaled page bled the next frame's top into the bottom edge — a hairline
across the King's legs. It checks that rebuilding every frame from base + crop is exact before compression."""
import argparse, json, os
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument("atlas"); ap.add_argument("out"); ap.add_argument("name")
ap.add_argument("--max", type=int, default=4096); ap.add_argument("--webp", type=int, default=70)
ap.add_argument("--pad", type=int, default=2); ap.add_argument("--gutter", type=int, default=4); ap.add_argument("--skip", default="")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
m = json.load(open(a.atlas)); W, H = m["cell"]
src = np.asarray(Image.open(os.path.splitext(a.atlas)[0] + ".png").convert("RGBA"))
cell = lambda i: src[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W]
skip = set(x for x in a.skip.split(",") if x)
gs = [g for g in m["gestures"] if g["name"] not in skip]
home = cell(0); frames = []; out_g = []
for g in gs:
    out_g.append({"name": g["name"], "at": len(frames), "frames": g["frames"]})
    frames += [cell(g["at"] + k) for k in range(g["frames"])]
changed = np.zeros((H, W), bool)
for f in frames: changed |= (f != home).any(2)
ys, xs = np.nonzero(changed)
x0, y0 = max(0, xs.min() - a.pad), max(0, ys.min() - a.pad); x1, y1 = min(W, xs.max() + 1 + a.pad), min(H, ys.max() + 1 + a.pad)
cw, ch = x1 - x0, y1 - y0
for f in frames:                                    # exactness: outside the crop every frame IS the base
    o = f.copy(); o[y0:y1, x0:x1] = home[y0:y1, x0:x1]
    assert (o == home).all(), "a frame changes outside the crop"
cw, ch = int(cw), int(ch); G = a.gutter; pw, ph = cw + 2 * G, ch + 2 * G     # pitch: frame + gutter on every side
cols = a.max // pw; rows = a.max // ph; per = cols * rows
pages = []
for p in range(0, len(frames), per):
    chunk = frames[p:p + per]; r = (len(chunk) + cols - 1) // cols
    pg = np.zeros((r * ph, cols * pw, 4), np.uint8)
    for i, f in enumerate(chunk):   # each frame with its edge pixels repeated into the gutter: a scaled-down page
        X, Y = (i % cols) * pw, (i // cols) * ph   # samples a little past a frame's edge, and must find the same frame there
        pg[Y:Y + ph, X:X + pw] = np.pad(f[y0:y1, x0:x1], ((G, G), (G, G), (0, 0)), mode="edge")
    pg = Image.fromarray(pg)
    fn = f"{a.name}-p{len(pages)}.webp"; pg.save(os.path.join(a.out, fn), "WEBP", quality=a.webp, method=6, alpha_quality=90)
    pages.append(fn)
Image.fromarray(home).save(os.path.join(a.out, f"{a.name}-base.webp"), "WEBP", quality=90, method=6, alpha_quality=100)
meta = {"cell": [W, H], "pivot": m.get("pivot"), "fps": m.get("fps", 12), "base": f"{a.name}-base.webp",
        "crop": [int(x0), int(y0), int(cw), int(ch)], "gutter": G, "cols": cols, "rows": rows, "per_page": per, "pages": pages, "gestures": out_g}
json.dump(meta, open(os.path.join(a.out, a.name + ".json"), "w"), indent=1)
sizes = [os.path.getsize(os.path.join(a.out, f)) for f in pages + [meta["base"]]]
print(f"{len(frames)} frames, crop {cw}x{ch} at ({x0},{y0}), gutter {G}, {len(pages)} page(s) of ≤{cols * pw}x{rows * ph}"
      f" ({cols * pw * rows * ph / 1e6:.1f} Mpx), {sum(sizes) / 1e6:.2f} MB")
