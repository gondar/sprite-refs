#!/usr/bin/env python3
"""Korowód eagle3: extract + key every frame of a first/last-frame H3 clip onto the WORK canvas and measure it.
usage: frames.py CLIP.mp4 OUTDIR FIRST_POSE LAST_POSE      (poses: home | perch | herb)
OUTDIR/k_###.png (RGBA WORK², same canvas as refs/korowod/eagle3/anim/place-*.png), OUTDIR/measure.json, OUTDIR/sheet.png
Measures per frame: corner (ground) colour, mean colour of the bird (opaque px), share of dark px inside the bird
(ink is ~10 %; a bird turning dark/brown raises it), distance to frame 0 / to the home picture."""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/sprite-refs/jobs/korowod-eagle")
from ekey import key, bg_of
A = "/home/user/sprite-refs/refs/korowod/eagle3/anim"
clip, out, p0, p1 = sys.argv[1:5]
os.makedirs(out + "/src", exist_ok=True)
if not glob.glob(out + "/src/f_*.png"):
    subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", "fps=24", out + "/src/f_%03d.png"], check=True)
fs = sorted(glob.glob(out + "/src/f_*.png")); W, H = Image.open(fs[0]).size
blue = lambda p: np.asarray(Image.open(f"{A}/eagle3-{p}-blue-v1.png").convert("RGB").resize((W, H), Image.LANCZOS), float)
pf, pl = blue(p0), blue(p1)
WORK = Image.open(f"{A}/place-home.png").size[0]
rows = []; th0 = None
def th(k): t = np.asarray(Image.fromarray(k).resize((128, 128), Image.BILINEAR), float) / 255; return np.dstack([t[..., :3] * t[..., 3:], t[..., 3:]])
for i, f in enumerate(fs):
    rgb = np.asarray(Image.open(f).convert("RGB"), float); bg = bg_of(rgb)
    k = np.round(key(rgb, bg)).astype(np.uint8)
    op = k[..., 3] > 250; px = rgb[op]
    dark = float((px.max(1) < 90).mean()); mc = px.mean(0)
    t = th(k); th0 = t if th0 is None else th0
    Image.fromarray(k, "RGBA").resize((WORK, WORK), Image.LANCZOS).save(f"{out}/k_{i:03d}.png")
    ys, xs = np.nonzero(k[..., 3] > 128)
    rows.append({"i": i, "corner": [round(x) for x in bg], "mean": [round(x, 1) for x in mc], "dark": round(dark, 3),
                 "dF0": round(float(np.abs(t - th0).mean() * 100), 2), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]})
c = np.array([r["corner"] for r in rows]); m = np.array([r["mean"] for r in rows]); d = [r["dark"] for r in rows]
rec = {"clip": os.path.basename(clip), "size": [W, H], "frames": len(fs),
       "mae_f0_first": round(float(np.abs(np.asarray(Image.open(fs[0]).convert("RGB"), float) - pf).mean()), 2),
       "mae_last_last": round(float(np.abs(np.asarray(Image.open(fs[-1]).convert("RGB"), float) - pl).mean()), 2),
       "corner_min": c.min(0).tolist(), "corner_max": c.max(0).tolist(),
       "bird_mean_min": m.min(0).round(1).tolist(), "bird_mean_max": m.max(0).round(1).tolist(), "dark_min": min(d), "dark_max": max(d), "rows": rows}
json.dump(rec, open(out + "/measure.json", "w"), indent=0)
print(json.dumps({k: v for k, v in rec.items() if k != "rows"}))
for r in rows[::4]: print(r["i"], r["corner"], r["mean"], r["dark"], r["dF0"], r["bbox"])
# contact sheet: every 2nd frame, with index
from PIL import ImageDraw
tw = 160; sel = list(range(0, len(fs), 2)); cols = 12
sh = Image.new("RGB", (cols * tw, ((len(sel) + cols - 1) // cols) * tw), (40, 40, 40)); dr = ImageDraw.Draw(sh)
for j, i in enumerate(sel):
    sh.paste(Image.open(fs[i]).convert("RGB").resize((tw, tw), Image.LANCZOS), ((j % cols) * tw, (j // cols) * tw))
    dr.text(((j % cols) * tw + 3, (j // cols) * tw + 2), str(i), fill=(255, 255, 0))
sh.save(out + "/sheet.png")
