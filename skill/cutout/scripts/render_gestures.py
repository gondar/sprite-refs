#!/usr/bin/env python3
"""Render the gestures of a skinned cutout rig (build_warp_rig.py) into a game atlas.

usage: render_gestures.py RIGDIR OUTDIR [--gestures RIGDIR/gestures.json] [--webp 70]
  (run from the sprites root; the rig's home fit places the reference picture in the game cell)

Per frame: overlays are laid on the figure (rest space) -> the figure is bent by the deformers
(inverse map, chain head -> torso, weights from w_*.png) -> laid over the throne (base) -> resampled into the
cell with the similarity fitted to the shipped home frame. Pixels with weight 0 sample themselves exactly,
so the throne, legs, feet and hands are the same pixels in every frame; a frame whose channels are all at
rest is the rest frame bit for bit. Writes atlas.png/.webp, atlas.json, review.png, frames/<name>_NN.png."""
import argparse, json, os, numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument("rig"); ap.add_argument("out"); ap.add_argument("--gestures")
ap.add_argument("--webp", type=int, default=70); ap.add_argument("--maxw", type=int, default=16383)
A = ap.parse_args()
R = json.load(open(os.path.join(A.rig, "rig.json")))
G = json.load(open(A.gestures or os.path.join(A.rig, "gestures.json")))
W, H = R["size"]
ld = lambda n: np.array(Image.open(os.path.join(A.rig, n)).convert("RGBA")).astype(np.float32)
pm = lambda a: np.dstack([a[..., :3] * a[..., 3:] / 255, a[..., 3]])          # premultiply
base, king = pm(ld(R["layers"]["base"])), pm(ld(R["layers"]["king"]))
WT = {n: np.array(Image.open(os.path.join(A.rig, d["weights"]))).astype(np.float32) / 255 for n, d in R["deformers"].items()}
OV = {}
for n, o in R["overlays"].items():
    a = pm(ld(o["png"])); x, y = o["xy"]; full = np.zeros((H, W, 4), np.float32)
    full[y:y + a.shape[0], x:x + a.shape[1]] = a; OV[n] = full
# region that can move: anything with weight, grown by the largest displacement
moving = sum(WT.values()) > 0
ys, xs = np.nonzero(ndi.binary_dilation(moving, iterations=30))
BY0, BY1, BX0, BX1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

# home placement: cell = s*R(th)*src + t  (fitted by silhouette+colour to the shipped home frame)
hm = R["home"]; fit = json.load(open(hm["fit"]))["src_to_cell"]
CW, CH = hm["cell"]; PIV = hm["pivot"]
s, th, tx, ty = fit


def smooth(u): return u * u * (3 - 2 * u)


