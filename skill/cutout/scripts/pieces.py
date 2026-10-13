#!/usr/bin/env python3
"""Key a cut-out parts sheet and split it into pieces by connected component (any layout: exploded view or grid).

usage: pieces.py SHEET.png OUTDIR [--key auto] [--min-frac 0.0015]
writes OUTDIR/pNN.png (tight RGBA crop), OUTDIR/pieces.json ({id, bbox:[x,y,w,h] in sheet px, area}) and
OUTDIR/index.png (the keyed sheet with every piece boxed and numbered) — name the pieces from index.png."""
import argparse, json, os, importlib.util, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("key", os.path.join(here, "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

ap = argparse.ArgumentParser()
ap.add_argument("sheet"); ap.add_argument("outdir")
ap.add_argument("--key", default="auto"); ap.add_argument("--min-frac", type=float, default=0.0015)
a = ap.parse_args()
os.makedirs(a.outdir, exist_ok=True)
rgba, k = key.key_image(np.array(Image.open(a.sheet).convert("RGB")), a.key)
al = rgba[..., 3]
lab, n = ndi.label(ndi.binary_closing(al > 128, iterations=2))
H, W = al.shape
out = []
for i, sl in enumerate(ndi.find_objects(lab), 1):
    m = lab[sl] == i
    if m.sum() < a.min_frac * H * W: continue
    y0, x0 = sl[0].start, sl[1].start
    # widen by 2 px to keep the soft edge, and keep only this component's pixels (neighbours' edges zeroed)
    yy0, xx0 = max(0, y0 - 2), max(0, x0 - 2)
    yy1, xx1 = min(H, sl[0].stop + 2), min(W, sl[1].stop + 2)
    own = ndi.binary_dilation(lab[yy0:yy1, xx0:xx1] == i, iterations=2)
    crop = rgba[yy0:yy1, xx0:xx1].copy(); crop[..., 3] *= own
    pid = f"p{len(out):02d}"
    Image.fromarray(np.round(crop).astype(np.uint8)).save(os.path.join(a.outdir, pid + ".png"))
    out.append({"id": pid, "bbox": [int(xx0), int(yy0), int(xx1 - xx0), int(yy1 - yy0)], "area": int(m.sum())})
json.dump({"sheet": a.sheet, "key": k, "size": [W, H], "pieces": out}, open(os.path.join(a.outdir, "pieces.json"), "w"), indent=1)
bg = Image.new("RGBA", (W, H), (235, 235, 235, 255)); bg.alpha_composite(Image.fromarray(np.round(rgba).astype(np.uint8)))
d = ImageDraw.Draw(bg)
for p in out:
    x, y, w, h = p["bbox"]; d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0, 255), width=2)
    d.rectangle([x, y, x + 34, y + 18], fill=(255, 0, 0, 255)); d.text((x + 3, y + 3), p["id"], fill=(255, 255, 255, 255))
bg.convert("RGB").save(os.path.join(a.outdir, "index.png"))
print(f"{len(out)} pieces from {a.sheet} (key {k})")
