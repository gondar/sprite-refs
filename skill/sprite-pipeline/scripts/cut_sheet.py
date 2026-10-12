#!/usr/bin/env python3
"""Cut a keyed sprite SHEET (RGBA) into its figures, in reading order.

usage: cut_sheet.py KEYED.png OUTDIR [--min-area 4000] [--rows N]

Each figure is a connected blob of alpha (dilated a little so a tail tip or a detached paw stays with its
body); blobs smaller than --min-area are dropped (stray specks, flying hearts). Figures are ordered by row
(clustered on their vertical centre) then left to right, and written as OUTDIR/fig_00.png … tight-cropped,
plus OUTDIR/figs.json with each figure's box in the sheet."""
import argparse, json, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument("inp"); ap.add_argument("outdir")
ap.add_argument("--min-area", type=int, default=4000); ap.add_argument("--rows", type=int, default=0)
a = ap.parse_args()
im = np.array(Image.open(a.inp).convert("RGBA"))
mask = im[..., 3] > 40
lab, n = ndi.label(ndi.binary_dilation(mask, iterations=4))
objs = ndi.find_objects(lab)
figs = []
for i, sl in enumerate(objs):
    area = int((lab[sl] == i + 1).sum())
    if area < a.min_area: continue
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    figs.append({"id": i + 1, "box": [x0, y0, x1, y1], "cy": (y0 + y1) / 2, "area": area})
# rows: split on gaps in the vertical centres
figs.sort(key=lambda f: f["cy"])
rows, cur = [], [figs[0]]
for f in figs[1:]:
    h = f["box"][3] - f["box"][1]
    (cur.append(f) if f["cy"] - cur[-1]["cy"] < h * 0.5 else (rows.append(cur), cur := [f]))
rows.append(cur)
os.makedirs(a.outdir, exist_ok=True)
out = []
for r, row in enumerate(rows):
    for f in sorted(row, key=lambda f: f["box"][0]):
        x0, y0, x1, y1 = f["box"]
        crop = im[y0:y1, x0:x1].copy()
        crop[..., 3] = np.where(lab[y0:y1, x0:x1] == f["id"], crop[..., 3], 0)  # drop neighbours' pixels
        k = len(out)
        Image.fromarray(crop).save(os.path.join(a.outdir, f"fig_{k:02d}.png"))
        out.append({"file": f"fig_{k:02d}.png", "row": r, "box": f["box"], "area": f["area"]})
json.dump(out, open(os.path.join(a.outdir, "figs.json"), "w"), indent=1)
print(f"{len(out)} figures in {len(rows)} rows -> {a.outdir}")
