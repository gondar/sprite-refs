"""Abordaż art: from the cut sheets (sheets/abordaz/*) to the game's fail-open WebP files.
Run from the sprite-refs root: python3 scripts/abordaz_build.py /home/user/MusicGames
Writes fingerpick-warmup/art/abordaz/ (Morskie opowieści, Palce) and ukulele-warmup/art/abordaz/ (the song theme)."""
import sys, os, json
import numpy as np
from PIL import Image

MG = sys.argv[1]
FP = os.path.join(MG, "fingerpick-warmup/art/abordaz"); UK = os.path.join(MG, "ukulele-warmup/art/abordaz")
os.makedirs(FP, exist_ok=True); os.makedirs(UK, exist_ok=True)
S = "sheets/abordaz"

def load(p): return Image.open(os.path.join(S, p)).convert("RGBA")
def fit(im, side):
    k = side / max(im.size)
    return im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS) if k < 1 else im
def trim(im):
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(bb) if bb else im
def save(im, *paths, q=82):
    for d, name in paths:
        im.save(os.path.join(d, name + ".webp"), "WEBP", quality=q, method=6)
meta = {}

# the sea plate (no alpha): one picture for both games
sea = Image.open("refs/abordaz/gen/plate-sea.png").convert("RGB")
sea = sea.resize((2400, round(2400 * sea.size[1] / sea.size[0])), Image.LANCZOS)
sea.save(os.path.join(FP, "sea.webp"), "WEBP", quality=78, method=6)
sea.resize((1800, round(1800 * sea.size[1] / sea.size[0])), Image.LANCZOS).save(os.path.join(UK, "sea.webp"), "WEBP", quality=76, method=6)
meta["sea"] = {"w": sea.size[0], "h": sea.size[1], "horizon": 0.41}

# the brig: the drawn waterline is cut off just under the keel
ship = load("ship/ship.webp")
a = np.asarray(ship)[:, :, 3] > 40
rows = a.mean(axis=1)
line = max(i for i in range(len(rows)) if rows[i] > 0.6)   # the long waterline row
ship = trim(ship.crop((0, 0, ship.size[0], line - 3)))
ship = fit(ship, 1100); save(ship, (FP, "ship")); save(fit(ship, 420), (UK, "ship"))
meta["ship"] = {"w": ship.size[0], "h": ship.size[1]}

# Lina hanging: the bar she grips is erased outside her fists (the rope is drawn in code)
lh = load("crew/lina-hang.webp"); arr = np.array(lh)
fists = [(188, 238), (266, 320)]
for y in range(0, 78):
    for x in range(arr.shape[1]):
        if not any(f0 <= x < f1 for f0, f1 in fists) or y < 40: arr[y, x, 3] = 0
lh = trim(Image.fromarray(arr))
def largest(im):   # keep the figure only (drops a stray splash or a bar stub)
    from scipy import ndimage as ndi
    al = np.array(im); m = al[:, :, 3] > 20
    lab, n = ndi.label(ndi.binary_dilation(m, iterations=3))
    if n > 1:
        sizes = ndi.sum(m, lab, range(1, n + 1)); keep = lab == (1 + int(np.argmax(sizes)))
        al[~keep, 3] = 0
    return trim(Image.fromarray(al))
lh = largest(lh)
figs = {"lina-hang": lh}
for n in ["szabla-arm", "pieprznik", "grzmot", "szabla-cheer", "lina-crouch", "lina-leap", "lina-air", "lina-land"]:
    figs[n] = largest(load("crew/" + n + ".webp"))
figs["szabla"] = largest(load("szabla/szabla.webp"))
for n in ["szabla", "szabla-arm", "pieprznik", "grzmot", "lina-hang", "szabla-cheer"]:
    im = fit(figs[n], 420); save(im, (FP, n)); meta[n] = {"w": im.size[0], "h": im.size[1]}
save(fit(figs["szabla-cheer"], 420), (UK, "szabla-cheer"))

# Lina's hop for the song conductor: four poses in one strip, equal cells, feet on one baseline
poses = [fit(figs[n], 260) for n in ["lina-crouch", "lina-leap", "lina-air", "lina-land"]]
H = max(p.size[1] for p in poses); W = max(p.size[0] for p in poses)
strip = Image.new("RGBA", (W * 4, H), (0, 0, 0, 0))
for i, p in enumerate(poses): strip.alpha_composite(p, (i * W + (W - p.size[0]) // 2, H - p.size[1]))
save(strip, (UK, "lina-hop")); meta["lina-hop"] = {"cell": [W, H], "frames": 4}

# props
isl = load("props/island.webp"); al = np.asarray(isl).astype(int)
blue = (al[:, :, 2] > al[:, :, 0] + 40) & (al[:, :, 3] > 40) & (al[:, :, 2] > 120)
water_rows = [y for y in range(al.shape[0]) if blue[y].mean() > 0.35]
isl = trim(isl.crop((0, 0, isl.size[0], min(water_rows) + 2))) if water_rows else isl
isl = fit(isl, 520); save(isl, (FP, "island"), (UK, "island")); meta["island"] = {"w": isl.size[0], "h": isl.size[1]}
for n in ["gull-up", "gull-mid", "gull-down"]:
    g = fit(load("props/" + n + ".webp"), 160); save(g, (FP, n), (UK, n)); meta[n] = {"w": g.size[0], "h": g.size[1]}
for n, side in [("chest-open", 320), ("cloud", 360), ("capybara", 220)]:
    im = fit(load("props/" + n + ".webp"), side); save(im, (FP, n), (UK, n))

# the comic page: eight panels, the song theme's side pictures
for i in range(1, 9):
    p = Image.open(os.path.join(S, "comic/panel-%d.png" % i)).convert("RGB")
    p = p.resize((560, round(560 * p.size[1] / p.size[0])), Image.LANCZOS)
    p.save(os.path.join(UK, "panel-%d.webp" % i), "WEBP", quality=80, method=6)
json.dump(meta, open(os.path.join(FP, "art.json"), "w"), indent=1)
print(json.dumps(meta))
