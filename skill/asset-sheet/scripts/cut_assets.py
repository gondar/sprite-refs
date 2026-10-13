#!/usr/bin/env python3
"""Cut a sheet of many separate assets into named files + an atlas, and prove the names are right.

usage: cut_assets.py SHEET.png ITEMS.txt OUTDIR --grid RxC [--key auto|magenta|green|border] [--lo 40] [--hi 120]
                     [--min-area-frac 0.08] [--pad 4] [--max-side 256] [--webp 86]

ITEMS.txt: one asset name per line, in the order they were listed in the prompt (reading order of the grid).
1. key the background (same key as the animation skill: magenta/green excess with edge-only despill, or the
   border colour for anything else);
2. find blobs (dilated a little, so a lantern's handle stays with the lantern) and drop specks smaller than
   --min-area-frac of a grid cell;
3. assign each blob to the grid cell its centre falls in. Every cell must hold something — an EMPTY cell means
   the model skipped or merged an item, every later name would be off by one, and the run exits with code 2 so a
   script cannot quietly ship a misnamed set. Two or more blobs in one cell are one object in pieces (antlers)
   and are merged into one asset and reported;
4. write OUTDIR/<slug>.webp (tight crop + --pad, longest side capped at --max-side), atlas.png + atlas.json
   (shelf-packed, {name: {x,y,w,h}}), and check.png: every cut on a checkerboard with its name under it."""
