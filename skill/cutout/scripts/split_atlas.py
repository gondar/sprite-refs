#!/usr/bin/env python3
"""Split a full-cell gesture atlas into (1) one static base image and (2) an atlas of only the rectangle that ever
changes. The game draws base.png at the cell origin, then the gesture cell at (crop.x, crop.y). Inside the
rectangle the base is cleared (transparent), so cell over base == the full frame exactly.

usage: split_atlas.py ATLAS.json OUTDIR [--margin 2] [--webp 70]"""
import argparse, json, os, numpy as np
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument("atlas"); ap.add_argument("out")
ap.add_argument("--margin", type=int, default=2); ap.add_argument("--webp", type=int, default=70); A = ap.parse_args()
m = json.load(open(A.atlas)); at = np.asarray(Image.open(A.atlas[:-5] + ".png").convert("RGBA"))
W, H = m["cell"]; n = sum(g["frames"] for g in m["gestures"])
get = lambda i: at[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W]
rest = get(0); ch = np.zeros((H, W), bool)
for i in range(n): ch |= (get(i) != rest).any(2)
ys, xs = np.nonzero(ch); M = A.margin
x0, y0, x1, y1 = max(0, xs.min() - M), max(0, ys.min() - M), min(W, xs.max() + 1 + M), min(H, ys.max() + 1 + M)
x0, y0, x1, y1 = map(int, (x0, y0, x1, y1)); cw, chh = x1 - x0, y1 - y0
os.makedirs(A.out, exist_ok=True)
base = rest.copy(); base[y0:y1, x0:x1] = 0
Image.fromarray(base).save(os.path.join(A.out, "base.png"), optimize=True)
cols = 16383 // cw; rows = (n + cols - 1) // cols
sh = np.zeros((rows * chh, cols * cw, 4), np.uint8)
for i in range(n): sh[(i // cols) * chh:(i // cols + 1) * chh, (i % cols) * cw:(i % cols + 1) * cw] = get(i)[y0:y1, x0:x1]
im = Image.fromarray(sh); im.save(os.path.join(A.out, "atlas.png"), optimize=True)
im.save(os.path.join(A.out, "atlas.webp"), quality=A.webp, method=6, alpha_quality=90)
Image.fromarray(base).save(os.path.join(A.out, "base.webp"), quality=A.webp, method=6, alpha_quality=90)
meta = dict(m, cols=cols, rows=rows, crop=[int(x0), int(y0), int(cw), int(chh)], base="base.png",
            note="draw base at the cell origin, then cell i of this atlas at (crop[0], crop[1]); cell grid is crop[2] x crop[3]")
json.dump(meta, open(os.path.join(A.out, "atlas.json"), "w"), indent=1)
# exactness check: rebuild every frame
err = 0
for i in range(n):
    f = base.copy(); f[y0:y1, x0:x1] = sh[(i // cols) * chh:(i // cols + 1) * chh, (i % cols) * cw:(i % cols + 1) * cw]
    err = max(err, int(np.abs(f.astype(int) - get(i).astype(int)).max()))
kb = lambda p: os.path.getsize(os.path.join(A.out, p)) // 1024
print(f"crop {meta['crop']} ({cw * chh / (W * H):.0%} of the cell), {cols}x{rows}; rebuild max err {err}; "
      f"atlas.webp {kb('atlas.webp')} KB + base.webp {kb('base.webp')} KB")
