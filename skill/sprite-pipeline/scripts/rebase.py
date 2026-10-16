#!/usr/bin/env python3
"""Rebase a gesture atlas onto ANOTHER source's home frame, so two sources meet on literally the same pixels.

usage: rebase.py IN_ATLAS.json HOME_ATLAS.json OUT_ATLAS.json [--thr 6] [--grow 2] [--feather 1.5]

A hybrid idle (idle-animation skill) plays gestures from two sources — a cutout sheet and MiniMax clips — on one home
frame. Even placed by the same transform, the two homes differ along the outline (each source keyed its edges its own
way): the Mountain King's averaged 0.9 but 1,600 pixels were off by more than 40 levels, a visible jump at the start and
end of every MiniMax move. So every frame F of IN is rebuilt as: HOME where F equals IN's own home (within --thr), F
where it moved (mask grown --grow px, feathered --feather px) — the first and last frames become HOME exactly."""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser(); ap.add_argument("inp"); ap.add_argument("home"); ap.add_argument("out")
ap.add_argument("--thr", type=float, default=6); ap.add_argument("--grow", type=int, default=2); ap.add_argument("--feather", type=float, default=1.5)
a = ap.parse_args()
def load(p):
    m = json.load(open(p)); return m, np.asarray(Image.open(os.path.splitext(p)[0] + ".png").convert("RGBA"), dtype=float)
m, A = load(a.inp); hm, HA = load(a.home); W, H = m["cell"]
get = lambda arr, mm, i: arr[(i // mm["cols"]) * H:(i // mm["cols"] + 1) * H, (i % mm["cols"]) * W:(i % mm["cols"] + 1) * W]
own, home = get(A, m, 0), get(HA, hm, 0)
n = sum(g["frames"] for g in m["gestures"]); nr = (n + m["cols"] - 1) // m["cols"]
out = np.zeros((nr * H, m["cols"] * W, 4))
for g in m["gestures"]:
    for k in range(g["frames"]):
        i = g["at"] + k; f = get(A, m, i)
        mv = np.abs(f - own).max(2) > a.thr
        mv = ndi.binary_dilation(ndi.binary_opening(mv), iterations=a.grow)
        w = np.clip(ndi.gaussian_filter(mv.astype(float), a.feather), 0, 1)[..., None]
        if k == 0 or k == g["frames"] - 1: w = w * 0           # the ends ARE the shared home
        pa = f[..., 3:4] / 255 * w + home[..., 3:4] / 255 * (1 - w)
        rgb = (f[..., :3] * f[..., 3:4] / 255 * w + home[..., :3] * home[..., 3:4] / 255 * (1 - w)) / np.maximum(pa, 1e-3)
        out[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W] = np.dstack([rgb, pa * 255])
Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8)).save(os.path.splitext(a.out)[0] + ".png")
json.dump({**m, "rows": nr, "rebased_on": a.home}, open(a.out, "w"), indent=1)
print(n, "frames rebased onto", a.home)
