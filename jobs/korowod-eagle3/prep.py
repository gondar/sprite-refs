#!/usr/bin/env python3
"""Korowód eagle3: key the three APPROVED pictures (refs/korowod/eagle3/{home,perch,herb}.png, 2048² on #2F6BD8) and
place them on ONE design canvas (S x S, original pixels) with the body centre of each on the same anchor, at one bird
scale (perch is drawn 1.33x bigger: eye-to-beak-tip 266 px vs 200 home / 203 herb -> perch x0.75).
Writes refs/korowod/eagle3/anim/eagle3-<pose>-blue-v1.png (OUT px, flat #2F6BD8, the H3 first/last frames) and
place-<pose>.png (WORK px RGBA, the clean cut-outs on the working canvas the clip frames are keyed into)."""
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/sprite-refs/jobs/korowod-eagle")
from ekey import key

R = "/home/user/sprite-refs/refs/korowod/eagle3"; O = R + "/anim"
S, ANC, OUT, WORK = 2700, (1350, 1400), 1280, 1024
BLUE = (47, 107, 216)
P = {"home": (1.0, (1056, 1248)), "herb": (1.0, (1024, 1056)), "perch": (0.75, (1100, 1000))}
meta = {"S": S, "anchor": ANC, "out": OUT, "work": WORK, "poses": {}}
for n, (sc, (ax, ay)) in P.items():
    rgb = np.asarray(Image.open(f"{R}/{n}.png").convert("RGB"), float)
    k = Image.fromarray(np.round(key(rgb, min_area=2000)).astype(np.uint8), "RGBA")
    if sc != 1: k = k.resize((round(2048 * sc),) * 2, Image.LANCZOS)
    ox, oy = round(ANC[0] - ax * sc), round(ANC[1] - ay * sc)
    big = Image.new("RGBA", (S, S), (0, 0, 0, 0)); big.alpha_composite(k, (ox, oy))
    for side, fn in [(OUT, f"eagle3-{n}-blue-v1.png"), (WORK, f"place-{n}.png")]:
        sm = big.resize((side, side), Image.LANCZOS)
        if side == OUT:
            bg = Image.new("RGBA", (side, side), BLUE + (255,)); bg.alpha_composite(sm); bg.convert("RGB").save(f"{O}/{fn}")
        else: sm.save(f"{O}/{fn}")
    a = np.asarray(big)[..., 3] > 128; ys, xs = np.nonzero(a)
    meta["poses"][n] = {"scale": sc, "offset": [ox, oy], "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}
json.dump(meta, open(f"{O}/place.json", "w"), indent=1); print(json.dumps(meta))
