#!/usr/bin/env python3
"""WinterTown — the walk-in nativity cast (sheet-nativity, 12 figures on green) cut into Palce's single pictures.

The sheet came back with the figures loosely placed rather than on its 3 x 4 grid (the holy family between two
cells, the free donkey under the ox), so cut_assets.py --grid named them off by one. Here each figure is the
key's biggest pieces, named by where its centre lies on the sheet (NAMES: fractions of the sheet, measured on
it), and the set is checked: twelve figures, each name used once.

Run from the sprite-refs root:  python3 scripts/wintertown_nativity.py [OUT_ROOT]
Writes fingerpick-warmup/art/wintertown/nv-<name>.webp (TARGET px high), their sizes into art.json, and
review/wintertown/check-nativity.jpg (every cut on a checkerboard with its name)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, "skill/sprite-pipeline/scripts")
from key import key_image  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "../MusicGames"
PALCE = os.path.join(OUT, "fingerpick-warmup/art/wintertown")
SRC = "refs/wintertown/gen/sheet-nativity.png"
if not os.path.exists(SRC): SRC = SRC[:-4] + ".webp"
NAMES = {   # name: (x, y) of its centre on the sheet, and its height in the game's file (px)
    "joseph-mary-donkey": ((.20, .18), 420), "holy-family": ((.53, .18), 380), "ox-lying": ((.83, .13), 200),
    "donkey-free": ((.84, .34), 300), "shepherd-old": ((.16, .51), 380), "shepherd-boy": ((.38, .51), 330),
    "sheep-a": ((.62, .55), 200), "sheep-b": ((.85, .56), 200), "carollers": ((.23, .81), 380),
    "bread-woman": ((.54, .83), 360), "highlander": ((.75, .83), 380), "dog": ((.90, .92), 150)}

rgb = np.array(Image.open(SRC).convert("RGB"))
rgba, _ = key_image(rgb, "green", 40, 120)
rgba = np.round(rgba).astype(np.uint8)
H, W = rgba.shape[:2]
solid = rgba[..., 3] > 60
lab, n = ndimage.label(ndimage.binary_dilation(solid, iterations=6))
pieces = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    area = (lab[sl] == i).sum()
    if area < .0005 * W * H: continue          # specks of key haze
    ys, xs = sl
    pieces.append({"i": i, "box": (xs.start, ys.start, xs.stop, ys.stop), "c": ((xs.start + xs.stop) / 2 / W, (ys.start + ys.stop) / 2 / H), "a": area})
# each piece goes to the nearest name; a name collects all its pieces (the star on its pole, a loose tail)
got = {k: [] for k in NAMES}
for p in pieces:
    k = min(NAMES, key=lambda k: (NAMES[k][0][0] - p["c"][0]) ** 2 + (NAMES[k][0][1] - p["c"][1]) ** 2)
    got[k].append(p)
empty = [k for k, v in got.items() if not v]
if empty: sys.exit("no figure near: " + ", ".join(empty))
J = json.load(open(os.path.join(PALCE, "art.json")))
cuts = []
for k, ps in got.items():
    x0 = min(p["box"][0] for p in ps); y0 = min(p["box"][1] for p in ps)
    x1 = max(p["box"][2] for p in ps); y1 = max(p["box"][3] for p in ps)
    mask = np.isin(lab[y0:y1, x0:x1], [p["i"] for p in ps])
    crop = rgba[y0:y1, x0:x1].copy(); crop[..., 3] = np.where(mask, crop[..., 3], 0)
    r, g, b = (crop[..., c].astype(int) for c in range(3))     # the lantern's glow mixed with the green: despill
    crop[..., 1] = np.minimum(g, np.maximum(r, b) + 6).astype(np.uint8)
    im = Image.fromarray(crop, "RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox())
    h = NAMES[k][1]
    im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    out = os.path.join(PALCE, "nv-%s.webp" % k)
    im.save(out, "WEBP", quality=84, method=6)
    J["art"]["nv-" + k] = {"size": list(im.size), "kb": round(os.path.getsize(out) / 1024)}
    cuts.append((k, im, len(ps)))
    print(k, im.size, len(ps), "pieces")
json.dump(J, open(os.path.join(PALCE, "art.json"), "w"), indent=1)

# the check: every cut on a checkerboard with its name
cw, ch = 300, 330
sheet = Image.new("RGB", (cw * 4, ch * 3), "white"); d = ImageDraw.Draw(sheet)
for j, (k, im, np_) in enumerate(cuts):
    cx, cy = (j % 4) * cw, (j // 4) * ch
    for a in range(0, cw, 15):
        for b in range(0, ch - 30, 15):
            if (a // 15 + b // 15) % 2: d.rectangle((cx + a, cy + b, cx + a + 14, cy + b + 14), fill=(220, 220, 220))
    t = im.copy(); t.thumbnail((cw - 10, ch - 40))
    sheet.paste(t, (cx + (cw - t.width) // 2, cy + ch - 32 - t.height), t)
    d.text((cx + 6, cy + ch - 24), "%s (%d)" % (k, np_), fill=(0, 0, 0))
os.makedirs("review/wintertown", exist_ok=True)
sheet.save("review/wintertown/check-nativity.jpg", quality=85)
