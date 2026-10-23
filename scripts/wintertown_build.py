#!/usr/bin/env python3
"""WinterTown (Pójdźmy wszyscy do stajenki) — cut the generated sheets into the games' files.

Run from the sprite-refs root:  python3 scripts/wintertown_build.py [OUT_ROOT]
OUT_ROOT defaults to ../MusicGames. Writes:
  fingerpick-warmup/art/wintertown/   plates, lights, stage pieces, cast and animal strips, movers, foreground props
  ukulele-warmup/art/wintertown/      the comic panels and the star boy's run
plus art.json in each and review/wintertown/check-*.png to look at.

Sizes are set from how big each thing is DRAWN, not from the source: the Palce stage is the bottom ~2/3 of a
900-unit-high view, drawn at most 2 device px per unit, so a plate needs ~1200 px of height, a character
~560, a horse ~460, a sparrow ~90 (see TARGET). Strips: equal cells side by side, `anchor` = the feet (the
point that stays put), `ref` = frame 0's figure height, all in strip pixels — as Morskie's art.json."""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

sys.path.insert(0, "skill/sprite-pipeline/scripts")
from key import key_image  # noqa: E402

GEN = "refs/wintertown/gen"


def src(name):
    """a generated sheet: the PNG when it is still here, else the q95 WebP kept in git (the PNGs are 200 MB)"""
    p = os.path.join(GEN, name)
    return p if os.path.exists(p) else p[:-4] + ".webp"

OUT = sys.argv[1] if len(sys.argv) > 1 else "../MusicGames"
PALCE = os.path.join(OUT, "fingerpick-warmup/art/wintertown")
SONG = os.path.join(OUT, "ukulele-warmup/art/wintertown")
REV = "review/wintertown"
for d in (PALCE, SONG, REV): os.makedirs(d, exist_ok=True)
ART_P, ART_S = {}, {}


def save(im, path, q=80):
    im.save(path, "WEBP", quality=q, method=6)
    return os.path.getsize(path)


def keyed(name, key):
    rgb = np.array(Image.open(src(name)).convert("RGB"))
    rgba, _ = key_image(rgb, key, 40, 120)
    return np.round(rgba).astype(np.uint8)


def cells(rgba, cols, rows, min_frac=0.0008):
    """the alpha mask's pieces, grouped by the grid cell their centre falls in → {(c, r): bbox}. Each cell keeps
    its biggest piece plus the small ones lying within ~8 % of it (a hen's loose feathers, a rat's whiskers);
    a sliver of the NEIGHBOUR's tail that pokes into the cell is dropped."""
    a = rgba[..., 3] > 40
    lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=2))
    h, w = a.shape
    per = {}
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None: continue
        ys, xs = sl
        area = (lab[sl] == i).sum()
        if area < min_frac * w * h * .05: continue
        cy, cx = (ys.start + ys.stop) / 2, (xs.start + xs.stop) / 2
        per.setdefault((int(cx * cols / w), int(cy * rows / h)), []).append((area, (xs.start, ys.start, xs.stop, ys.stop)))
    out = {}
    for k, ps in per.items():
        ps.sort(key=lambda p: -p[0])
        if ps[0][0] < min_frac * w * h: continue
        x0, y0, x1, y1 = ps[0][1]
        mx, my = .08 * (x1 - x0), .08 * (y1 - y0)
        for _, (a0, b0, a1, b1) in ps[1:]:
            if a0 >= x0 - mx and a1 <= x1 + mx and b0 >= y0 - my and b1 <= y1 + my:
                x0, y0, x1, y1 = min(x0, a0), min(y0, b0), max(x1, a1), max(y1, b1)
        out[k] = (x0, y0, x1, y1)
    return out


def clean(crop):
    """inside a crop keep the figure: its biggest piece, pieces of a fair size, and small ones that do not touch
    the crop's edge (loose feathers stay; a neighbour's sliver at the edge and faint key haze go)"""
    a = crop[..., 3] > 150          # the solid figure; key haze (a faint ghost tree) stays under this
    lab, n = ndimage.label(a)
    if n == 0: return crop
    areas = ndimage.sum(a, lab, range(1, n + 1))
    big = areas.max(); keep = np.zeros(n + 1, bool)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        edge = ys.start == 0 or xs.start == 0 or ys.stop == a.shape[0] or xs.stop == a.shape[1]
        keep[i] = areas[i - 1] >= .015 * big or (not edge and areas[i - 1] >= 30)
    m = ndimage.binary_dilation(keep[lab], iterations=3)
    out = crop.copy(); out[..., 3] = np.where(m, out[..., 3], 0)
    return out


