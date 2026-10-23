"""Abordaż animation strips: from the generated pose sheets (refs/abordaz/gen/anim/*.webp, magenta ground) to
equal-cell WebP strips for fingerpick-warmup/art/abordaz/, plus the extra sea plates (refs/abordaz/gen/seas/*.webp).
Run from the sprite-refs root: python3 scripts/abordaz_anim.py /home/user/MusicGames

Each sheet is a grid of frames of ONE loop. A frame is keyed, reduced to its largest figure, then shifted so its
anchor (the boots' centre, the back boot for the fencer, the beak's tip for the gull) sits where frame 1's does;
all frames are cut with one union box, so the strip plays in place. `ref` in the meta is frame 1's figure height
in strip pixels: the game sizes a strip by it, so a crouching pose is not blown up to a standing one's height."""
import sys, os, json, importlib.util
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

MG = sys.argv[1]
FP = os.path.join(MG, "fingerpick-warmup/art/abordaz")
spec = importlib.util.spec_from_file_location("key", "skill/asset-sheet/scripts/key.py"); key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)
G = "refs/abordaz/gen/anim"

def cells(path, rows, cols, take=None):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(float)
    rgba, _ = key.key_image(rgb, "magenta")
    H, W = rgba.shape[:2]; ch, cw = H // rows, W // cols
    out = []
    for i in range(rows * cols):
        if take and i not in take: continue
        r, c = divmod(i, cols)
        a = rgba[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw].copy()
        m = a[:, :, 3] > 40
        lab, n = ndi.label(ndi.binary_dilation(m, iterations=4))
        if n > 1:
            sizes = ndi.sum(m, lab, range(1, n + 1)); keep = lab == (1 + int(np.argmax(sizes)))
            a[~keep, 3] = 0
        out.append(a)
    return out

def bbox(a):
    ys, xs = np.where(a[:, :, 3] > 40); return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

