#!/usr/bin/env python3
"""Clean a lock.py atlas cell by cell: drop thin lines and loose pieces from the alpha (the rope H3 drew in the
townsman's hands — the game draws its own rope), keeping the figure and anything of a fair size touching it.

usage: python3 scripts/wintertown_strip_clean.py ATLAS_DIR [--thin 2] [--min 0.03]"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

d = sys.argv[1]; thin = int(sys.argv[sys.argv.index("--thin") + 1]) if "--thin" in sys.argv else 2
least = float(sys.argv[sys.argv.index("--min") + 1]) if "--min" in sys.argv else .03
J = json.load(open(d + "/atlas.json")); CW, CH = J["cell"]
A = np.asarray(Image.open(d + "/atlas.png").convert("RGBA")).copy()
n = sum(g["frames"] for g in J["gestures"])
for i in range(n):
    x, y = (i % J["cols"]) * CW, (i // J["cols"]) * CH
    c = A[y:y + CH, x:x + CW]
    solid = c[..., 3] > 100
    core = ndi.binary_opening(solid, iterations=thin)                 # a rope a few px thick is gone
    lab, k = ndi.label(core)
    if not k: continue
    sizes = ndi.sum(core, lab, range(1, k + 1)); keep = np.isin(lab, 1 + np.nonzero(sizes >= least * sizes.max())[0])
    m = ndi.binary_dilation(keep, iterations=thin + 1) & (c[..., 3] > 0)
    m = ndi.gaussian_filter(m.astype(float), .7)
    c[..., 3] = (c[..., 3] * np.clip(m * 1.4, 0, 1)).astype(np.uint8)
Image.fromarray(A).save(d + "/atlas-clean.png")
print("cleaned", n, "cells")
