#!/usr/bin/env python3
"""Build a SKINNED cutout rig from one finished picture + Nano Banana edits of it (the Mountain King way).

Why not rigid pieces: a seated, front-view, chunky figure has no clean joints (the beard covers the neck, the
belly covers the hips, the hands rest on the throne). Rigid pieces open gaps or show "double backs" at every
seam. Here the figure is ONE layer bent by smooth weight maps (like Spine/Live2D skinning), so seams cannot open,
and everything with weight 0 (throne, legs, feet, hands) is copied pixel-for-pixel in every frame.

Layers (all in reference-picture pixels):
  base.png    the throne alone: the reference outside the figure, and inside it the "King removed" edit
              (registered) — only ever seen in the thin slivers the head/torso uncover when they move
  king.png    the figure (parts map != throne), cut from the reference with a hard mask (so rest == reference)
  ov_*.png    face/hand overlays: only the pixels an edit changed (registered, masked, feathered)
  w_*.png     weight maps of the deformers (8-bit), pivots in rig.json

usage: build_warp_rig.py SPEC.json OUTDIR      (run from the sprites root)"""
import json, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import key
from register import warp_to_ref

S = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
rgb = lambda p: np.array(Image.open(p).convert("RGB")).astype(float)
src = rgb(S["ref"]); H, W = src.shape[:2]
ref, _ = key.key_image(src, S["key"])
REG = json.load(open(S["edits"]))
edir = os.path.dirname(S["edits"])


def edit(name):
    e = rgb(os.path.join(edir, name + ".png"))
    w = warp_to_ref(e, REG[name], (H, W))
    k, _ = key.key_image(w, S["key"])
    return k


# --- parts map ---
sg = S["seg"]; seg = warp_to_ref(rgb(sg["path"]), sg["reg"], (H, W), order=0)
names = list(sg["colors"]); C = np.array([sg["colors"][n] for n in names], float)
lab = ((seg[:, :, None, :] - C[None, None]) ** 2).sum(3).argmin(2)
sil = ref[..., 3] > 128; bgi = names.index("bg")
fix = sil & (lab == bgi)
if fix.any():
    _, (iy, ix) = ndi.distance_transform_edt(lab == bgi, return_indices=True); lab[fix] = lab[iy[fix], ix[fix]]
part = {n: lab == i for i, n in enumerate(names)}
king = np.zeros((H, W), bool)
for n in names:
    if n not in ("throne", "bg"): king |= part[n]
king = ndi.binary_fill_holes(ndi.binary_closing(king, iterations=2))
king = ndi.binary_dilation(king, iterations=2) & (ref[..., 3] > 0)

# --- layers ---
def save(name, a):
    Image.fromarray(np.round(np.clip(a, 0, 255)).astype(np.uint8)).save(os.path.join(out, name))

king_l = ref.copy(); king_l[..., 3] *= king
under = edit(S["under"])
inside = ndi.binary_dilation(king, iterations=4)
base = ref.copy(); base[inside] = under[inside]
save("king.png", king_l); save("base.png", base)

# --- deformer weights ---
yy, xx = np.mgrid[0:H, 0:W].astype(float)
ss = lambda e0, e1, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - e0) / (e1 - e0), 0, 1))
D = S["deformers"]; weights = {}
t = D["torso"]
wT = ss(t["y_zero"], t["y_full"], yy)                       # 1 above the chest, 0 at the hips
arms = part["armL"] | part["armR"]
dist_torso = ndi.distance_transform_edt(~(part["torso"] | part["head"]))
wT = np.where(arms, wT * np.clip(1 - dist_torso / t["arm_falloff"], 0, 1), wT)   # hands stay on the armrests
wT = ndi.gaussian_filter(wT * king, t["blur"])
wT[yy >= t["y_zero"]] = 0; wT[part["legs"]] = 0
wT *= ndi.gaussian_filter(np.clip(1 - dist_torso / t["arm_falloff"], 0, 1), 4)   # fades out along the arms: 0 at the hands
weights["torso"] = wT
h = D["head"]
# weight 1 over the WHOLE head incl. thin crown spikes (a blurred mask falls off inside thin parts and bends them):
# blur a grown head mask, so the fall-off happens outside the head, in the shoulders / backrest
wH = ndi.gaussian_filter(ndi.binary_dilation(part["head"], iterations=h.get("grow", 24)).astype(float), h["blur"])
wH = np.clip((wH - 0.15) / 0.6, 0, 1) * (1 - (1 - h["beard_keep"]) * ss(h["beard_y"][0], h["beard_y"][1], yy))
wH[yy >= t["y_zero"]] = 0
weights["head"] = wH

