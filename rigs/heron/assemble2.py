#!/usr/bin/env python3
"""Heron, round 2: every sheet is SELF-CONTAINED (base null) — a frame is drawn alone, never over the home picture,
because the page paints base + crop with source-over and no clear: wherever a frame is less opaque than home (a head
that moved away, a soft edge) the home showed through as a second hat/beak. crop = union of every frame's alpha bbox.
Sheets: idle (cutout), sig (MiniMax idle moves), joy, strum (cycle, in, down, up) — strum frames colour-matched to home.
usage: assemble2.py WORK_DIR OUT_DIR"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

WK, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
PREFIX = "art/pory-roku/"

def atlas(d):
    m = json.load(open(f"{WK}/{d}/atlas.json")); a = np.asarray(Image.open(f"{WK}/{d}/atlas.png").convert("RGBA"))
    W, H = m["cell"]
    return m, (lambda i: a[(i // m["cols"]) * H:(i // m["cols"] + 1) * H, (i % m["cols"]) * W:(i % m["cols"] + 1) * W].copy())

cm, cget = atlas("cutout"); HOME = cget(0); W, H = cm["cell"]; PIV = [186, 460]
def g_of(m, n): return next(g for g in m["gestures"] if g["name"] == n)

def clean(f):
    a = f[..., 3] > 24; lab, n = ndi.label(ndi.binary_dilation(a, iterations=2))
    if n > 1:
        sz = ndi.sum(a, lab, range(1, n + 1)); f = f.copy(); f[lab != (np.argmax(sz) + 1)] = 0
    return f

def trim(fr, eps=0.3):
    fr = list(fr)
    while len(fr) > 3 and np.abs(fr[1].astype(float) - HOME).mean() < eps: fr.pop(1)
    while len(fr) > 3 and np.abs(fr[-2].astype(float) - HOME).mean() < eps: fr.pop(-2)
    return fr

# home's own wing grey in the strumming area: the target the clip's wing is matched to
BOX = np.zeros((H, W), bool); BOX[150:330, 110:330] = True
def greyish(px, lim): return (px.max(-1) - px.min(-1) < lim) & (px.mean(-1) > 45)
hb = HOME[BOX & (HOME[..., 3] > 250)][:, :3].astype(float); TARGET = hb[greyish(hb, 40)].mean(0)

def colour_match(f):
    """the clip drew the strumming wing warm brown against home's cool grey: on the pixels that came from the clip
    (differ from home), weighted by how grey they are (the ukulele's brown stays), apply the gain that brings their
    grey mean to home's; capped at +-20 %."""
    f = f.astype(float); mv = BOX & (np.abs(f - HOME).max(2) > 12) & (f[..., 3] > 200)
    px = f[mv][:, :3]; sel = px[greyish(px, 60)]
    if len(sel) < 200: return f.astype(np.uint8)
    g = np.clip(TARGET / sel.mean(0), 0.8, 1.2)
    sat = f[..., :3].max(2) - f[..., :3].min(2); w = np.clip((70 - sat) / 30, 0, 1) * ndi.gaussian_filter(mv.astype(float), 1.5)
    f[..., :3] = np.clip(f[..., :3] * (1 + (g - 1) * w[..., None]), 0, 255)
    return np.round(f).astype(np.uint8)

def pack(name, frames, q):
    al = np.zeros((H, W), bool)
    for f in frames: al |= f[..., 3] > 0
    ys, xs = np.nonzero(al); x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2); x1, y1 = min(W, xs.max() + 3), min(H, ys.max() + 3)
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1); cw, ch = x1 - x0, y1 - y0; G = 4; pw, ph = cw + 2 * G, ch + 2 * G
    cols = 4096 // pw; rows = min(4096 // ph, int(16.0e6 // (cols * pw * ph))); per = cols * rows
    pages, prow = [], []
    for p in range(0, len(frames), per):
        chunk = frames[p:p + per]; r = (len(chunk) + cols - 1) // cols
        pg = np.zeros((r * ph, cols * pw, 4), np.uint8)
        for i, f in enumerate(chunk):
            X, Y = (i % cols) * pw, (i // cols) * ph; pg[Y:Y + ph, X:X + pw] = np.pad(f[y0:y1, x0:x1], ((G, G), (G, G), (0, 0)), mode="edge")
        fn = f"heron-{name}-p{len(pages)}.webp"
        Image.fromarray(pg).save(f"{OUT}/{fn}", "WEBP", quality=q, method=6, alpha_quality=90); pages.append(PREFIX + fn); prow.append(r)
    for f in frames:
        o = f.copy(); o[y0:y1, x0:x1] = 0; assert not o[..., 3].any(), "alpha outside the crop"
    return {"base": None, "pages": pages, "pageRows": prow, "crop": [int(x0), int(y0), int(cw), int(ch)], "gutter": G, "cols": cols,
            "perPage": per, "cell": [W, H], "pivot": PIV, "fps": 12}

def seq(rows):
    frames, out = [], {}
    for n, fr in rows: out[n] = {"at": len(frames), "frames": len(fr)}; frames += fr
    return frames, out

# ---- idle (cutout)
cut = [(n, [cget(g_of(cm, n)["at"] + k) for k in range(g_of(cm, n)["frames"])]) for n in ["blink", "breath", "tilt", "sway"]]
fr_i, at_i = seq(cut)
# ---- sig (MiniMax)
def mm(d, n, idx=None):
    m, get = atlas(d); g = g_of(m, n); ks = idx if idx is not None else range(g["frames"])
    return [clean(get(g["at"] + k)) for k in ks]
sig = []
for d, n in [("lock/A", "listen"), ("lock/A", "lookup"), ("lock/C1", "hat")]:
    fr = mm(d, n); fr[0] = HOME.copy(); fr[-1] = HOME.copy(); sig.append((n, trim(fr)))
fr_s, at_s = seq(sig)
# ---- joy
j = mm("lock/joy1", "joy"); j[0] = HOME.copy(); j[-1] = HOME.copy(); fr_j, at_j = seq([("joy", trim(j))])
# ---- strum: chained clip, 24 fps source indices
cyc = [55, 58, 61, 64, 67, 71, 75, 72, 68, 64, 60, 57]
inn = list(range(14, 54, 3))
DOWN = [55, 60, 67, 75]; UP = DOWN[::-1]
src = sorted(set(cyc + inn + DOWN)); got = dict(zip(src, [colour_match(f) for f in mm("lock/chain", "chain", src)]))
infr = [got[i] for i in inn]; infr[0] = HOME.copy()
fr_t, at_t = seq([("cycle", [got[i] for i in cyc]), ("in", infr), ("down", [got[i] for i in DOWN]), ("up", [got[i] for i in UP])])

Q = {"idle": 58, "sig": 58, "joy": 55, "strum": 68}
man = {"home": PREFIX + "heron-home.webp", "cell": [W, H], "pivot": PIV, "fps": 12}
st = pack("strum", fr_t, Q["strum"])
st.update({"at": at_t["cycle"]["at"], "frames": at_t["cycle"]["frames"], "hit": 1,
           "in": at_t["in"], "down": dict(at_t["down"], hit=1), "up": dict(at_t["up"], hit=2),
           "top": at_t["down"]["at"], "bottom": at_t["down"]["at"] + 3})
man["strum"] = st
idle = pack("idle", fr_i, Q["idle"])
W8 = {"blink": 3, "breath": 3, "tilt": 2, "sway": 2, "listen": 1, "lookup": 1, "hat": 1}
idle["gestures"] = [dict(name=n, sheet="idle", weight=W8[n], src="cutout", **at_i[n]) for n, _ in cut] + \
                   [dict(name=n, sheet="sig", weight=W8[n], src="minimax", sig=True, **at_s[n]) for n, _ in sig]
man["idle"] = idle
man["sig"] = pack("sig", fr_s, Q["sig"])
jo = pack("joy", fr_j, Q["joy"]); jo.update({"at": 0, "frames": at_j["joy"]["frames"], "gestures": [dict(name="joy", sheet="joy", src="minimax", **at_j["joy"])]})
man["joy"] = jo
Image.fromarray(HOME).save(f"{OUT}/heron-home.webp", "WEBP", quality=90, method=6, alpha_quality=100)
json.dump(man, open(f"{OUT}/heron.json", "w"), indent=1)
for k, fr in [("strum", fr_t), ("idle", fr_i), ("sig", fr_s), ("joy", fr_j)]:
    np.save(f"{WK}/truth-{k}.npy", np.stack(fr))
print(json.dumps({k: (v.get("crop"), len(v.get("pages", []))) for k, v in man.items() if isinstance(v, dict)}))
