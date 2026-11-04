#!/usr/bin/env python3
"""Małpka Kiwajka (UkuZiom, „Proste bicia”): a small cutout idle on her one finished picture.

The picture (refs/ukuziom/kiwajka-cut.png, cut at native size from the 8-mascot sheet that the shipped
monkey.webp was cut from) is bent by three smooth weight maps defined on the picture itself:
  arm   the raised forearm and hand, rotating about the elbow (the wave)
  tail  the curled tail, rotating about its root behind the hip
  head  the head with its ears, tilting about the chin (the raised hand excluded)
plus one overlay, the closed eyes from a single-change Nano Banana edit (refs/cutout/kiwajka/blink.png).
Inverse warp by fixed-point iteration on the SOURCE weights, so a pixel with weight 0 samples itself exactly
(feet, legs, belly and the other arm are the picture's own pixels in every frame).

Each frame is rendered at the picture's size, resampled into the shipped cell (230 x 256) by the similarity
fitted to monkey.webp, and REBASED: wherever the frame equals the rendered rest frame, the shipped
monkey.webp's own pixel is used, so every gesture's first and last frame IS the shipped picture.

usage: rig.py OUTDIR [--webp Q]     (run from the sprite-refs root)
writes OUTDIR/kiwajka-idle.webp (one atlas, a grid of 230x256 cells), kiwajka-idle.json (manifest),
       OUTDIR/frames/*.png, OUTDIR/strip-<gesture>.png (review), check.json"""
import argparse, json, math, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--webp", type=int, default=82)
ap.add_argument("--home", default=None, help="the shipped home picture (monkey.webp)")
A = ap.parse_args()
os.makedirs(os.path.join(A.out, "frames"), exist_ok=True)
SR = os.getcwd()
cut = np.asarray(Image.open(SR + "/refs/ukuziom/kiwajka-cut.png").convert("RGBA")).astype(np.float32)
H, W = cut.shape[:2]
HOME = A.home or SR + "/sheets/assets/ukuziom-cards/monkey.webp"
home = np.asarray(Image.open(HOME).convert("RGBA")).astype(np.float32)
CH, CW = home.shape[:2]
FPS = 12

# ---- the closed-eyes overlay: register the edit, keep only what changed around the eyes ----
ed = Image.open(SR + "/refs/cutout/kiwajka/blink.png").convert("RGB")
OX, OY = 81, 45                                       # where the cut sits on the 760 magenta reference
def place_edit(s, dx, dy):
    im = ed.resize((round(1024 * s), round(1024 * s)), Image.LANCZOS)
    can = Image.new("RGB", (W, H)); can.paste(im, (round(-OX + dx), round(-OY + dy)))
    return np.asarray(can).astype(np.float32)
best = None
FACE = (slice(90, 330), slice(140, 460))
for ds in (-0.006, -0.003, 0, 0.003, 0.006):
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            e = place_edit(760 / 1024 * (1 + ds), dx, dy)
            # fit on the lower face (mouth, nose, cheeks) which the edit must not change
            err = np.abs(e[240:320, 200:420] - cut[240:320, 200:420, :3]).mean()
            if best is None or err < best[0]: best = (err, ds, dx, dy)
err, ds, dx, dy = best
edr = place_edit(760 / 1024 * (1 + ds), dx, dy)
diff = np.abs(edr - cut[..., :3]).max(2)
eyes = np.zeros((H, W), bool); eyes[120:250, 205:440] = True     # both eyes and the brows above them
chg = (diff > 28) & eyes & (cut[..., 3] > 250)
chg = ndi.binary_closing(chg, iterations=3); chg = ndi.binary_fill_holes(chg)
chg = ndi.binary_dilation(chg, iterations=4)
a_ov = ndi.gaussian_filter(chg.astype(np.float32), 2.0) * eyes * (cut[..., 3] / 255)
blink = cut.copy(); blink[..., :3] = edr
print("blink fit L1 %.2f at ds=%s dx=%d dy=%d, overlay px %d" % (err, ds, dx, dy, int(chg.sum())))

