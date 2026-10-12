#!/usr/bin/env python3
"""Cut one multi-action clip into named animations, and print where the actions really are.

usage: segments.py FRAMEDIR OUTDIR NAME=START-END[:STEP] ... [--fps 24] [--key auto]
FRAMEDIR is the `src/` folder video_frames.py extracted (all frames at --fps). START/END are seconds, STEP is
"keep every Nth frame". Each segment is keyed and written to OUTDIR/<NAME>/f_00.png …; pack it with pack.py.
It also prints a motion curve (mean keyed-alpha change per 1/6 s) so the boundaries can be read off the clip
instead of trusted from the prompt's timing."""
import argparse, glob, os, sys, numpy as np, importlib.util
from PIL import Image
spec = importlib.util.spec_from_file_location("key", os.path.join(os.path.dirname(__file__), "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("segs", nargs="+")
ap.add_argument("--fps", type=float, default=24); ap.add_argument("--key", default="auto")
a = ap.parse_args()
fs = sorted(glob.glob(os.path.join(a.src, "f_*.png")))
cache = {}
def keyed(i):
    if i not in cache: cache[i] = key.key_image(np.array(Image.open(fs[i]).convert("RGB")), a.key)[0]
    return cache[i]
small = [np.asarray(Image.fromarray(keyed(i)[..., 3].astype(np.uint8)).resize((64, 64)), dtype=float) for i in range(len(fs))]
step = int(a.fps / 6)
curve = [np.abs(small[i + step] - small[i]).mean() for i in range(0, len(fs) - step, step)]
print("motion per 1/6 s:", " ".join(f"{i * step / a.fps:.2f}:{c:.0f}" for i, c in enumerate(curve)))
for s in a.segs:
    name, rng = s.split("=")
    rng, st = (rng.split(":") + ["1"])[:2]
    t0, t1 = map(float, rng.split("-"))
    idx = list(range(int(t0 * a.fps), min(len(fs), int(t1 * a.fps) + 1), int(st)))
    d = os.path.join(a.out, name); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(d, "*.png")): os.remove(f)
    for k, i in enumerate(idx): Image.fromarray(np.round(keyed(i)).astype(np.uint8)).save(os.path.join(d, f"f_{k:02d}.png"))
    print(name, len(idx), "frames", f"{t0}-{t1}s")
