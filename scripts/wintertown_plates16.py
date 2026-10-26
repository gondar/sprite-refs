#!/usr/bin/env python3
"""WinterTown — the 16:9 backdrops of 2026-10-26 (bg2-*.png, the layout with a calm sky behind the tab) into
Palce's plates, with their warm lights measured again; and the port's lit lamp room keyed off its magenta.

Run from the sprite-refs root:  python3 scripts/wintertown_plates16.py [OUT_ROOT] [id ...]
OUT_ROOT defaults to ../MusicGames. Writes fingerpick-warmup/art/wintertown/plate-<id>.webp (1200 px high, the
same quality as wintertown_build.py), updates those entries of art.json (`size`, and `lights` by plate name) and
review/wintertown/check-lights16-<id>.jpg. The game reads a 16:9 plate's floor row from FLOOR (.84)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, "skill/sprite-pipeline/scripts")
from key import key_image  # noqa: E402

GEN = "refs/wintertown/gen"
OUT = sys.argv[1] if len(sys.argv) > 1 else "../MusicGames"
IDS = sys.argv[2:] or ["town", "forest", "port", "mountains", "station", "lake", "stable"]   # stable: the EMPTY one
PALCE = os.path.join(OUT, "fingerpick-warmup/art/wintertown")
REV = "review/wintertown"
os.makedirs(REV, exist_ok=True)
PLATE_H = 1200


def src(name):
    """a generated picture: the PNG when it is still here, else the q95 WebP kept in git"""
    p = os.path.join(GEN, name)
    return p if os.path.exists(p) else p[:-4] + ".webp"


def lights_of(im, n=40):
    """bright, warm pixels (windows, lanterns, the bonfire) → blobs (x, y, r) as fractions of the plate (r of its
    height) — the same rule as wintertown_build.py"""
    W, H = im.size
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = .3 * r + .59 * g + .11 * b
    warm = ndimage.binary_opening((lum > 150) & (r > 200) & (r - b > 70), iterations=1)
    lab, _ = ndimage.label(ndimage.binary_dilation(warm, iterations=3))
    blobs = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        m = (lab[sl] == i) & warm[sl]
        area = m.sum()
        if area < 40: continue
        cy, cx = ndimage.center_of_mass(m)
        blobs.append({"x": round((xs.start + cx) / W, 4), "y": round((ys.start + cy) / H, 4),
                      "r": round(float(np.sqrt(area / np.pi)) / H, 4), "a": int(area)})
    blobs.sort(key=lambda o: -o["a"])
    return [{k: o[k] for k in ("x", "y", "r")} for o in blobs[:n]]


art_path = os.path.join(PALCE, "art.json")
J = json.load(open(art_path))
for p in IDS:
    im = Image.open(src("bg2-%s.png" % p if p != "stable" else "plate-stable-empty.png")).convert("RGB")
    W = round(im.size[0] * PLATE_H / im.size[1])
    im = im.resize((W, PLATE_H), Image.LANCZOS)
    out = os.path.join(PALCE, "plate-%s.webp" % p)
    im.save(out, "WEBP", quality=78, method=6)
    L = lights_of(im)
    J["art"]["plate-" + p] = {"size": [W, PLATE_H], "kb": round(os.path.getsize(out) / 1024), "lights": len(L)}
    J["lights"].pop(p, None)
    J["lights"]["plate-" + p] = L
    chk = im.resize((W // 2, PLATE_H // 2)); d = ImageDraw.Draw(chk)
    for o in L:
        x, y, rr = o["x"] * W / 2, o["y"] * PLATE_H / 2, max(4, o["r"] * PLATE_H)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(0, 255, 255), width=2)
    for f in (.08, .30, .84): d.line([(0, f * PLATE_H / 2), (W / 2, f * PLATE_H / 2)], fill=(255, 0, 0))
    chk.save(os.path.join(REV, "check-lights16-%s.jpg" % p), quality=80)
    print(p, W, PLATE_H, len(L), "lights", J["art"]["plate-" + p]["kb"], "kb")

# the port's lamp room, lit: keyed off magenta, cropped tight, 300 px wide (it is drawn ~40 units wide)
if "port" in IDS:
    rgb = np.array(Image.open(src("port-lamp.png")).convert("RGB"))
    rgba, _ = key_image(rgb, "magenta", 40, 120)
    lamp = Image.fromarray(np.round(rgba).astype(np.uint8))
    lamp = lamp.crop(lamp.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox())
    lamp = lamp.resize((300, round(lamp.size[1] * 300 / lamp.size[0])), Image.LANCZOS)
    out = os.path.join(PALCE, "port-lamp.webp")
    lamp.save(out, "WEBP", quality=82, method=6)
    J["art"]["port-lamp"] = {"size": list(lamp.size), "kb": round(os.path.getsize(out) / 1024)}
    print("port-lamp", lamp.size)

json.dump(J, open(art_path, "w"), indent=1)