# pad the picture so a hand or a tail swung outwards is not cut at its edge; X, Y stay picture coordinates
P = 80
cut = np.pad(cut, ((P, P), (P, P), (0, 0))); blink = np.pad(blink, ((P, P), (P, P), (0, 0))); a_ov = np.pad(a_ov, P)
H, W = cut.shape[:2]
Y, X = (np.mgrid[0:H, 0:W] - P).astype(np.float32)
def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ---- weights (picture coordinates, 598 x 669) ----
# the raised arm swings a little from the shoulder, the hand waves from the wrist; the ear beside the hand stays
SH = np.array([395.0, 345.0]); WR = np.array([522.0, 262.0])
v = (WR - SH) / np.linalg.norm(WR - SH); vn = np.array([-v[1], v[0]])
pua = (X - SH[0]) * v[0] + (Y - SH[1]) * v[1]; pna = (X - SH[0]) * vn[0] + (Y - SH[1]) * vn[1]
not_ear = 1 - (1 - ss(474, 476, X)) * (1 - ss(228, 236, Y))
w_arm = ss(10, 60, pua) * np.maximum(ss(-40, -30, pna), ss(120, 140, pua)) * not_ear
uh = np.array([0.2, -0.98]); uh /= np.linalg.norm(uh)
w_hand = ss(-8, 12, (X - WR[0]) * uh[0] + (Y - WR[1]) * uh[1]) * not_ear * ss(474, 476, X)
TP = np.array([132.0, 486.0])                        # tail root, behind the hip
dt = np.hypot(X - TP[0], Y - TP[1])
tm = ((((X < 100) & (Y > 262)) | ((X < 165) & (Y > 276))) & (Y < 380)) | ((X < 150 - (Y - 380) * 0.35) & (Y >= 380) & (Y < 505))   # the ear's bottom sits on the tail's top
w_tail = ss(25, 120, dt) * ndi.gaussian_filter(tm.astype(np.float32), 1.5) * ss(10, 95, np.hypot(X - 110, Y - 272))   # bends to rest where it meets the ear
CHIN = np.array([300.0, 330.0])                      # head tilts about the chin
eh = ((X - 285) / 232) ** 2 + ((Y - 180) / 180) ** 2
w_head = (1 - ss(0.92, 1.2, eh)) * (1 - ss(285, 325, Y))
# keep the whole raised arm out of the head (it stands beside the cheek)
A0, A1 = np.array([380.0, 345.0]), np.array([560.0, 180.0])
d = A1 - A0; tseg = np.clip(((X - A0[0]) * d[0] + (Y - A0[1]) * d[1]) / (d @ d), 0, 1)
dseg = np.hypot(X - (A0[0] + tseg * d[0]), Y - (A0[1] + tseg * d[1]))
w_head *= np.maximum(ss(30, 55, dseg), 1 - ss(222, 245, Y))   # the ear above the hand tilts whole
w_head *= 1 - ss(474, 477, X)                                  # ...but never the thumb beside it
for n, wmap in [("arm", w_arm), ("hand", w_hand), ("tail", w_tail), ("head", w_head)]:
    Image.fromarray((wmap * 255).astype(np.uint8)).save(os.path.join(A.out, f"w_{n}.png"))