def track(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1: return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
    return keys[-1][1]


def params(g, t):
    p = {}
    for ch, keys in g["tracks"].items(): p[ch] = track(keys, t)
    return p


def inv_affine(name, p, X, Y):
    """inverse of: pivot + Rot·Scale·(x - pivot) + (dx,dy), applied to arrays X,Y"""
    px, py = R["deformers"][name]["pivot"]
    r = np.radians(p.get(name + ".rot", 0)); sx = p.get(name + ".sx", 1); sy = p.get(name + ".sy", 1)
    dx = p.get(name + ".dx", 0); dy = p.get(name + ".dy", 0)
    u, v = X - px - dx, Y - py - dy
    c, si = np.cos(r), np.sin(r)
    u, v = c * u + si * v, -si * u + c * v          # R^-1
    return px + u / sx, py + v / sy


def active(name, p):
    return any(abs(p.get(f"{name}.{k}", d) - d) > 1e-9 for k, d in (("rot", 0), ("dx", 0), ("dy", 0), ("sx", 1), ("sy", 1)))


def render_src(p):
    img = king.copy()
    for n in ("smile", "glance", "down", "blink", "drum2", "beard"):
        a = p.get("ov." + n, 0)
        if n in OV and a > 1e-6:
            o = OV[n]; img = img * (1 - a * o[..., 3:] / 255) + a * o
    chain = [n for n in R["chain"] + (["hand"] if "hand" in WT else []) if n in WT and active(n, p)]
    if chain:
        Y, X = np.mgrid[BY0:BY1, BX0:BX1].astype(np.float32)
        qx, qy = X, Y
        # forward order hand -> head -> torso, so undo torso first, then head, then hand
        for n in sorted(chain, key=lambda n: {"torso": 0, "head": 1, "hand": 2}[n]):
            w = ndi.map_coordinates(WT[n], [qy, qx], order=1)
            ix, iy = inv_affine(n, p, qx, qy)
            qx, qy = qx + w * (ix - qx), qy + w * (iy - qy)
        crop = img[BY0:BY1, BX0:BX1]
        same = (qx == X) & (qy == Y)
        warped = np.stack([ndi.map_coordinates(img[..., c], [qy, qx], order=1, mode="constant", cval=0) for c in range(4)], -1)
        warped[same] = crop[same]
        img = img.copy(); img[BY0:BY1, BX0:BX1] = warped
    out = img + base * (1 - img[..., 3:] / 255)
    return out


PAD = 40
def to_cell(src_pm):
    """resample the source-space frame into the game cell: premultiplied LANCZOS through a box, then a tiny
    rotation (the fit's th) is ignored on purpose — it is 0.09 degrees, under a pixel at the cell's edges."""
    a = np.zeros((H + 2 * PAD, W + 2 * PAD, 4), np.float32); a[PAD:-PAD, PAD:-PAD] = src_pm
    im = Image.frombytes("RGBa", (a.shape[1], a.shape[0]), np.round(np.clip(a, 0, 255)).astype(np.uint8).tobytes())
    box = ((0 - tx) / s + PAD, (0 - ty) / s + PAD, (CW - tx) / s + PAD, (CH - ty) / s + PAD)
    return im.resize((CW, CH), Image.LANCZOS, box=box).convert("RGBA")


os.makedirs(os.path.join(A.out, "frames"), exist_ok=True)
fps = G["fps"]
rest = to_cell(render_src({}))
rest.save(os.path.join(A.out, "rest.png"))
frames, gs = [], []
for g in G["gestures"]:
    n = int(round(g["dur"] * fps)) + 1
    gs.append({"name": g["name"], "at": len(frames), "frames": n, "src": "cutout"})
    for i in range(n):
        if i == 0 or i == n - 1: f = rest.copy()        # the shared home frame, exactly
        else: f = to_cell(render_src(params(g, i / fps)))
        f.save(os.path.join(A.out, "frames", f"{g['name']}_{i:02d}.png")); frames.append(f)
    print(f"{g['name']}: {n} frames ({g['dur']} s)")

cols = A.maxw // CW; rows = (len(frames) + cols - 1) // cols
atlas = Image.new("RGBA", (cols * CW, rows * CH), (0, 0, 0, 0))
for i, f in enumerate(frames): atlas.paste(f, ((i % cols) * CW, (i // cols) * CH))
atlas.save(os.path.join(A.out, "atlas.png"), optimize=True)
atlas.save(os.path.join(A.out, "atlas.webp"), quality=A.webp, method=6, alpha_quality=90)
meta = {"cell": [CW, CH], "pivot": PIV, "fps": fps, "cols": cols, "rows": rows, "gestures": gs}
json.dump(meta, open(os.path.join(A.out, "atlas.json"), "w"), indent=1)

# review: 8 evenly spaced frames per gesture, 200 px wide each, on a mid-grey
tw = 200; thh = int(round(CH * tw / CW)); lab = 90
rv = Image.new("RGB", (lab + 8 * tw, len(gs) * thh), (96, 96, 96))
from PIL import ImageDraw
dr = ImageDraw.Draw(rv)
for r, g in enumerate(gs):
    dr.text((6, r * thh + thh // 2), g["name"], fill=(255, 255, 255))
    for k in range(8):
        i = g["at"] + round(k * (g["frames"] - 1) / 7)
        t_ = frames[i].resize((tw, thh), Image.LANCZOS); bg = Image.new("RGBA", t_.size, (96, 96, 96, 255)); bg.alpha_composite(t_)
        rv.paste(bg.convert("RGB"), (lab + k * tw, r * thh))
rv.save(os.path.join(A.out, "review.png"))
print(json.dumps({k: meta[k] for k in ("cell", "cols", "rows")}), len(frames), "frames",
      os.path.getsize(os.path.join(A.out, "atlas.webp")) // 1024, "KB webp")

# ---- self-check: static stability + seams ----
def to_cell_mask(m):
    a = np.dstack([m * 255.0] * 4).astype(np.float32)
    return np.array(to_cell(a))[..., 3] / 255.0
kingA = king[..., 3] > 0
head_zone = ndi.binary_dilation(WT["head"] > 0.01, iterations=20)
throne_only = (base[..., 3] > 0) & ~kingA & ~head_zone
backrest = throne_only & (np.mgrid[0:H, 0:W][0] < 690)        # the throne's back (above the armrests)
armrests = throne_only & ~backrest
fa = np.array(rest)[..., 3] > 128; ys_ = np.nonzero(fa)[0]; fy0, fy1 = ys_.min(), ys_.max()
bottom = np.zeros((CH, CW), bool); bottom[int(fy1 - 0.28 * (fy1 - fy0)):, :] = True; bottom &= ndi.binary_dilation(fa, iterations=2)
thr = to_cell_mask(backrest) > 0.99
arm = (to_cell_mask(armrests) > 0.99) & ~bottom
regions = {"bottom28": bottom, "throne_back": thr & ~bottom, "both": bottom | thr, "armrests_info": arm}
rest_a = np.array(rest).astype(float)
check = {}
for g in gs:
    fr = [np.array(frames[g["at"] + i]).astype(float) for i in range(g["frames"])]
    d = {k: max(float(np.abs(f - fr[0])[m].mean()) for f in fr) for k, m in regions.items()}
    d["seam_first"] = float(np.abs(fr[0] - rest_a).mean()); d["seam_last"] = float(np.abs(fr[-1] - rest_a).mean())
    d["max_px_any_static"] = float(max(np.abs(f - fr[0])[regions["both"]].max() for f in fr))
    check[g["name"]] = {k: round(v, 4) for k, v in d.items()}
    print(g["name"], check[g["name"]])
json.dump(check, open(os.path.join(A.out, "check.json"), "w"), indent=1)
