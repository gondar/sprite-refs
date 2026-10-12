#!/usr/bin/env python3
"""Onion-skin a packed strip: every frame's silhouette outline drawn over frame 1, plus per-frame numbers that
say how much the drawing jumps. usage: onion.py STRIP.png META.json OUT.png
  iou[i]   — alpha overlap of frame i with frame i+1 (a calm idle should be > 0.9; a walk 0.75-0.9)
  dx, dy   — shift of the alpha centroid between consecutive frames, px at strip size (jitter shows up here)
  area     — opaque area relative to frame 1 (an idle that breathes should stay within a few %)"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
strip, meta, out = sys.argv[1:4]
m = json.load(open(meta)); cw, ch = m["cell"]; n = m["frames"]
S = np.array(Image.open(strip).convert("RGBA"))
fr = [S[:, i * cw:(i + 1) * cw] for i in range(n)]
al = [f[..., 3] > 128 for f in fr]
cen = [np.array(np.nonzero(a)).mean(1) for a in al]
rows = []
for i in range(n):
    j = (i + 1) % n
    iou = (al[i] & al[j]).sum() / max(1, (al[i] | al[j]).sum())
    dy, dx = cen[j] - cen[i]
    rows.append({"f": i + 1, "iou_next": round(float(iou), 3), "dx": round(float(dx), 1), "dy": round(float(dy), 1),
                 "area": round(float(al[i].sum() / al[0].sum()), 3)})
sc = 3
base = Image.fromarray(fr[0]).resize((cw * sc, ch * sc), Image.NEAREST)
img = Image.new("RGBA", base.size, (24, 20, 34, 255)); img.alpha_composite(base)
d = ImageDraw.Draw(img)
cols = [(255, 80, 80), (255, 170, 60), (240, 230, 70), (90, 220, 90), (70, 200, 230), (90, 120, 255), (190, 90, 255), (255, 255, 255)]
for i, a in enumerate(al):
    edge = a & ~np.roll(a, 1, 0) | a & ~np.roll(a, 1, 1)
    for y, x in zip(*np.nonzero(edge)):
        d.point((x * sc + 1, y * sc + 1), fill=cols[i % 8])
img.save(out)
print(json.dumps(rows))