# ---- gestures: keyframes, smoothstep between keys ----
G = [
  {"name": "wave", "dur": 1.75, "sig": True, "weight": 1, "tracks": {
      "arm": [[0, 0], [0.3, 5], [1.35, 5], [1.75, 0]],
      "hand": [[0, 0], [0.25, 16], [0.5, -2], [0.75, 16], [1.0, -2], [1.25, 14], [1.55, 0], [1.75, 0]],
      "head": [[0, 0], [0.3, 1.6], [1.3, 1.6], [1.7, 0], [1.75, 0]]}},
  {"name": "blink", "dur": 0.42, "weight": 3, "tracks": {
      "eyes": [[0, 0], [0.08, 1], [0.25, 1], [0.34, 0], [0.42, 0]]}},
  {"name": "tail", "dur": 1.6, "weight": 2, "tracks": {
      "tail": [[0, 0], [0.32, -6], [0.7, 5], [1.08, -4], [1.4, 0], [1.6, 0]]}},
  {"name": "happy", "dur": 1.9, "weight": 2, "tracks": {
      "head": [[0, 0], [0.45, -4], [1.4, -4], [1.85, 0], [1.9, 0]],
      "eyes": [[0, 0], [0.35, 0], [0.5, 1], [1.3, 1], [1.45, 0], [1.9, 0]],
      "tail": [[0, 0], [0.5, 4], [1.4, 4], [1.85, 0], [1.9, 0]]}},
]
def track(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            x = (t - t0) / (t1 - t0); return v0 + (v1 - v0) * x * x * (3 - 2 * x)
    return keys[-1][1]

PM = lambda a: np.dstack([a[..., :3] * a[..., 3:] / 255, a[..., 3]])
def sample(img, sx, sy):
    out = np.empty(sx.shape + (img.shape[2],), np.float32)
    for c in range(img.shape[2]): out[..., c] = ndi.map_coordinates(img[..., c], [sy, sx], order=1, mode="constant", cval=0)
    return out

def render(p):
    src = cut.copy()
    if p.get("eyes", 0) > 0:
        a = (a_ov * p["eyes"])[..., None]; src[..., :3] = src[..., :3] * (1 - a) + blink[..., :3] * a
    src = PM(src)
    defs = [(w_arm, SH, p.get("arm", 0)), (w_hand, WR, p.get("hand", 0)), (w_tail, TP, p.get("tail", 0)), (w_head, CHIN, p.get("head", 0))]
    defs = [d for d in defs if abs(d[2]) > 1e-6]
    if not defs: return src
    # fixed point: s = p - disp(s), disp from SOURCE weights; start from p
    sx, sy = X.copy(), Y.copy()
    for _ in range(8):
        nx, ny = X.copy(), Y.copy()
        for wmap, c, deg in defs:
            wv = ndi.map_coordinates(wmap, [sy + P, sx + P], order=1, mode="constant", cval=0)
            th = np.radians(deg) * wv
            ox, oy = sx - c[0], sy - c[1]
            dxp = np.cos(th) * ox - np.sin(th) * oy - ox
            dyp = np.sin(th) * ox + np.cos(th) * oy - oy
            nx -= dxp; ny -= dyp
        sx, sy = nx, ny
    out = sample(src, sx + P, sy + P)
    # a destination nothing maps to (the place a part just left) can make the iteration flip between two
    # sources; check the forward map and leave such a pixel empty instead of showing the rest pose there
    fx, fy = sx.copy(), sy.copy()
    for wmap, c, deg in defs:
        wv = ndi.map_coordinates(wmap, [sy + P, sx + P], order=1, mode="constant", cval=0)
        th = np.radians(deg) * wv; ox, oy = sx - c[0], sy - c[1]
        fx += np.cos(th) * ox - np.sin(th) * oy - ox; fy += np.sin(th) * ox + np.cos(th) * oy - oy
    bad = np.hypot(fx - X, fy - Y) > 0.75
    out[bad] = 0
    still = np.ones((H, W), bool)
    for wmap, c, deg in defs: still &= wmap < 1e-4
    still &= ndi.map_coordinates(sum(d[0] for d in defs), [sy + P, sx + P], order=1) < 1e-4
    still &= ~bad
    out[still] = src[still]                          # weight 0 samples itself exactly
    return out

# ---- the picture -> cell similarity, fitted to the shipped home frame ----
def to_cell(pm_img, s, tx, ty, size=None):
    cw, chh = size or (CW, CH)
    Yc, Xc = np.mgrid[0:chh, 0:cw].astype(np.float32)
    # supersample 3x3 for a clean downscale
    acc = np.zeros((chh, cw, 4), np.float32)
    for oy in (-1/3, 0, 1/3):
        for ox in (-1/3, 0, 1/3):
            acc += sample(pm_img, (Xc + ox - tx) / s + P, (Yc + oy - ty) / s + P)
    acc /= 9
    a = acc[..., 3:]; rgb = np.where(a > 0, acc[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    return np.dstack([rgb, a[..., 0]])
rest_pm = PM(cut)
best = None
hy, hx = np.nonzero(home[..., 3] > 128)
s0 = (hy.max() - hy.min()) / (H - 2 * P - 1)                 # the shipped cut has a margin: fit the figure's height
for s in s0 * np.array([0.994, 0.997, 1.0, 1.003, 1.006]):
    for tx in np.arange(-1.5, 1.51, 0.5):
        for ty in np.arange(-1.5, 1.51, 0.5):
            c = to_cell(rest_pm, s, hx.min() + tx, hy.min() + ty)
            e = np.abs(c[..., 3] - home[..., 3]).mean() + np.abs((c[..., :3] - home[..., :3]) * (home[..., 3:] > 200)).mean()
            if best is None or e < best[0]: best = (e, s, hx.min() + tx, hy.min() + ty)
e, S, TX, TY = best
print("home fit: err %.2f scale %.4f t (%.2f, %.2f)" % (e, S, TX, TY))
# the shipped cell grows by a margin (the figure keeps its place: the page draws the cell that much past the box)
ML, MT, MR, MB = 16, 12, 30, 0
CW2, CH2 = CW + ML + MR, CH + MT + MB
homeS = home
home = np.zeros((CH2, CW2, 4), np.float32); home[MT:MT + CH, ML:ML + CW] = homeS
CW, CH = CW2, CH2; TX += ML; TY += MT
REST = to_cell(rest_pm, S, TX, TY)

def rebase(cell):
    """where the frame equals the rendered rest, take the shipped home's own pixel"""
    dd = np.abs(cell - REST).max(2)
    m = ndi.binary_dilation(dd > 3, iterations=2)          # grown, so no outline of the rest pose is left behind
    m = np.clip(ndi.gaussian_filter(m.astype(np.float32), 0.7) * 2, 0, 1)[..., None]
    return home * (1 - m) + cell * m

frames, man = [], []
for g in G:
    n = max(2, round(g["dur"] * FPS) + 1)
    at = len(frames)
    for i in range(n):
        t = g["dur"] * i / (n - 1)
        p = {ch: track(k, t) for ch, k in g["tracks"].items()}
        cell = home.copy() if i in (0, n - 1) else rebase(to_cell(render(p), S, TX, TY))
        cell = np.clip(cell + 0.5, 0, 255).astype(np.uint8)
        frames.append(cell)
        Image.fromarray(cell, "RGBA").save(os.path.join(A.out, "frames", f"{g['name']}_{i:02d}.png"))
    man.append({"name": g["name"], "at": at, "frames": n, "weight": g["weight"], "sig": bool(g.get("sig"))})

# ---- atlas: frame 0 is the home itself, then every gesture; a grid at most 8 cells wide ----
allf = [np.clip(home + 0.5, 0, 255).astype(np.uint8)] + frames
for f in allf: f[f[..., 3] < 6] = 0                  # the cut's faint keying haze: invisible, and bytes in every cell
for m in man: m["at"] += 1
uniq, idx = [], []
for f in allf:
    j = next((k for k, u_ in enumerate(uniq) if np.array_equal(u_, f)), -1)
    if j < 0: uniq.append(f); j = len(uniq) - 1
    idx.append(j)
for m in man: m["seq"] = idx[m["at"]:m["at"] + m["frames"]]
cols = 8; rows = math.ceil(len(uniq) / cols)
atlas = Image.new("RGBA", (cols * CW, rows * CH), (0, 0, 0, 0))
for k, f in enumerate(uniq): atlas.paste(Image.fromarray(f, "RGBA"), ((k % cols) * CW, (k // cols) * CH))
atlas.save(os.path.join(A.out, "kiwajka-idle.png"))
atlas.save(os.path.join(A.out, "kiwajka-idle.webp"), quality=A.webp, method=6, alpha_quality=90)
J = {"cell": [CW, CH], "box": [ML, MT, CW - ML - MR, CH - MT - MB], "cols": cols, "count": len(uniq), "fps": FPS, "home": 0,
     "gestures": [{"name": m["name"], "weight": m["weight"], "sig": m["sig"], "seq": m["seq"]} for m in man]}
json.dump(J, open(os.path.join(A.out, "kiwajka-idle.json"), "w"), indent=1)

# ---- checks ----
chk = {"blink_fit": float(err), "home_fit": float(e)}
for m in man:
    a, b = allf[m["at"]].astype(np.float32), allf[m["at"] + m["frames"] - 1].astype(np.float32)
    mid = max(range(m["at"], m["at"] + m["frames"]), key=lambda k: (np.abs(allf[k].astype(np.float32) - allf[0]).max(2) > 40).sum())
    chk[m["name"]] = {"ends_vs_home": float(max(np.abs(a - allf[0]).mean(), np.abs(b - allf[0]).mean())),
                      "peak_frame": mid - m["at"], "peak_changed_px": int((np.abs(allf[mid].astype(np.float32) - allf[0]).max(2) > 40).sum()),
                      "feet_rows_changed": int((np.abs(allf[mid][-40:].astype(np.float32) - allf[0][-40:]).max(2) > 40).sum())}
    strip = Image.new("RGBA", (m["frames"] * CW, CH), (90, 90, 90, 255))
    for i in range(m["frames"]): strip.alpha_composite(Image.fromarray(allf[m["at"] + i], "RGBA"), (i * CW, 0))
    strip.convert("RGB").save(os.path.join(A.out, f"strip-{m['name']}.png"))
json.dump(chk, open(os.path.join(A.out, "check.json"), "w"), indent=1)
print(json.dumps(chk, indent=1)); print("atlas", atlas.size, os.path.getsize(os.path.join(A.out, "kiwajka-idle.webp")), "bytes")
