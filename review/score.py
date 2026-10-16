"""Score an idle-gesture atlas (gestures.py / lock.py / cutout format) on the owner's complaints, at cell size.
usage: score.py NAME=atlas.json [NAME=atlas.json …]
  static  — max over frames of mean |RGBA diff| vs the gesture's first frame over the bottom 35 % of the figure
            (legs, feet, throne base): shimmer and broken throne. Lower is better; ~0 means locked.
  colour  — max over frames of the distance between the figure's mean RGB and the first frame's: colour drift.
  seam    — max |diff| between any gesture's first/last frame and gesture 0's first frame: does every gesture meet
            on one home frame.
  motion  — mean over gestures of the largest mean |diff| vs the first frame over the upper 65 %: is anything visibly
            happening (a locked but motionless sprite would win the other three)."""
import json, sys, os
import numpy as np
from PIL import Image

def cells(path):
    m = json.load(open(path)); base = os.path.splitext(path)[0]
    a = np.asarray(Image.open(base + ".png").convert("RGBA"), dtype=float); W, H = m["cell"]
    get = lambda i: a[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W]
    return m, get

for spec in sys.argv[1:]:
    name, path = spec.split("=")
    m, get = cells(path)
    home = get(m["gestures"][0]["at"]); al = home[..., 3] > 128
    ys = np.nonzero(al.any(1))[0]; cut = int(ys.min() + 0.65 * (ys.max() - ys.min()))
    def pm(f): return np.dstack([f[..., :3] * f[..., 3:4] / 255, f[..., 3:4]])
    st, co, se, mo = [], [], [], []
    for g in m["gestures"]:
        f0 = get(g["at"]); se += [np.abs(pm(f0) - pm(home)).mean(), np.abs(pm(get(g["at"] + g["frames"] - 1)) - pm(home)).mean()]
        mc0 = f0[f0[..., 3] > 128][:, :3].mean(0); mx = 0
        for k in range(g["frames"]):
            f = get(g["at"] + k)
            st.append(np.abs(pm(f)[cut:] - pm(f0)[cut:]).mean())
            co.append(np.sqrt(((f[f[..., 3] > 128][:, :3].mean(0) - mc0) ** 2).sum()))
            mx = max(mx, np.abs(pm(f)[:cut] - pm(f0)[:cut]).mean())
        mo.append(mx)
    print(f"{name:14s} static {max(st):5.2f}   colour {max(co):5.2f}   seam {max(se):5.2f}   motion {np.mean(mo):5.2f}   ({len(m['gestures'])} gestures)")
