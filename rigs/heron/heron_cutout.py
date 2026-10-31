#!/usr/bin/env python3
"""Heron (Pory roku) cutout gestures: the home picture bent by weight maps (head+neck, body) plus a blink overlay
cut from one Nano Banana edit. Renders in the 768x768 clip space (the same pixels the H3 clips start from), then
places frames into the game cell with lock.py's transform. usage: heron_cutout.py OUT_DIR --cell W,H --pivot X,Y --fig F"""
import argparse, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

R = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(R, "..", ".."))
CUT = os.path.join(ROOT, "refs/heron/heron-cut.png"); OX, OY = 205, 60; N = 768
# design (1024x1536) -> 768 space
S = 640 / 1388; DX, DY = 132, 75
def d2c(x, y): return ((x - DX) * S + OX, (y - DY) * S + OY)

def smooth(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def track(keys, t):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1: return v0 + (v1 - v0) * smooth((t - t0) / max(t1 - t0, 1e-6))
    return keys[-1][1]

def load():
    cut = np.asarray(Image.open(CUT).convert("RGBA"), dtype=float)
    home = np.zeros((N, N, 4)); home[OY:OY + cut.shape[0], OX:OX + cut.shape[1]] = cut
    return home

def weights(home):
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    _, ytop = d2c(0, 395); _, ybot = d2c(0, 440)          # neck ramps out into the cape collar
    xh0, _ = d2c(300, 0); xh1, _ = d2c(820, 0)
    wh = smooth((ybot - yy) / (ybot - ytop)) * ((xx > xh0) & (xx < xh1))
    wh = ndi.gaussian_filter(wh, 2)
    _, hem = d2c(0, 1300); _, top = d2c(0, 120)
    wb = smooth((hem - yy) / 60.0)                          # body (cape, wings, ukulele, head) above the hem
    return wh, wb, hem

def blink_overlay(home):
    ed = Image.open(os.path.join(ROOT, "refs/cutout/heron/blink.png")).convert("RGB").resize((1024, 1536), Image.LANCZOS)
    orig = np.asarray(Image.open(os.path.join(ROOT, "refs/heron/design/heron-design-v1.png")).convert("RGB"), dtype=float)
    ed = np.asarray(ed, dtype=float)
    ex, ey = 548, 225; r = 60
    best = None
    for sy in range(-14, 15):
        for sx in range(-14, 15):
            a = orig[ey - r:ey + r, ex - r:ex + r]; b = ed[ey - r + sy:ey + r + sy, ex - r + sx:ex + r + sx]
            m = np.ones((2 * r, 2 * r), bool); m[r - 22:r + 22, r - 22:r + 22] = False   # ring around the eye
            e = np.abs(a - b)[m].mean()
            if best is None or e < best[0]: best = (e, sx, sy)
    _, sx, sy = best
    patch = ed[ey - r + sy:ey + r + sy, ex - r + sx:ex + r + sx]
    yy, xx = np.mgrid[-r:r, -r:r]; mask = np.clip((24 - np.hypot(xx, yy * 1.15)) / 8, 0, 1)
    full = orig.copy(); fm = np.zeros(orig.shape[:2]); full[ey - r:ey + r, ex - r:ex + r] = patch; fm[ey - r:ey + r, ex - r:ex + r] = mask
    # into 768 space via the same crop+scale as the cut
    def to768(img, ch):
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB" if ch == 3 else "L").crop((DX, DY, DX + 777, DY + 1404))
        im = im.resize((358, 647), Image.LANCZOS); z = np.zeros((N, N, ch)) if ch == 3 else np.zeros((N, N))
        a = np.asarray(im, dtype=float); z[OY:OY + 647, OX:OX + 358] = a; return z
    rgb = to768(full, 3); m = to768(fm * 255, 1) / 255
    print("blink registered shift", sx, sy, "err", round(best[0], 1))
    return rgb, m * (home[..., 3] / 255)

def warp(img, dx, dy):
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    pm = np.dstack([img[..., :3] * img[..., 3:4] / 255, img[..., 3]])
    out = np.dstack([ndi.map_coordinates(pm[..., c], [yy - dy, xx - dx], order=1, mode="constant") for c in range(4)])
    a = out[..., 3]; rgb = out[..., :3] / np.maximum(a, 1e-3)[..., None] * 255
    return np.dstack([np.clip(rgb, 0, 255), a])

GEST = [
    {"name": "blink", "dur": 0.9, "ch": {"blink": [[0, 0], [0.25, 0], [0.33, 1], [0.5, 1], [0.6, 0], [0.9, 0]]}},
    {"name": "breath", "dur": 2.0, "ch": {"body.sy": [[0, 0], [0.9, 1], [1.2, 1], [2.0, 0]], "head.dy": [[0, 0], [0.9, -1.2], [1.2, -1.2], [2.0, 0]]}},
    {"name": "tilt", "dur": 1.8, "ch": {"head.rot": [[0, 0], [0.5, 4.0], [1.25, 4.0], [1.8, 0]], "head.dy": [[0, 0], [0.5, 1.5], [1.25, 1.5], [1.8, 0]]}},
    {"name": "nod", "dur": 1.5, "ch": {"head.rot": [[0, 0], [0.3, 3], [0.55, 0], [0.85, 3], [1.15, 0], [1.5, 0]], "head.dy": [[0, 0], [0.3, 3], [0.55, 0], [0.85, 3], [1.15, 0], [1.5, 0]]}},
    {"name": "sway", "dur": 2.0, "ch": {"body.rot": [[0, 0], [0.7, 0.9], [1.3, -0.5], [2.0, 0]]}},
    {"name": "dream", "dur": 2.2, "ch": {"head.rot": [[0, 0], [0.6, -3], [1.6, -3], [2.2, 0]], "blink": [[0, 0], [0.55, 0], [0.7, 1], [1.45, 1], [1.6, 0], [2.2, 0]], "body.sy": [[0, 0], [1.0, 1], [2.2, 0]]}},
]

def render(home, wh, wb, hem, blink, g, t):
    v = {k: track(keys, t) for k, keys in g["ch"].items()}
    img = home.copy()
    if v.get("blink", 0) > 0:
        rgb, m = blink; a = (m * v["blink"])[..., None]; img[..., :3] = img[..., :3] * (1 - a) + rgb * a
    yy, xx = np.mgrid[0:N, 0:N].astype(float)
    dx = np.zeros((N, N)); dy = np.zeros((N, N))
    hx, hy = d2c(470, 420)                          # neck base
    th = np.radians(v.get("head.rot", 0)); px, py = xx - hx, yy - hy
    dx += wh * (np.cos(th) * px - np.sin(th) * py - px); dy += wh * (np.sin(th) * px + np.cos(th) * py - py + v.get("head.dy", 0))
    sy = 0.007 * v.get("body.sy", 0); dy += wb * sy * (yy - hem)
    fx, fy = d2c(510, 1460); tb = np.radians(v.get("body.rot", 0)); px, py = xx - fx, yy - fy
    wr = smooth((fy - yy) / (fy - hem + 200))
    dx += wr * (np.cos(tb) * px - np.sin(tb) * py - px); dy += wr * (np.sin(tb) * px + np.cos(tb) * py - py)
    return warp(img, dx, dy) if (np.abs(dx).max() > 1e-3 or np.abs(dy).max() > 1e-3) else img

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--cell", default="400,480"); ap.add_argument("--pivot", default="190,474"); ap.add_argument("--fig", type=float, default=440)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    home = load(); wh, wb, hem = weights(home); blink = blink_overlay(home)
    fig = home[..., 3] > 127; ys, xs = np.nonzero(fig); s = a.fig / (ys.max() - ys.min() + 1); bx, by = (xs.min() + xs.max()) / 2, ys.max()
    CW, CH = map(int, a.cell.split(",")); PX, PY = map(float, a.pivot.split(","))
    aff = (1 / s, 0, bx - PX / s, 0, 1 / s, by - PY / s)
    def place(f): return Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8), "RGBA").transform((CW, CH), Image.AFFINE, aff, Image.BICUBIC)
    frames, gs = [], []
    for g in GEST:
        n = int(round(g["dur"] * 12)) + 1
        seq = [place(home) if k in (0, n - 1) else place(render(home, wh, wb, hem, blink, g, k / 12)) for k in range(n)]
        gs.append({"name": g["name"], "at": len(frames), "frames": n, "src": "cutout"}); frames += seq
    cols = min(len(frames), 16383 // CW); nr = (len(frames) + cols - 1) // cols
    atlas = Image.new("RGBA", (CW * cols, CH * nr))
    for i, f in enumerate(frames): atlas.paste(f, ((i % cols) * CW, (i // cols) * CH))
    atlas.save(os.path.join(a.out, "atlas.png"))
    json.dump({"cell": [CW, CH], "pivot": [PX, PY], "fps": 12, "cols": cols, "rows": nr, "gestures": gs}, open(os.path.join(a.out, "atlas.json"), "w"), indent=1)
    print(len(frames), "frames", gs)

if __name__ == "__main__":
    main()