def anchor(a, how):
    x0, y0, x1, y1 = bbox(a)
    if how == "beak":   # the gull: the tip of its yellow beak (the rightmost orange pixel; the feet are at the back)
        r, g, b, al = (a[:, :, i] for i in range(4))
        ys, xs = np.where((r > 170) & (g > 100) & (g < 210) & (b < 120) & (al > 200))
        i = int(np.argmax(xs)); return float(xs[i]), float(ys[i])
    band = a[y1 - max(4, (y1 - y0) // 14):y1, :, 3] > 40      # the boots
    xs = np.where(band.any(0))[0]
    if how == "back": return float(xs.min()), float(y1)
    return float(xs.mean()), float(y1)

def hat_w(a):   # the black tricorne: the widest run of dark pixels in the top third
    x0, y0, x1, y1 = bbox(a)
    top = a[y0:y0 + (y1 - y0) // 3]
    lum = top[:, :, :3].mean(2); dark = (lum < 80) & (top[:, :, 3] > 200)
    xs = np.where(dark.any(0))[0]; return float(xs.max() - xs.min())

def height(a): b = bbox(a); return float(b[3] - b[1])

def prep(frames, metric):
    """Every frame to frame 1's scale (the model draws some frames of a sheet a size smaller: the singer's last two
    came out 7% short), by `metric` — the figure's height for a standing pose, the hat's width for the fencer —
    then padded, so a lunge shifted onto the back boot is never cut at its cell's edge."""
    m0 = metric(frames[0]) if metric else 1; out = []
    for a in frames:
        f = m0 / metric(a) if metric else 1
        if abs(f - 1) > .01:
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
            a = np.asarray(im.resize((round(im.size[0] * f), round(im.size[1] * f)), Image.LANCZOS)).astype(float)
        out.append(np.pad(a, ((300, 300), (300, 300), (0, 0))))
    H = max(a.shape[0] for a in out); W = max(a.shape[1] for a in out)
    return [np.pad(a, ((0, H - a.shape[0]), (0, W - a.shape[1]), (0, 0))) for a in out]

def strip(frames, how, target_ref, name, scale=None, metric=None):
    frames = prep(frames, metric)
    ax0, ay0 = anchor(frames[0], how)
    shifted = []
    for a in frames:
        ax, ay = anchor(a, how); dx, dy = int(round(ax0 - ax)), int(round(ay0 - ay))
        b = np.zeros_like(a); H, W = a.shape[:2]
        sy0, sy1 = max(0, -dy), min(H, H - dy); sx0, sx1 = max(0, -dx), min(W, W - dx)
        b[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx] = a[sy0:sy1, sx0:sx1]
        shifted.append(b)
    boxes = [bbox(b) for b in shifted]
    X0 = min(b[0] for b in boxes) - 3; Y0 = min(b[1] for b in boxes) - 3; X1 = max(b[2] for b in boxes) + 3; Y1 = max(b[3] for b in boxes) + 3
    ref = boxes[0][3] - boxes[0][1]
    k = scale if scale else target_ref / ref
    cw, chh = round((X1 - X0) * k), round((Y1 - Y0) * k)
    out = Image.new("RGBA", (cw * len(shifted), chh), (0, 0, 0, 0))
    for i, b in enumerate(shifted):
        im = Image.fromarray(np.clip(b[Y0:Y1, X0:X1], 0, 255).astype(np.uint8), "RGBA").resize((cw, chh), Image.LANCZOS)
        out.alpha_composite(im, (i * cw, 0))
    out.save(os.path.join(FP, name + ".webp"), "WEBP", quality=84, method=6)
    return {"cell": [cw, chh], "frames": len(shifted), "ref": round(ref * k, 1),
            "anchor": [round((ax0 - X0) * k, 1), round((ay0 - Y0) * k, 1)]}, k

meta = {}
sing = cells(G + "/szabla-sing.webp", 2, 2)
meta["szabla-sing"], ks = strip(sing, "mid", 420, "szabla-sing", metric=height)
fence = cells(G + "/szabla-fence2.webp", 2, 3)
# the same head size as the singer: the hat metric matches the strips' dark pixels, which in the crouch include the
# navy coat, so it came out 20% small; 1.25 is the face-to-face match read off a side-by-side (/tmp cmp, 2026-10-23)
kf = ks * hat_w(sing[0]) / hat_w(fence[0]) * 1.25
meta["szabla-fence"], _ = strip(fence, "back", None, "szabla-fence", scale=kf)   # the sheet drew these six at one size; the hat metric is fooled by the raised sword
grz = cells(G + "/grzmot-idle.webp", 2, 2)
meta["grzmot-idle"], _ = strip(grz, "mid", 420, "grzmot-idle", metric=height)
gull = cells(G + "/gull-flap.webp", 2, 4)
gull = [gull[i] for i in (0, 1, 2, 4, 5, 6, 3, 7)]     # wings up → level → down → rising (the sheet's order wandered)
gk = 150 / max(bbox(g)[2] - bbox(g)[0] for g in gull)
meta["gull-flap"], _ = strip(gull, "beak", None, "gull-flap", scale=gk)

# the extra sea plates: the paper's edge trimmed off, 2400 wide like sea.webp, the horizon measured
seas = {}
for n in ["dawn", "dusk", "night", "caribbean", "mediterranean", "antarctic", "pacific"]:
    im = Image.open("refs/abordaz/gen/seas/" + n + ".webp").convert("RGB")
    w, h = im.size; m = round(w * .012)
    im = im.crop((m, m, w - m, h - m)).resize((2400, round(2400 * (h - 2 * m) / (w - 2 * m))), Image.LANCZOS)
    im.save(os.path.join(FP, "sea-" + n + ".webp"), "WEBP", quality=78, method=6)
    a = np.asarray(im).astype(float).mean(2); prof = np.abs(np.diff(ndi.uniform_filter1d(a.mean(1), 5)))
    lo, hi = int(len(prof) * .3), int(len(prof) * .58)
    hz = (lo + int(np.argmax(prof[lo:hi]))) / im.size[1]
    seas[n] = {"w": im.size[0], "h": im.size[1], "horizon": round(hz, 3)}
meta["seas"] = seas
p = os.path.join(FP, "art.json"); art = json.load(open(p)); art.update(meta)
json.dump(art, open(p, "w"), indent=1)
print(json.dumps(meta, indent=1))