# --- overlays ---
ovs = {}
for n, o in S["overlays"].items():
    f = edit(n)
    within = np.zeros((H, W), bool)
    for q in o["within"]: within |= part[q]
    if o.get("grow_within"): within = ndi.binary_dilation(within, iterations=o["grow_within"])
    x0, y0, x1, y1 = o["box"]; box = np.zeros((H, W), bool); box[y0:y1, x0:x1] = True
    d = np.abs(ndi.gaussian_filter(f[..., :3], (1.2, 1.2, 0)) - ndi.gaussian_filter(ref[..., :3], (1.2, 1.2, 0))).max(2)
    da = np.abs(f[..., 3] - ref[..., 3])
    m = ((d > o["thr"]) | (da > 128)) & within & box
    m = ndi.binary_opening(m, iterations=2)
    lab2, k = ndi.label(m)
    if k > 1:
        sz = ndi.sum(m, lab2, range(1, k + 1)); m = np.isin(lab2, 1 + np.nonzero(sz > 0.08 * sz.max())[0])
    m = ndi.binary_fill_holes(ndi.binary_dilation(m, iterations=o["grow"])) & box
    a = np.clip(ndi.gaussian_filter(m.astype(float), o["feather"]) * 1.6 - 0.3, 0, 1)
    a = np.where(f[..., 3] > 128, a, np.where(ref[..., 3] > 128, 0, a))   # never paint outside both silhouettes
    lay = f.copy(); lay[..., 3] = f[..., 3] * a
    ys, xs = np.nonzero(lay[..., 3] > 1)
    bb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    save(f"ov_{n}.png", lay[bb[1]:bb[3], bb[0]:bb[2]])
    ovs[n] = {"png": f"ov_{n}.png", "xy": bb[:2], "area": int((a > 0.5).sum())}
    if n == D["hand"]["of"]:   # the hand that strokes the beard: the part of the overlay over the head
        hm = m & part["head"]
        weights["hand"] = np.clip(ndi.gaussian_filter(hm.astype(float), D["hand"]["blur"]) * 1.4, 0, 1)

for n, w in weights.items():
    save(f"w_{n}.png", w * 255)

rig = {"size": [W, H], "ref": S["ref"], "layers": {"base": "base.png", "king": "king.png"},
       "deformers": {n: {"weights": f"w_{n}.png", "pivot": D[n]["pivot"]} for n in weights},
       "chain": ["head", "torso"],          # forward order: head bends first, then the torso carries it
       "overlays": ovs, "home": S["home"]}
json.dump(rig, open(os.path.join(out, "rig.json"), "w"), indent=1)

# check sheet: king, base, weights, overlays
def thumb(a, s=0.4):
    im = Image.fromarray(np.round(np.clip(a, 0, 255)).astype(np.uint8))
    if im.mode != "RGBA": im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (60, 60, 60, 255)); bg.alpha_composite(im)
    return bg.convert("RGB").resize((int(W * s), int(H * s)))
tiles = [thumb(king_l), thumb(base)] + [thumb(np.dstack([w * 255] * 3 + [np.full((H, W), 255.)])) for w in weights.values()]
sheet = Image.new("RGB", (sum(t_.width for t_ in tiles), tiles[0].height)); x = 0
for t_ in tiles: sheet.paste(t_, (x, 0)); x += t_.width
sheet.save(os.path.join(out, "check.png"))
print("overlays:", {n: o["area"] for n, o in ovs.items()})
