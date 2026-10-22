#!/usr/bin/env python3
"""Per-frame curves for a keyed clip dir: distance to the home picture and to frame 0 (alpha+colour on 128 px
thumbnails), the silhouette's top / bottom row (wing up / down) and its width. Also a contact sheet.
usage: curves.py DIR HOME_PLACE.png [SHEET.png]"""
import glob, sys
import numpy as np
from PIL import Image

d, homep = sys.argv[1:3]
fs = sorted(glob.glob(d + "/k_*.png"))
def th(im):
    a = np.asarray(im.resize((128, 128), Image.BILINEAR), float) / 255
    return np.dstack([a[..., :3] * a[..., 3:], a[..., 3:]])
home = th(Image.open(homep)); f0 = None
rows = []
for i, f in enumerate(fs):
    im = Image.open(f); t = th(im)
    if f0 is None: f0 = t
    a = np.asarray(im)[..., 3] > 128; ys, xs = np.nonzero(a)
    rows.append((i, np.abs(t - home).mean() * 100, np.abs(t - f0).mean() * 100, ys.min(), ys.max(), xs.min(), xs.max()))
print(" i  dHome  dF0  top  bot  x0  x1")
for r in rows: print("%3d %5.2f %5.2f %4d %4d %4d %4d" % r)
if len(sys.argv) > 3:
    n = len(fs); cols = 12; tw = 160; sel = list(range(0, n, 2))
    sh = Image.new("RGB", (cols * tw, ((len(sel) + cols - 1) // cols) * tw), (40, 40, 40))
    for j, i in enumerate(sel):
        im = Image.open(fs[i]).resize((tw, tw), Image.LANCZOS)
        bg = Image.new("RGBA", (tw, tw), (90, 90, 90, 255)); bg.alpha_composite(im)
        sh.paste(bg.convert("RGB"), ((j % cols) * tw, (j // cols) * tw))
    sh.save(sys.argv[3])
