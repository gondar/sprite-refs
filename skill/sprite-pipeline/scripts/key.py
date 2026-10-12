#!/usr/bin/env python3
"""Chroma-key a flat magenta (or green) background to RGBA, with despill and a soft edge.

usage: key.py IN.png OUT.png [--key magenta|green|auto] [--lo 40] [--hi 120] [--check CHECK.png]

How it works. For magenta the "key excess" of a pixel is min(R,B) - G: 255 on pure #FF00FF, around 0 or
negative on orange fur, cream, olive cloth, brown — and also ~0 on PALE PINK (255,200,200), because pink
has G close to B. That is why inner ears survive a magenta key. For green the excess is G - max(R,B).
alpha = 1 below --lo, 0 above --hi, linear in between (soft edge). Despill: wherever excess > 0 the key
channels are pulled down by the excess, so the fringe loses its magenta cast instead of glowing.
--key auto reads the background from the image border.
--check writes the result over a checkerboard and over black, to inspect the edge."""
import argparse, numpy as np
from PIL import Image


def excess(rgb, key):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return np.minimum(r, b) - g if key == "magenta" else g - np.maximum(r, b)


def detect(rgb):
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    r, g, b = np.median(border, 0)
    return "green" if g > max(r, b) else "magenta"


def key_border(rgb, lo=40, hi=120):
    """Any flat background, even one that changes from frame to frame (H3 cycled a 'flat magenta' through the
    rainbow in first+last-frame mode): the key colour is the median of this frame's border, alpha is the RGB
    distance from it, and edge pixels are un-mixed — out = (pix - (1-a)·bg) / a — so no fringe of any hue."""
    border = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
    bg = np.median(border, 0)
    d = np.sqrt(((rgb - bg) ** 2).sum(2))
    al = np.clip((d - lo) / (hi - lo), 0, 1)
    a3 = np.maximum(al, 1e-3)[..., None]
    out = np.clip((rgb - (1 - al)[..., None] * bg) / a3, 0, 255)
    return np.dstack([out, al * 255])


def key_image(rgb, key="auto", lo=40, hi=120):
    rgb = rgb.astype(np.float64)
    if key == "border": return key_border(rgb, lo, hi), "border"
    if key == "auto": key = detect(rgb)
    ex = excess(rgb, key)
    al = np.clip((hi - ex) / (hi - lo), 0, 1)
    out = rgb.copy()
    sp = np.clip(ex, 0, None)
    if key == "magenta":
        out[..., 0] -= sp; out[..., 2] -= sp
    else:
        out[..., 1] -= sp
    out = np.clip(out, 0, 255)
    return np.dstack([out, al * 255]), key


def checker(rgba, path):
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    chk = np.where(((yy // 16 + xx // 16) % 2)[..., None] == 1, 200.0, 255.0) * np.ones(3)
    a = rgba[..., 3:4] / 255
    left = rgba[..., :3] * a + chk * (1 - a)
    right = rgba[..., :3] * a
    Image.fromarray(np.concatenate([left, right], 1).astype(np.uint8)).save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--key", default="auto"); ap.add_argument("--lo", type=float, default=40)
    ap.add_argument("--hi", type=float, default=120); ap.add_argument("--check")
    a = ap.parse_args()
    rgba, k = key_image(np.array(Image.open(a.inp).convert("RGB")), a.key, a.lo, a.hi)
    Image.fromarray(np.round(rgba).astype(np.uint8)).save(a.out)
    if a.check: checker(rgba, a.check)
    print(f"keyed {a.inp} on {k}")