def strip(name, frames, target, dest, art, base=None, pad=6):
    """frames: [(rgba, bbox, baseline)] → one strip. All frames share ONE scale (frame 0's height → target),
    each sits on its row's baseline so a jump stays in the air, centred on its bbox."""
    s = target / (frames[0][1][3] - frames[0][1][1])
    ims = []
    for rgba, (x0, y0, x1, y1), bl in frames:
        im = Image.fromarray(clean(rgba[y0:y1, x0:x1])).resize((max(1, round((x1 - x0) * s)), max(1, round((y1 - y0) * s))), Image.LANCZOS)
        ims.append((im, round((bl - y1) * s)))          # px the figure's bottom is above the ground
    above = max(im.size[1] + lift for im, lift in ims)
    cw = max(im.size[0] for im, _ in ims) + 2 * pad
    ch = above + 2 * pad
    sheet = Image.new("RGBA", (cw * len(ims), ch))
    for i, (im, lift) in enumerate(ims):
        sheet.paste(im, (i * cw + (cw - im.size[0]) // 2, ch - pad - lift - im.size[1]), im)
    size = save(sheet, os.path.join(dest, name + ".webp"))
    art[name] = {"cell": [cw, ch], "frames": len(ims), "anchor": [cw / 2, ch - pad], "ref": round(ims[0][0].size[1], 1), "kb": round(size / 1024)}
    return sheet


def single(rgba, bbox, name, size, dest, art, by="h", q=82):
    x0, y0, x1, y1 = bbox
    im = Image.fromarray(clean(rgba[y0:y1, x0:x1]))
    k = size / (im.size[1] if by == "h" else im.size[0])
    if k < 1: im = im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS)
    kb = save(im, os.path.join(dest, name + ".webp"), q)
    art[name] = {"size": list(im.size), "kb": round(kb / 1024)}
    return im


def baseline_of(boxes, keys):
    return max(boxes[k][3] for k in keys)


# ---------------- plates + their lights ----------------
PLATES = ["town", "forest", "port", "mountains", "station", "lake", "stable"]
PLATE_H = 1200
lights_all = {}
for p in PLATES:
    im = Image.open(src("plate-%s.png" % p)).convert("RGB")
    W = round(im.size[0] * PLATE_H / im.size[1])
    im = im.resize((W, PLATE_H), Image.LANCZOS)
    kb = save(im, os.path.join(PALCE, "plate-%s.webp" % p), 78)
    # the warm lights: bright, warm pixels (windows, lanterns, the bonfire, the star) → blobs with a centre and
    # a radius, as fractions of the plate, for the code's flicker halos and the snow's glints
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = .3 * r + .59 * g + .11 * b
    warm = (lum > 150) & (r > 200) & (r - b > 70)
    warm = ndimage.binary_opening(warm, iterations=1)
    lab, n = ndimage.label(ndimage.binary_dilation(warm, iterations=3))
    blobs = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        m = (lab[sl] == i) & warm[sl]
        area = m.sum()
        if area < 40: continue
        cy, cx = ndimage.center_of_mass(m)
        blobs.append({"x": round((xs.start + cx) / W, 4), "y": round((ys.start + cy) / PLATE_H, 4),
                      "r": round(float(np.sqrt(area / np.pi)) / PLATE_H, 4), "a": int(area)})
    blobs.sort(key=lambda o: -o["a"])
    lights_all[p] = [{k: o[k] for k in ("x", "y", "r")} for o in blobs[:40]]
    ART_P["plate-" + p] = {"size": [W, PLATE_H], "kb": round(kb / 1024), "lights": len(lights_all[p])}
    # a check image with the lights circled
    chk = im.copy().resize((W // 2, PLATE_H // 2))
    from PIL import ImageDraw
    d = ImageDraw.Draw(chk)
    for o in lights_all[p]:
        x, y, rr = o["x"] * W / 2, o["y"] * PLATE_H / 2, max(4, o["r"] * PLATE_H / 2 * 2.2)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(0, 255, 255), width=2)
    chk.save(os.path.join(REV, "check-lights-%s.jpg" % p), quality=80)

# ---------------- the cast: 8 × 3 cells (the model drew 8 columns, not 5) ----------------
cast = keyed("sheet-cast.png", "magenta")
cb = cells(cast, 8, 3)
CAST = {   # name: [(col, row) stand, sing/play A, sing/play B]
    "fiddler": [(0, 0), (0, 1), (1, 2)],
    "starboy": [(2, 0), (2, 1), (2, 2)],
    "shepherd": [(4, 0), (4, 1), (4, 2)],
    "angel": [(5, 0), (5, 1), (5, 2)],
    "girl": [(6, 0), (6, 1), (7, 2)],
}
CAST_H = 560
f0 = cb[CAST["fiddler"][0]]
cast_scale = CAST_H / (f0[3] - f0[1])
for nm, ks in CAST.items():
    # one scale for the whole cast (relative heights kept): frame 0's height × cast_scale
    t = (cb[ks[0]][3] - cb[ks[0]][1]) * cast_scale
    strip(nm, [(cast, cb[k], cb[k][3]) for k in ks], round(t), PALCE, ART_P)

# ---------------- the animals: 4 poses each (stand · sing · dance · mischief) ----------------
big = keyed("sheet-animals-big.png", "green")       # rows 2, 3 (horse, pig) are clean
big[: int(big.shape[0] * .21), :, 3] = 0; big[int(big.shape[0] * .615):, :, 3] = 0   # the rest has bits of the moodboard pasted in: drop it
bb = cells(big, 4, 5)
hs = keyed("sheet-horse.png", "green")               # the horse redone alone: its old row touched the pasted moodboard
hb = cells(hs, 4, 2)                                 # it came as two rows of four: the top row
big2 = keyed("sheet-animals-big2.png", "green")     # donkey, sheep, fox redone on a clean ground
bb2 = cells(big2, 4, 3)
small = keyed("sheet-animals-small.png", "green")
sb = cells(small, 4, 6)
TARGET = {"horse": 460, "donkey": 400, "pig": 260, "sheep": 250, "fox": 230,
          "hen": 160, "rooster": 190, "dove": 120, "sparrow": 92, "rat": 124, "rat2": 124}
ROWS = [("horse", hs, hb, 0), ("pig", big, bb, 2), ("donkey", big2, bb2, 0), ("sheep", big2, bb2, 1), ("fox", big2, bb2, 2),
        ("hen", small, sb, 0), ("rooster", small, sb, 1), ("dove", small, sb, 2), ("sparrow", small, sb, 3), ("rat", small, sb, 4), ("rat2", small, sb, 5)]
for nm, sh, boxes, row in ROWS:
    ks = [(c, row) for c in range(4)]
    missing = [k for k in ks if k not in boxes]
    if missing: raise SystemExit("%s: no figure in %s" % (nm, missing))
    bl = baseline_of(boxes, ks)
    if nm == "dove": bl = boxes[(0, row)][3]          # the flying doves are in the air: measure from the standing one
    strip(nm, [(sh, boxes[k], bl) for k in ks], TARGET[nm], PALCE, ART_P)

# ---------------- the town's movers: 4 × 4 single items ----------------
mv = keyed("sheet-movers.png", "green")
mb = cells(mv, 4, 4)
MOVERS = [("loco", 150), ("carriage", 130), ("wheel-red", 80), ("wheel-iron", 60), ("sleigh", 110), ("sled", 120),
          ("skater-w", 150), ("skater-m", 150), ("skier", 130), ("cart", 140), ("wheel-wood", 70), ("iceyacht", 170),
          ("walker-lantern", 150), ("walker-basket", 150), ("crow-up", 70), ("crow-down", 70)]
for i, (nm, hpx) in enumerate(MOVERS):
    k = (i % 4, i // 4)
    if k not in mb: raise SystemExit("movers: nothing in cell %s (%s)" % (k, nm))
    single(mv, mb[k], nm, hpx * 2, PALCE, ART_P)

# ---------------- the stage pieces: found by shape and place ----------------
sp = keyed("sheet-stagepieces.png", "green")
a = sp[..., 3] > 40
lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=3))
H, W = a.shape
pieces = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    ys, xs = sl
    if (lab[sl] == i).sum() < 0.002 * W * H: continue
    pieces.append((xs.start, ys.start, xs.stop, ys.stop))
pieces.sort(key=lambda b: (b[0], b[1]))
def pick(cond):
    for b in pieces:
        if cond(b): return b
    raise SystemExit("stage piece not found")
tall = sorted([b for b in pieces if (b[3] - b[1]) > .7 * H], key=lambda b: b[0])
curtain, pillar = tall[0], tall[1]
mid = [b for b in pieces if b not in tall and b[0] < .8 * W]
valance = min(mid, key=lambda b: b[1]); floor = max(mid, key=lambda b: b[3])
crest = [b for b in mid if b not in (valance, floor)][0]
right = sorted([b for b in pieces if b[0] >= .8 * W], key=lambda b: b[1])
lantern, footlight = right[0], right[1]
single(sp, curtain, "curtain", 1250, PALCE, ART_P)
single(sp, pillar, "pillar", 1250, PALCE, ART_P)
single(sp, valance, "valance", 2000, PALCE, ART_P, by="w")
single(sp, crest, "crest", 760, PALCE, ART_P, by="w")
single(sp, lantern, "lantern", 300, PALCE, ART_P)
single(sp, footlight, "footlight", 120, PALCE, ART_P)
single(sp, floor, "floor", 2400, PALCE, ART_P, by="w")

# ---------------- foreground props (parallax), when the sheet exists ----------------
if os.path.exists(src("sheet-foreground.png")):
    fg = keyed("sheet-foreground.png", "green")
    fb = cells(fg, 4, 3)
    FG = [("fir", 640), ("spruce", 300), ("birch", 640), ("drift", 140), ("fence", 160), ("lamp", 520),
          ("reeds", 220), ("boulder", 200), ("bench", 150), ("signpost", 300), ("barrels", 220), ("branch", 360)]
    for i, (nm, hpx) in enumerate(FG):
        k = (i % 4, i // 4)
        if k in fb: single(fg, fb[k], "fg-" + nm, hpx * 2, PALCE, ART_P)
        else: print("foreground: nothing in", k, nm)

# ---------------- the comic page: 16 square panels ----------------
cp = np.asarray(Image.open(src("sheet-comic.png")).convert("RGB")).astype(np.int16)
cream = cp[5:40, 5:40].reshape(-1, 3).mean(0)
ink = np.abs(cp - cream).sum(2) > 60
H, W = ink.shape
rows_on = ink.mean(1) > .5; cols_on = ink.mean(0) > .5      # the gutters are cream across the whole page
def runs(on):
    out, s = [], None
    for i, v in enumerate(on):
        if v and s is None: s = i
        if not v and s is not None:
            if i - s > 200: out.append((s, i))
            s = None
    if s is not None and len(on) - s > 200: out.append((s, len(on)))
    return out
ry, rx = runs(rows_on), runs(cols_on)
if len(ry) != 4 or len(rx) != 4: raise SystemExit("comic: found %d×%d panels" % (len(rx), len(ry)))
page = Image.open(src("sheet-comic.png")).convert("RGB")
n = 0
for (y0, y1) in ry:
    for (x0, x1) in rx:
        n += 1
        im = page.crop((x0, y0, x1, y1)).resize((900, round(900 * (y1 - y0) / (x1 - x0))), Image.LANCZOS)
        kb = save(im, os.path.join(SONG, "panel-%d.webp" % n), 80)
        ART_S["panel-%d" % n] = {"size": list(im.size), "kb": round(kb / 1024)}

# ---------------- the star boy's run (Śpiewnik's conductor), when the sheet exists ----------------
if os.path.exists(src("sheet-run.png")):
    rn = keyed("sheet-run.png", "magenta")
    rb = cells(rn, 4, 2)
    ks = [(c, r) for r in range(2) for c in range(4)]
    if all(k in rb for k in ks):
        bl = [max(rb[(c, r)][3] for c in range(4)) for r in range(2)]   # each row of the sheet has its own ground
        strip("starboy-run", [(rn, rb[k], bl[k[1]]) for k in ks], 150, SONG, ART_S)
    else: print("run: missing cells", [k for k in ks if k not in rb])
    single(cast, cb[CAST["starboy"][0]], "starboy", 300, SONG, ART_S)
# the songbook theme's other pictures: the fiddler who calls the count-in, the donkey who peeks when paused, and
# the town at night as the page's background, with the stage's curtain and valance for its edges
single(cast, cb[CAST["fiddler"][0]], "fiddler", 300, SONG, ART_S)
single(big2, bb2[(1, 0)], "donkey-sing", 220, SONG, ART_S)
import shutil
for f in ("plate-town", "curtain", "valance"):
    shutil.copy(os.path.join(PALCE, f + ".webp"), os.path.join(SONG, f + ".webp"))
    ART_S[f] = dict(ART_P[f])

json.dump({"art": ART_P, "lights": lights_all}, open(os.path.join(PALCE, "art.json"), "w"), indent=1)
json.dump({"art": ART_S}, open(os.path.join(SONG, "art.json"), "w"), indent=1)
tot = lambda d: sum(v.get("kb", 0) for v in d.values())
print("palce: %d files, %d KB · song: %d files, %d KB" % (len(ART_P), tot(ART_P), len(ART_S), tot(ART_S)))
