"""Cut a sheet whose layout the model chose itself: key it, find blobs, group them into rows by their vertical
centre, sort each row left to right, and name them from ITEMS in that reading order. Writes full-res PNG crops
(premultiplied-safe RGBA) and check.png. usage: cutsheet.py SHEET ITEMS OUTDIR --key green|magenta [--lo --hi]
--min-area px  ;  --rowgap fraction of height that separates rows (default 0.12)"""
import argparse, json, math, os, sys, numpy as np, importlib.util
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
spec = importlib.util.spec_from_file_location("key", "/home/user/MusicGames/.claude/skills/asset-sheet/scripts/key.py")
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)
ap = argparse.ArgumentParser(); ap.add_argument("sheet"); ap.add_argument("items"); ap.add_argument("outdir")
ap.add_argument("--key", default="auto"); ap.add_argument("--lo", type=float, default=40); ap.add_argument("--hi", type=float, default=120)
ap.add_argument("--min-area", type=float, default=4000); ap.add_argument("--rowgap", type=float, default=0.12)
ap.add_argument("--dil", type=int, default=4)
a = ap.parse_args()
names = [l.strip() for l in open(a.items) if l.strip()]
rgb = np.array(Image.open(a.sheet).convert("RGB"))
rgba, kn = key.key_image(rgb, a.key, a.lo, a.hi)
H, W = rgba.shape[:2]
solid = rgba[..., 3] > 60
lab, n = ndi.label(ndi.binary_dilation(solid, iterations=a.dil))
objs = ndi.find_objects(lab)
blobs = []
for i, sl in enumerate(objs):
    m = lab[sl] == i + 1
    ar = (m & solid[sl]).sum()
    if ar < a.min_area: continue
    ys, xs = np.nonzero(m)
    blobs.append(dict(id=i + 1, sl=sl, cy=sl[0].start + ys.mean(), cx=sl[1].start + xs.mean(), area=int(ar)))
blobs.sort(key=lambda b: b["cy"])
rows = []
for b in blobs:
    if rows and b["cy"] - rows[-1][-1]["cy"] < a.rowgap * H: rows[-1].append(b)
    else: rows.append([b])
order = [b for r in rows for b in sorted(r, key=lambda b: b["cx"])]
print("rows:", [len(r) for r in rows], "blobs:", len(order), "names:", len(names))
os.makedirs(a.outdir, exist_ok=True)
cuts = []
for k, b in enumerate(order):
    name = names[k] if k < len(names) else f"extra_{k}"
    sl = b["sl"]; m = lab[sl] == b["id"]
    crop = rgba[sl].copy(); crop[..., 3] = np.where(m, crop[..., 3], 0)
    ys, xs = np.nonzero(crop[..., 3] > 0)
    crop = crop[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray(np.round(crop).astype(np.uint8)); im.save(os.path.join(a.outdir, name + ".png"))
    cuts.append((name, im, (sl[1].start + xs.min(), sl[0].start + ys.min())))
json.dump({n: {"x": int(o[0]), "y": int(o[1]), "w": im.width, "h": im.height} for n, im, o in cuts},
          open(os.path.join(a.outdir, "cuts.json"), "w"), indent=1)
T = 200; cols = 8; R = math.ceil(len(cuts) / cols)
chk = Image.new("RGB", (cols * T, R * (T + 18)), "white"); d = ImageDraw.Draw(chk)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
for k, (name, im, _) in enumerate(cuts):
    X, Y = (k % cols) * T, (k // cols) * (T + 18)
    for yy in range(0, T, 10):
        for xx in range(0, T, 10):
            if (xx // 10 + yy // 10) % 2: d.rectangle([X + xx, Y + yy, X + xx + 9, Y + yy + 9], fill=(205, 205, 205))
    t = im.copy(); t.thumbnail((T - 8, T - 8)); chk.paste(t, (X + (T - t.width) // 2, Y + (T - t.height) // 2), t)
    d.text((X + 3, Y + T + 1), f"{name} {im.width}x{im.height}", fill=(20, 20, 20), font=f)
chk.save(os.path.join(a.outdir, "check.png"))
