#!/usr/bin/env python3
"""Assemble the heron's three sheets (strum, idle, joy) from the cutout render and the locked MiniMax clips, all on
ONE home frame (the cutout's frame 0), clean stray specks off the MiniMax frames, write full atlases for score.py and
pages.py. usage: assemble.py WORK_DIR OUT_DIR"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

W_, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)

def atlas(d):
    m = json.load(open(f"{W_}/{d}/atlas.json")); a = np.asarray(Image.open(f"{W_}/{d}/atlas.png").convert("RGBA"))
    W, H = m["cell"]
    return m, (lambda i: a[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W].copy())

cm, cget = atlas("cutout"); HOME = cget(0); W, H = cm["cell"]
def g_of(m, name): return next(g for g in m["gestures"] if g["name"] == name)

def clean(f):
    """drop alpha specks not connected to the figure (MiniMax backdrop grain the key kept)."""
    a = f[..., 3] > 24; lab, n = ndi.label(ndi.binary_dilation(a, iterations=2))
    if n > 1:
        sz = ndi.sum(a, lab, range(1, n + 1)); keep = lab == (np.argmax(sz) + 1)
        f = f.copy(); f[~keep] = 0
    return f

stats = {}
def seam(f): d = np.abs(f.astype(int) - HOME.astype(int)).max(2); return int((d > 40).sum()), float(np.abs(f.astype(float) - HOME).mean())

def mm(d, name, idx=None):
    m, get = atlas(d); g = g_of(m, name); ks = idx if idx is not None else range(g["frames"])
    fr = [clean(get(g["at"] + k)) for k in ks]
    stats[name] = {"first_vs_home": seam(fr[0]), "last_vs_home": seam(fr[-1])}
    return fr

def trim(fr, eps=0.3):
    """drop rest frames at both ends (H3 sits on home for ~0.3 s before it moves and after it lands)."""
    fr = list(fr)
    while len(fr) > 3 and np.abs(fr[1].astype(float) - HOME).mean() < eps: fr.pop(1)
    while len(fr) > 3 and np.abs(fr[-2].astype(float) - HOME).mean() < eps: fr.pop(-2)
    return fr

def write(name, rows, fps=12, home_first=False):
    frames, gs = ([HOME], [{"name": "home", "at": 0, "frames": 1}]) if home_first else ([], [])
    for r in rows:
        gs.append({"name": r["name"], "at": len(frames), "frames": len(r["fr"]), "src": r["src"], **({"sig": True} if r.get("sig") else {})})
        frames += r["fr"]
    cols = min(len(frames), 16383 // W); nr = (len(frames) + cols - 1) // cols
    A = np.zeros((nr * H, cols * W, 4), np.uint8)
    for i, f in enumerate(frames): A[(i // cols) * H:(i // cols + 1) * H, (i % cols) * W:(i % cols + 1) * W] = f
    Image.fromarray(A).save(f"{OUT}/{name}.png")
    json.dump({"cell": [W, H], "pivot": cm["pivot"], "fps": fps, "cols": cols, "rows": nr, "gestures": gs}, open(f"{OUT}/{name}.json", "w"), indent=1)
    return gs

# ---- idle: 4 cutout + 4 MiniMax, every gesture's ends forced onto HOME (MiniMax ends are home already through lock's ease)
idle = []
for n in ["blink", "breath", "tilt", "sway"]:
    g = g_of(cm, n); idle.append({"name": n, "src": "cutout", "fr": [cget(g["at"] + k) for k in range(g["frames"])]})
for d, n in [("lock/A", "listen"), ("lock/A", "lookup"), ("lock/B", "ruffle"), ("lock/C1", "hat")]:
    fr = mm(d, n); fr[0] = HOME.copy(); fr[-1] = HOME.copy(); fr = trim(fr); idle.append({"name": n, "src": "minimax", "sig": True, "fr": fr})
write("idle", idle)

# ---- joy: one MiniMax gesture (flourish with the wing spread, then a deep bow)
fr = mm("lock/joy1", "joy"); fr[0] = HOME.copy(); fr[-1] = HOME.copy(); fr = trim(fr)
write("joy", [{"name": "joy", "src": "minimax", "fr": fr}], home_first=True)

# ---- strum: the chained clip (home -> drawn down-strum pose), cut at 24 fps source frames
DOWN = [55, 58, 61, 64, 67, 71, 75]; UP = [72, 68, 64, 60, 57]
cyc = mm("lock/chain", "chain", DOWN + UP)
inn = mm("lock/chain", "chain", list(range(14, 54, 3)))
inn[0] = HOME.copy()
write("strum", [{"name": "cycle", "src": "minimax", "fr": cyc}, {"name": "in", "src": "minimax", "fr": inn}], home_first=True)
json.dump(stats, open(f"{OUT}/seams.json", "w"), indent=1); print(json.dumps(stats))
