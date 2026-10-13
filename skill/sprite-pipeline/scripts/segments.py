#!/usr/bin/env python3
"""Cut one multi-action clip into named animations, and print where the actions really are.

usage: segments.py FRAMEDIR OUTDIR NAME=START-END[:STEP[:loop]] ... [--fps 24] [--key auto] [--min-cycle 0.25]
A segment marked `loop` (walk, run) is not cut at START/END: inside that window it searches the pair of frames
(i, j), j-i >= --min-cycle s, whose keyed silhouettes and colours match best, and keeps frames i..j-1 — one whole
stride, so the last frame flows into the first. It prints the seam score (difference at the cut divided by the
typical frame-to-frame motion: < 1 is smoother than an ordinary frame step).
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
ap.add_argument("--min-cycle", type=float, default=0.25)
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
def thumb(i):
    k = keyed(i); al = k[..., 3:4] / 255
    return np.asarray(Image.fromarray(np.dstack([k[..., :3] * al, al * 255]).astype(np.uint8)).resize((96, 96)), dtype=float)
for s in a.segs:
    name, rng = s.split("=")
    parts = rng.split(":"); rng = parts[0]; st = int(parts[1]) if len(parts) > 1 and parts[1] else 1
    loop = len(parts) > 2 and parts[2] == "loop"
    t0, t1 = map(float, rng.split("-"))
    lo_i, hi_i = int(t0 * a.fps), min(len(fs) - 1, int(t1 * a.fps))
    if loop:
        th = {i: thumb(i) for i in range(lo_i, hi_i + 1)}
        step_d = np.median([np.abs(th[i + 1] - th[i]).mean() for i in range(lo_i, hi_i)]) or 1e-6
        mc = max(2, int(a.min_cycle * a.fps)); best = None
        for i in range(lo_i, hi_i + 1):
            for j in range(i + mc, hi_i + 1):
                dd = np.abs(th[i] - th[j]).mean() / step_d
                if best is None or dd < best[0]: best = (dd, i, j)
        cut = f"{t0}-{t1}s"
        sd = np.abs(th[lo_i] - th[hi_i]).mean() / step_d
        d0, i, j = best
        idx = list(range(i, j, st))
        print(f"{name}: loop {i / a.fps:.3f}-{j / a.fps:.3f}s ({j - i} fr), seam {d0:.2f} (plain cut {cut}: {sd:.2f})")
    else:
        idx = list(range(lo_i, hi_i + 1, st))
    d = os.path.join(a.out, name); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(d, "*.png")): os.remove(f)
    for k, i in enumerate(idx): Image.fromarray(np.round(keyed(i)).astype(np.uint8)).save(os.path.join(d, f"f_{k:02d}.png"))
    print(name, len(idx), "frames", f"{t0}-{t1}s")
