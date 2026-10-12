#!/usr/bin/env python3
"""From a generated clip to keyed frames of its cleanest loop.

usage: video_frames.py RAW.mp4 OUTDIR [--fps 24] [--min-len 0.75] [--max-len 4] [--pick 8] [--key auto]
                       [--lo 40] [--hi 120] [--start S] [--end E]

1. extract every frame at --fps with ffmpeg (audio dropped — H3 always adds a soundtrack)
2. key each frame (key.py's despill key; the background is read from the border: magenta or green)
3. loop detection: on the keyed frames (premultiplied, downsampled, so the background never counts) find
   the pair (i, j), j-i within [min-len, max-len] seconds, whose frames differ least — the seam of the
   cleanest full cycle. The score is normalised by the clip's typical frame-to-frame motion, so it reads
   "how many frames' worth of motion the seam jumps": < 1 is a seamless loop.
4. pick --pick frames evenly from [i, j) and write them as OUTDIR/loop/f_00.png …, plus OUTDIR/loop.json
   with the seam score, the cycle bounds, and per-frame camera drift (alpha-centroid and bbox height of every
   extracted frame, so a zoom or a pan in the clip shows up as a number, not a hunch).
--start/--end restrict the search (e.g. skip a settling first half-second)."""
import argparse, json, os, subprocess, glob, numpy as np
from PIL import Image
import importlib.util
spec = importlib.util.spec_from_file_location("key", os.path.join(os.path.dirname(__file__), "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

ap = argparse.ArgumentParser()
ap.add_argument("raw"); ap.add_argument("outdir")
ap.add_argument("--fps", type=float, default=24); ap.add_argument("--min-len", type=float, default=0.75)
ap.add_argument("--max-len", type=float, default=4); ap.add_argument("--pick", type=int, default=8)
ap.add_argument("--key", default="auto"); ap.add_argument("--lo", type=float, default=40); ap.add_argument("--hi", type=float, default=120)
ap.add_argument("--start", type=float, default=0); ap.add_argument("--end", type=float, default=1e9)
a = ap.parse_args()
src = os.path.join(a.outdir, "src"); os.makedirs(src, exist_ok=True)
for f in glob.glob(os.path.join(src, "*.png")): os.remove(f)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.raw, "-an", "-vf", f"fps={a.fps}", os.path.join(src, "f_%04d.png")], check=True)
files = sorted(glob.glob(os.path.join(src, "f_*.png")))
keyed, small, cen, hgt = [], [], [], []
for f in files:
    rgba, keyname = key.key_image(np.array(Image.open(f).convert("RGB")), a.key, a.lo, a.hi)
    keyed.append(rgba)
    al = rgba[..., 3] / 255
    pm = rgba[..., :3] * al[..., None]
    im = Image.fromarray(np.dstack([pm, al * 255]).astype(np.uint8)).resize((96, 96), Image.BILINEAR)
    small.append(np.asarray(im, dtype=np.float64))
    ys, xs = np.nonzero(al > 0.5)
    cen.append([float(xs.mean()), float(ys.mean())] if len(xs) else [0, 0])
    hgt.append(int(ys.max() - ys.min() + 1) if len(ys) else 0)
n = len(small)
t = np.arange(n) / a.fps
step = np.median([np.abs(small[i + 1] - small[i]).mean() for i in range(n - 1)]) or 1e-6
best = None
for i in range(n):
    if t[i] < a.start: continue
    for j in range(i + int(a.min_len * a.fps), min(n, i + int(a.max_len * a.fps) + 1)):
        if t[j] > a.end: break
        d = np.abs(small[i] - small[j]).mean() / step
        if best is None or d < best[0]: best = (d, i, j)
d, i, j = best
idx = [i + round(k * (j - i) / a.pick) for k in range(a.pick)]
lo = os.path.join(a.outdir, "loop"); os.makedirs(lo, exist_ok=True)
for f in glob.glob(os.path.join(lo, "*.png")): os.remove(f)
for k, q in enumerate(idx):
    Image.fromarray(np.round(keyed[q]).astype(np.uint8)).save(os.path.join(lo, f"f_{k:02d}.png"))
cx = [c[0] for c in cen]; cy = [c[1] for c in cen]
meta = {"raw": a.raw, "key": keyname, "frames": n, "fps": a.fps, "duration_s": round(n / a.fps, 2),
        "loop": {"start_frame": i, "end_frame": j, "start_s": round(t[i], 3), "len_s": round((j - i) / a.fps, 3),
                 "seam_score": round(float(d), 3), "picked": idx},
        "drift": {"centroid_x_range_px": round(max(cx) - min(cx), 1), "centroid_y_range_px": round(max(cy) - min(cy), 1),
                  "height_range_pct": round(100 * (max(hgt) - min(hgt)) / max(1, np.median(hgt)), 1),
                  "height_first_last": [hgt[0], hgt[-1]]},
        "first_last_diff": round(float(np.abs(small[0] - small[-1]).mean() / step), 3)}
json.dump(meta, open(os.path.join(a.outdir, "loop.json"), "w"), indent=1)
print(json.dumps(meta))
