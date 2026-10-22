#!/usr/bin/env python3
"""Korowód eagle: extract + key every frame of a first/last-frame H3 clip into the 1024 design canvas,
and measure it (corner colour per frame, frame 0 / last frame against the pictures).

usage: frames.py JOB_MP4 OUTDIR FIRST_PICTURE.png LAST_PICTURE.png
writes OUTDIR/k_###.png (RGBA, 1024x1024, the same canvas as refs/korowod/eagle/place-*.png) and OUTDIR/measure.json"""
import glob, json, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ekey import key, bg_of

clip, out, first, last = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
src = os.path.join(out, "src"); os.makedirs(src, exist_ok=True)
if not glob.glob(os.path.join(src, "f_*.png")):
    subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", "fps=24", os.path.join(src, "f_%03d.png")], check=True)
fs = sorted(glob.glob(os.path.join(src, "f_*.png")))
W, H = Image.open(fs[0]).size
pf = np.asarray(Image.open(first).convert("RGB").resize((W, H), Image.LANCZOS), float)
pl = np.asarray(Image.open(last).convert("RGB").resize((W, H), Image.LANCZOS), float)
corners, rec = [], {}
for i, f in enumerate(fs):
    rgb = np.asarray(Image.open(f).convert("RGB"), float)
    bg = bg_of(rgb); corners.append([round(x, 1) for x in bg])
    k = key(rgb, bg)
    im = Image.fromarray(np.round(k).astype(np.uint8), "RGBA").resize((1024, 1024), Image.LANCZOS)
    im.save(os.path.join(out, f"k_{i:03d}.png"))
    if i == 0: rec["mae_f0_first"] = round(float(np.abs(rgb - pf).mean()), 2)
    if i == len(fs) - 1:
        rec["mae_last_last"] = round(float(np.abs(rgb - pl).mean()), 2)
c = np.array(corners)
rec.update({"size": [W, H], "frames": len(fs), "corner_min": c.min(0).tolist(), "corner_max": c.max(0).tolist()})
json.dump(rec, open(os.path.join(out, "measure.json"), "w"))
print(os.path.basename(clip), rec)
