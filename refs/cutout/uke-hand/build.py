#!/usr/bin/env python3
"""Build the UkuZiom Short's left hand on the ukulele neck (film „W grocie Króla Gór”, take zagrasz).

One base painting (base.png, Nano Banana Pro from layout.png + the cast style) and one single-change edit per
pressed note (Nano Banana flash). Each state = the base everywhere except where its edit changed, inside the moving
finger's column, so the neck, the sleeve and the other fingers are the base's pixels in every state.
Then the magenta is keyed out, the right end of the neck fades out, and every state is cropped and scaled the same.

usage: python3 build.py OUTDIR   (from sprite-refs root or anywhere)"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../../skill/cutout/scripts"))
from key import key_border  # noqa: E402

OUT = sys.argv[1]
# state -> (edit file, finger column box x0, x1 in base px)
STATES = {"e1": ("E1b.png", 120, 560), "c1": ("C1c.png", 120, 560),
          "e2": ("E2b.png", 450, 760), "c2": ("C2.png", 450, 760),
          "e3": ("E3c.png", 700, 960), "c3": ("C3.png", 700, 960)}
W_OUT = 1100                      # px wide after scaling (the film shows it ~990 px wide)
CROP = (0, 0, 1376, 660)          # sleeve at the top edge … just under the neck


def load(n):
    return np.asarray(Image.open(os.path.join(HERE, n)).convert("RGB")).astype(np.float32)


def shift(a, dx, dy):
    return np.roll(np.roll(a, dy, 0), dx, 1)


def register(base, ed, x0, x1):
    """integer shift (±6 px) that best fits the edit's neck onto the base's, outside the moving finger"""
    m = np.zeros(base.shape[:2], bool); m[340:640, :] = True; m[:, x0 - 20:x1 + 20] = False; m[:, :10] = m[:, -10:] = False
    best = None
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            e = np.abs(shift(ed, dx, dy) - base)[m].mean()
            if best is None or e < best[0]: best = (e, dx, dy)
    return best


STRING_Y = {"A": 381, "E": 450, "C": 520, "G": 590}   # base px
KNUCKLE_Y, TIP_BELOW = 250, 17                            # a pressing fingertip's lowest outline sits ~17 px under its string


def tip(ed, base, x0, x1):
    """lowest changed skin pixel in the finger's column: (x, y) of the fingertip's bottom"""
    d = (np.abs(ed - base).max(2) > 40) & (ed[..., 0] > 180) & (ed[..., 1] > 120) & (ed[..., 2] > 90)
    d[:, :x0] = d[:, x1:] = False; d[648:] = False
    ys, xs = np.nonzero(d); yb = ys.max()
    return float(xs[ys > yb - 25].mean()), int(yb)


def stretch(ed, x0, x1, f):
    """scale the finger column vertically about the knuckles by f (rows above the knuckles untouched)"""
    out = ed.copy()
    for y in range(KNUCKLE_Y, 648):
        sy = KNUCKLE_Y + (y - KNUCKLE_Y) / f
        y0 = int(sy); t = sy - y0
        if y0 + 1 >= ed.shape[0]: break
        out[y, x0:x1] = ed[y0, x0:x1] * (1 - t) + ed[y0 + 1, x0:x1] * t
    return out


base = load("base.png")
H, W = base.shape[:2]
states = {"open": base}
info = {}
for name, (fn, x0, x1) in STATES.items():
    ed = load(fn)
    err, dx, dy = register(base, ed, x0, x1)
    ed = shift(ed, dx, dy)
    tx, ty = tip(ed, base, x0, x1)
    want = STRING_Y[name[0].upper()] + TIP_BELOW
    f = (want - KNUCKLE_Y) / (ty - KNUCKLE_Y)
    m = (np.abs(ed - base).max(2) > 28).astype(np.float32)        # what the edit changed (the finger)
    if abs(f - 1) > .02:                                          # finger too long or short: bend the edit AND its mask
        ed = stretch(ed, x0, x1, f)
        m = (stretch(np.repeat(m[..., None], 3, 2), x0, x1, f)[..., 0] > .5).astype(np.float32)
    box = np.zeros_like(m); box[:648, x0:x1] = 1                 # only the moving finger's column, above the neck's bottom
    m = m * box
    # the finger = what changed, plus the edit's own skin in this column below the knuckles (so no rest-finger nail
    # shows through a moved finger of the same colour); keep only the blob that holds the fingertip
    skin = (ed[..., 0] > 170) & (ed[..., 0] - ed[..., 2] > 65) & (ed[..., 1] < ed[..., 0] - 30) & (ed[..., 1] > 100)
    skin[:KNUCKLE_Y - 40] = False
    skin &= ndimage.binary_dilation(m > 0, iterations=20)
    m = ndimage.binary_opening((m > 0) | (skin & (box > 0)), iterations=2)
    lab, n = ndimage.label(m)
    ty_new = int(KNUCKLE_Y + (ty - KNUCKLE_Y) * f) - 8
    win = lab[max(0, ty_new - 40):ty_new + 10, int(tx) - 30:int(tx) + 30]
    keep = np.bincount(win[win > 0]).argmax() if (win > 0).any() else 1 + np.argmax(ndimage.sum(m, lab, range(1, n + 1)))
    m = ndimage.binary_fill_holes(lab == keep).astype(np.float32)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(2.5))
    a = (np.asarray(mi).astype(np.float32) / 255 * np.asarray(Image.fromarray((box * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))) / 255)[..., None]
    states[name] = base * (1 - a) + ed * a
    info[name] = {"edit": fn, "shift": [dx, dy], "neck_err": round(float(err), 2), "changed_px": int((a[..., 0] > .5).sum()), "stretch": round(f, 3),
                  "tip": [round(tx), round(KNUCKLE_Y + (ty - KNUCKLE_Y) * f)]}

fade = np.ones((H, W), np.float32)
fade[:, 1290:] = np.linspace(1, 0, W - 1290)[None, :] ** 1.5      # the cut end of the neck melts away (it runs off the screen)
os.makedirs(OUT, exist_ok=True)
x0, y0, x1, y1 = CROP
s = W_OUT / (x1 - x0)
for name, rgb in states.items():
    rgba = key_border(np.clip(rgb, 0, 255))
    rgba[..., 3] *= fade
    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").crop(CROP)
    im = im.resize((W_OUT, round((y1 - y0) * s)), Image.LANCZOS)
    im.save(os.path.join(OUT, f"hand-{name}.webp"), quality=86, method=6)

geo = {"size": [W_OUT, round((y1 - y0) * s)], "scale_from_base": s,
       "strings_y": {k: round(v * s, 1) for k, v in {"A": 381, "E": 450, "C": 520, "G": 590}.items()},
       "nut_x": round(215 * s, 1), "frets_x": [round(v * s, 1) for v in (470, 723, 955, 1166, 1356)],
       "states": info,
       "tips": {n: [round(v["tip"][0] * s, 1), round(v["tip"][1] * s, 1)] for n, v in info.items()}}
json.dump(geo, open(os.path.join(OUT, "hand.json"), "w"), indent=1)
print(json.dumps(geo, indent=1))
