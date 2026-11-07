"""Pack the Mountain King cave show's cast for the game (MusicGames fingerpick-warmup/art/cast/).

In:  sheets/mountain-king-cast/<who>/*.webp — cut by cut_assets.py at the generated sheet's own scale (one scale
     per sheet, so the poses of a character keep their relative sizes), <who>-run/f1..f8.webp, props/*.webp.
Out: <game>/art/cast/<who>.webp — the character's poses shelf-packed at one scale, chosen so its reference pose is
     REF_PX tall (about 1.6x its height on a 1080p screen), and <game>/art/cast/cast.json:
     { who: { img, h (reference height as a fraction of the painting's height), poses: { id: [x, y, w, h, ax, ay] } } }
     where ax, ay is the pose's anchor inside its rect: the feet (bottom centre), or the toes for a hanging bat.
     A run cycle is 8 frames in equal cells, the feet on one line and the body's centre on one column.
usage: python3 scripts/mk_cast_build.py <game fingerpick-warmup dir>"""
import sys, os, json, glob, numpy as np
from PIL import Image

SRC = "sheets/mountain-king-cast"
# height of each character's reference pose, as a fraction of the painting's height (1072 px), and that pose
CAST = {
  "florek":     (0.165, "stand"),
  "panna":      (0.15, "swoon"),
  "drzemek":    (0.15, "asleep"),       # a bust: only ever seen over a rock
  "psotek":     (0.15, "stand"),
  "nietoperek": (0.085, "hang-sleep"),
  "iskierka":   (0.06, "crawl"),
  "kopus":      (0.14, "stand"),
  "glazik":     (0.13, "nod-up"),       # inside a porthole
}
RUNS = {"florek-run": ("florek", "stand", 0.93), "panna-run": ("panna", "swoon", 0.95)}
PROPS = {"hat-red": 0.05, "heart": 0.035, "pebble": 0.018, "dust-puff": 0.05, "dizzy-stars": 0.03, "sparkle": 0.04}
HANG = ("hang-",)
OVER = 1.6                       # pixels stored per painting pixel at 1080p
PAD = 2

def load(p):
    im = Image.open(p).convert("RGBA"); bb = im.getchannel("A").point(lambda v: 255 if v > 10 else 0).getbbox()
    return im.crop(bb)

def shelf(items, maxw=2048):
    x = y = rowh = 0; out = {}
    for k, im in items:
        if x + im.size[0] > maxw: x = 0; y += rowh + PAD; rowh = 0
        out[k] = (x, y); x += im.size[0] + PAD; rowh = max(rowh, im.size[1])
    W = max(out[k][0] + im.size[0] for k, im in items); H = y + rowh
    sheet = Image.new("RGBA", (W, H))
    for k, im in items: sheet.alpha_composite(im, out[k])
    return sheet, out

def anchor(k, im):
    a = np.asarray(im.getchannel("A")) > 40; ys, xs = np.where(a)
    if k.startswith(HANG):                       # hanging: the toes at the top
        top = ys.min(); cols = xs[ys < top + max(4, im.size[1] // 20)]
        return float(cols.mean()), float(top)
    bot = ys.max(); cols = xs[ys > bot - max(4, im.size[1] // 12)]
    return float(cols.mean()), float(bot)

def main(game):
    out = os.path.join(game, "art", "cast"); os.makedirs(out, exist_ok=True); meta = {}
    for who, (hfrac, ref) in CAST.items():
        files = sorted(glob.glob(os.path.join(SRC, who, "*.webp")))
        ims = {os.path.basename(f)[:-5]: load(f) for f in files if not os.path.basename(f).startswith("atlas")}
        k = hfrac * 1072 * OVER / ims[ref].size[1]
        items = [(n, im.resize((max(1, round(im.size[0] * k)), max(1, round(im.size[1] * k))), Image.LANCZOS)) for n, im in sorted(ims.items())]
        sheet, pos = shelf(items)
        sheet.save(os.path.join(out, who + ".webp"), quality=86, method=6)
        poses = {}
        for n, im in items:
            ax, ay = anchor(n, im); poses[n] = [int(pos[n][0]), int(pos[n][1]), im.size[0], im.size[1], round(ax, 1), round(ay, 1)]
            if who == "drzemek":                      # the bobble of his nightcap: the leftmost point (the bat hangs from it)
                al = np.asarray(im.getchannel("A")) > 100; ys, xs = np.where(al); i = xs.argmin(); poses[n] += [int(xs[i]), int(ys[i])]
        meta[who] = {"img": "art/cast/%s.webp" % who, "h": hfrac, "ref": ref, "px": round(ims[ref].size[1] * k), "poses": poses}
        meta[who]["_k"] = k
    for run, (who, ref, rel) in RUNS.items():
        fr = [load(os.path.join(SRC, run, "f%d.webp" % i)) for i in range(1, 9)]
        med = float(np.median([f.size[1] for f in fr]))
        k = meta[who]["px"] * rel / med
        fr = [f.resize((round(f.size[0] * k), round(f.size[1] * k)), Image.LANCZOS) for f in fr]
        # align: feet (lowest opaque row) on one line, the body's centre of mass (upper 70%) on one column
        info = []
        for f in fr:
            a = np.asarray(f.getchannel("A")).astype(float) / 255; ys, xs = np.nonzero(a > .16)
            bot = ys.max(); top = ys.min(); body = a[:int(top + (bot - top) * .7)]
            cx = (body.sum(0) * np.arange(body.shape[1])).sum() / body.sum()
            info.append((cx, bot))
        L = max(cx for cx, _ in info); R = max(f.size[0] - cx for f, (cx, _) in zip(fr, info))
        U = max(b for _, b in info); cw, ch = int(np.ceil(L + R)) + 2, int(U) + 3
        strip = Image.new("RGBA", (cw * 8, ch))
        for i, (f, (cx, b)) in enumerate(zip(fr, info)):
            strip.alpha_composite(f, (int(round(i * cw + L - cx)) + 1, int(round(U - b))))
        strip.save(os.path.join(out, run + ".webp"), quality=86, method=6)
        meta[run] = {"img": "art/cast/%s.webp" % run, "of": who, "cell": [cw, ch], "frames": 8, "anchor": [round(float(L) + 1, 1), int(U)]}
    items = []
    for n, hfrac in PROPS.items():
        im = load(os.path.join(SRC, "props", n + ".webp")); k = hfrac * 1072 * OVER / im.size[1]
        items.append((n, im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS)))
    sheet, pos = shelf(items); sheet.save(os.path.join(out, "props.webp"), quality=88, method=6)
    meta["props"] = {"img": "art/cast/props.webp", "poses": {n: [int(pos[n][0]), int(pos[n][1]), im.size[0], im.size[1], im.size[0] / 2, im.size[1] / 2] for n, im in items}}
    for v in meta.values(): v.pop("_k", None)
    meta["_over"] = OVER
    json.dump(meta, open(os.path.join(out, "cast.json"), "w"), indent=1)
    tot = sum(os.path.getsize(f) for f in glob.glob(os.path.join(out, "*.webp")))
    print("cast:", len(meta) - 1, "sheets,", round(tot / 1024), "KB")

if __name__ == "__main__":
    main(sys.argv[1])