import argparse, json, math, os, re, sys, numpy as np, importlib.util
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("key", os.path.join(here, "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

ap = argparse.ArgumentParser()
ap.add_argument("sheet"); ap.add_argument("items"); ap.add_argument("outdir")
ap.add_argument("--grid", required=True); ap.add_argument("--key", default="auto")
ap.add_argument("--lo", type=float, default=40); ap.add_argument("--hi", type=float, default=120)
ap.add_argument("--min-area-frac", type=float, default=0.08); ap.add_argument("--pad", type=int, default=4)
ap.add_argument("--max-side", type=int, default=256); ap.add_argument("--webp", type=int, default=86)
ap.add_argument("--dup", type=float, default=0.055,
                help="flag pairs of cuts closer than this (mean abs diff of 32 px premultiplied thumbnails); measured: "
                     "real duplicates 0.035-0.050, the closest distinct pair on a clean 100-sheet 0.059 (lily pad vs stone)")
a = ap.parse_args()
R, C = map(int, a.grid.lower().split("x"))
names = [l.strip() for l in open(a.items) if l.strip()][:R * C]
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]

rgb = np.array(Image.open(a.sheet).convert("RGB"))
rgba, kname = key.key_image(rgb, a.key, a.lo, a.hi)
H, W = rgba.shape[:2]; cw, ch = W / C, H / R
lab, n = ndi.label(ndi.binary_dilation(rgba[..., 3] > 60, iterations=max(2, int(min(cw, ch) * 0.02))))
areas = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
cells = {}
for i, ar in enumerate(areas):
    if ar < a.min_area_frac * cw * ch: continue
    ys, xs = np.nonzero(lab == i + 1)
    r, c = min(R - 1, int(ys.mean() // ch)), min(C - 1, int(xs.mean() // cw))
    cells.setdefault((r, c), []).append(i + 1)
os.makedirs(a.outdir, exist_ok=True)
bad, cuts, merged = [], [], []
for r in range(R):
    for c in range(C):
        k = r * C + c; got = cells.get((r, c), [])
        # several blobs in one cell = one object in pieces (antlers, a whistle and its cord): merged, reported
        if len(got) > 1: merged.append(f"{names[k] if k < len(names) else (r, c)}: {len(got)} pieces merged")
        if not got: bad.append((r, c, 0, names[k] if k < len(names) else "?")); continue
        name = slug(names[k]) if k < len(names) else f"cell_{r}_{c}"
        m = np.isin(lab, got)
        ys, xs = np.nonzero(m)
        y0, y1 = max(0, ys.min() - a.pad), min(H, ys.max() + 1 + a.pad)
        x0, x1 = max(0, xs.min() - a.pad), min(W, xs.max() + 1 + a.pad)
        crop = rgba[y0:y1, x0:x1].copy(); crop[..., 3] = np.where(m[y0:y1, x0:x1], crop[..., 3], 0)
        im = Image.fromarray(np.round(crop).astype(np.uint8))
        if max(im.size) > a.max_side:
            s = a.max_side / max(im.size); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        im.save(os.path.join(a.outdir, name + ".webp"), "WEBP", quality=a.webp, method=6)
        cuts.append((name, im))
# atlas: shelf packing in name order
aw = int(math.ceil(math.sqrt(sum(i.width * i.height for _, i in cuts)) * 1.15))
x = y = shelf = 0; rects = {}
for name, im in cuts:
    if x + im.width > aw: x, y, shelf = 0, y + shelf + 2, 0
    rects[name] = {"x": x, "y": y, "w": im.width, "h": im.height}; x += im.width + 2; shelf = max(shelf, im.height)
atlas = Image.new("RGBA", (aw, y + shelf), (0, 0, 0, 0))
for name, im in cuts: atlas.alpha_composite(im, (rects[name]["x"], rects[name]["y"]))
atlas.save(os.path.join(a.outdir, "atlas.png"))
json.dump({"image": "atlas.png", "frames": rects, "source": a.sheet, "grid": a.grid, "key": kname}, open(os.path.join(a.outdir, "atlas.json"), "w"), indent=1)
# check sheet
T = 150; cols = min(8, max(1, len(cuts))); rows = math.ceil(len(cuts) / cols)
chk = Image.new("RGB", (cols * T, rows * (T + 16)), (255, 255, 255)); d = ImageDraw.Draw(chk)
try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
except OSError: f = ImageFont.load_default()
for k, (name, im) in enumerate(cuts):
    X, Y = (k % cols) * T, (k // cols) * (T + 16)
    for yy in range(0, T, 10):
        for xx in range(0, T, 10):
            if (xx // 10 + yy // 10) % 2: d.rectangle([X + xx, Y + yy, X + xx + 9, Y + yy + 9], fill=(215, 215, 215))
    t = im.copy(); t.thumbnail((T - 10, T - 10)); chk.paste(t, (X + (T - t.width) // 2, Y + (T - t.height) // 2), t)
    d.text((X + 3, Y + T + 1), name[:24], fill=(30, 30, 30), font=f)
chk.save(os.path.join(a.outdir, "check.png"))
# duplicates: an over-full sheet repeats items and drops others, so every cell holds something and the count
# check passes while every later name is wrong (144 on one 1K sheet did exactly that)
def feat(im):
    t = im.copy(); t.thumbnail((32, 32)); c = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    c.alpha_composite(t, ((32 - t.width) // 2, (32 - t.height) // 2)); q = np.asarray(c, float) / 255
    return np.dstack([q[..., :3] * q[..., 3:4], q[..., 3:4]]).ravel()
dups = []
if len(cuts) > 1:
    M = np.array([feat(im) for _, im in cuts]); D = np.abs(M[:, None] - M[None]).mean(2)
    for i in range(len(cuts)):
        for j in range(i + 1, len(cuts)):
            if D[i, j] < a.dup: dups.append(f"{cuts[i][0]} ~ {cuts[j][0]} ({D[i, j]:.3f})")
print(json.dumps({"expected": R * C, "cut": len(cuts), "cells_wrong": len(bad), "key": kname,
                  "merged": merged, "possible_duplicates": dups[:12], "bad": [f"cell {r},{c}: empty (expected '{nm}')" for r, c, k, nm in bad][:12]}))
sys.exit(2 if bad else 3 if dups else 0)
