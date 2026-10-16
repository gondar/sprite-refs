"""Mountain King, eight idle gestures from four H3 clips (two gestures per clip, home pose at 0, 2 and 4 s).

Every gesture must start and end on ONE shared home frame, so the game can play them in any order with no
jump at the seam. The home frame is the shipped idle strip's frame 0 (so idle -> nod -> cheer still meet).

  mountain_king_idle8.py prep  OUT JOB [JOB ...]       extract + key + register + static fix, print the curves
  mountain_king_idle8.py cut   OUT NAME=JOB:t0-t1 ...   cut, ease both ends into the home frame, pack an atlas

prep: every frame is keyed on its own border (the background drifts), then REGISTERED to the home frame by
the throne and legs (the bottom 28 % of the figure never moves): the scale is the width of that region, the
offset its bottom centre, per frame and median-smoothed (H3 zooms a little while it settles from the
reference image). Below that line alpha is clipped to the home frame's silhouette and colour is matched to it
by per-channel gains on the same static region (mountain_king_fix.py, the same rescue). Prints, per clip, the
distance of the moving part to the home frame every 1/12 s: the home pose is where it dips.

cut: keeps every 2nd frame (12 fps), then crossfades the first and last EASE frames into the home frame, so
frame 0 and the last frame of every gesture ARE the home frame. Packs all gestures into one atlas (a row per
gesture, a column per frame, equal cells) + JSON, and a GIF of a random mix."""
import glob, json, os, subprocess, sys, importlib.util, random
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("key", os.path.join(HERE, "..", "skill", "sprite-pipeline", "scripts", "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

CELL = (479, 444)               # the nod/cheer cell; the old idle cell (379 wide) is placed in it on its pivot
PIVOT = (245.6, 442.8)
HALO = 16                       # px around the home silhouette a gesture may reach
COLS = 24
UPPER = {"20261016-135850-b65102"}   # framed too close: fitted on the upper body (upper_fit)
STATIC = 0.72                   # below this fraction of the figure height nothing moves (throne, legs, feet)


def home():
    sh = os.path.join(HERE, "..", "sheets", "mountain-king")
    meta = json.load(open(os.path.join(sh, "king-idle.json")))
    strip = Image.open(os.path.join(sh, "king-idle.png")).convert("RGBA")
    cw, ch = meta["cell"]
    f0 = strip.crop((0, 0, cw, ch))
    c = Image.new("RGBA", CELL, (0, 0, 0, 0))
    c.alpha_composite(f0, (int(round(PIVOT[0] - meta["pivot"][0])), int(round(PIVOT[1] - meta["pivot"][1]))))
    return np.asarray(c, dtype=float)


def static_box(al, top, bot):
    cut = int(top + STATIC * (bot - top))
    ys, xs = np.nonzero(al[cut:])
    return xs.min(), xs.max(), ys.max() + cut, cut


def figure(al):
    ys = np.where(al.any(1))[0]
    return ys.min(), ys.max()


def prep(out, jobs):
    H = home(); ha = H[..., 3] > 128
    htop, hbot = figure(ha)
    hx0, hx1, hyb, hcut = static_box(ha, htop, hbot)
    hmask = ndi.binary_dilation(ha, iterations=5)
    halo = ndi.binary_dilation(ha, iterations=HALO)   # a subtle gesture never leaves this: steam, glows and the
                                                      # drifting background's vignette all do
    stat = np.zeros_like(ha); stat[hcut:] = True; stat &= ndi.binary_erosion(ha, iterations=6)
    hmean = H[stat][:, :3].mean(0)
    curves = {}
    for job in jobs:
        src = os.path.join(out, job, "src"); os.makedirs(src, exist_ok=True)
        if not glob.glob(os.path.join(src, "f_*.png")):
            subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "..", "raw", job + ".mp4"), "-vf", "fps=24",
                            os.path.join(src, "f_%03d.png")], check=True)
        fs = sorted(glob.glob(os.path.join(src, "f_*.png")))
        keyed, geo = [], []
        for f in fs:
            k = key.key_image(np.array(Image.open(f).convert("RGB")), "border")[0]
            al = k[..., 3] > 128
            lab, n = ndi.label(ndi.binary_dilation(al, iterations=3))
            if n > 1:
                big = 1 + int(np.argmax(ndi.sum(np.ones_like(lab), lab, range(1, n + 1))))
                k[..., 3] = np.where(lab == big, k[..., 3], 0); al = k[..., 3] > 128
            top, bot = figure(al)
            if job in UPPER: keyed.append(k); geo.append((1, 0, 0)); continue
            x0, x1, yb, _ = static_box(al, top, bot)
            keyed.append(k); geo.append(((hx1 - hx0) / (x1 - x0), (x0 + x1) / 2, yb))
        g = np.array(geo)
        if job in UPPER: g = upper_fit(keyed, H, hcut, ha)
        else: g = np.stack([ndi.median_filter(g[:, i], size=9, mode="nearest") for i in range(3)], 1)
        dst = os.path.join(out, job, "reg"); os.makedirs(dst, exist_ok=True)
        cur = []
        for i, (k, row) in enumerate(zip(keyed, g)):
            if job in UPPER:                      # output (u, v) = input * s + (U0, V0)
                s, U0, V0 = row[0], row[3], row[4]
                a, b, c, d, e, f_ = 1 / s, 0, -U0 / s, 0, 1 / s, -V0 / s
            else:                                 # output (u, v) <- input ((u - hcx)/s + cx, (v - hyb)/s + yb)
                s, cx, yb = row
                hcx = (hx0 + hx1) / 2
                a, b, c = 1 / s, 0, cx - hcx / s
                d, e, f_ = 0, 1 / s, yb - hyb / s
            im = Image.fromarray(np.round(k).astype(np.uint8), "RGBA").transform(CELL, Image.AFFINE, (a, b, c, d, e, f_), Image.BICUBIC)
            im = np.asarray(im, dtype=float).copy()
            al = im[..., 3]
            al[hcut:] = np.where(hmask[hcut:], al[hcut:], 0)
            if job in UPPER:                      # below the line the clip has no feet: the home frame stands in
                band = 24                         # rows over which the clip fades into the home frame
                w = np.clip((np.arange(CELL[1]) - (hcut - band)) / band, 0, 1)[:, None]
                pa = al / 255 * (1 - w) + H[..., 3] / 255 * w
                rgb = (im[..., :3] * (al / 255)[..., None] * (1 - w[..., None]) + H[..., :3] * (H[..., 3:4] / 255) * w[..., None]) / np.maximum(pa, 1e-3)[..., None]
                im[..., :3] = rgb; al = pa * 255
            al[:hcut] = np.where(halo[:hcut], al[:hcut], 0)
            # the King has no magenta in him: what is left of it is steam lit by the background, or its spill
            pink = np.minimum(im[..., 0], im[..., 2]) - im[..., 1]
            al *= np.clip(1 - (pink - 70) / 50, 0, 1)
            sel = stat & (al > 200)
            if sel.sum() > 500:
                gain = hmean / np.maximum(im[sel][:, :3].mean(0), 1)
                im[..., :3] = np.clip(im[..., :3] * gain, 0, 255)
            im[..., 3] = al
            Image.fromarray(im.astype(np.uint8)).save(os.path.join(dst, f"f_{i:03d}.png"))
            cur.append(dist(im, H, hcut))
        curves[job] = cur
        print(job, f"scale {g[:, 0].min():.3f}–{g[:, 0].max():.3f}")
        print("  dist to home per 1/12 s:", " ".join(f"{j / 24:.2f}:{cur[j]:.1f}" for j in range(0, len(cur), 2)))
    json.dump(curves, open(os.path.join(out, "curves.json"), "w"))


def upper_fit(keyed, H, hcut, ha):
    """a clip framed so close that the throne's foot is out of the picture: fit ONE scale and offset on the
    upper body of its first (home-pose) frame by silhouette overlap with the home frame — the camera is locked,
    so it holds for the whole clip — and let the home frame supply everything below the static line."""
    k0 = keyed[0][..., 3] > 128
    hcx = None
    ref = ha[:hcut]
    best = (-1, None)
    ys, xs = np.nonzero(k0)
    for s in np.arange(0.30, 0.80, 0.01):
        # place: output (u,v) = ((x - cx)*s + U, (y - cy)*s + V); search U,V by aligning the crown top and centre
        u = xs * s; v = ys * s
        for dv in range(-20, 21, 4):
            V0 = np.nonzero(ref.any(1))[0].min() - v.min() + dv
            for du in range(-20, 21, 4):
                U0 = np.nonzero(ref.any(0))[0].mean() - u.mean() + du
                uu = (u + U0).astype(int); vv = (v + V0).astype(int)
                ok = (uu >= 0) & (uu < CELL[0]) & (vv >= 0) & (vv < hcut)
                m = np.zeros_like(ref); m[vv[ok], uu[ok]] = True
                iou = (m & ref).sum() / max(1, (m | ref).sum())
                if iou > best[0]: best = (iou, (s, U0, V0))
    s, U0, V0 = best[1]
    print(f"  upper fit: scale {s:.2f}, IoU {best[0]:.3f}")
    # express as (scale, cx, yb) for the shared affine: output = (x - cx)*S + hcx_ref, (y - yb)*S + hyb_ref
    return None if False else np.array([[s, 0, 0, U0, V0]] * len(keyed))


def dist(im, H, cut):
    """mean |premultiplied RGB difference| over the moving part (above the static line), at 1/4 resolution"""
    def pm(x): return (x[:cut, :, :3] * x[:cut, :, 3:4] / 255)[::4, ::4]
    return float(np.abs(pm(im) - pm(H)).mean())


def cut(out, specs, ease=2, step=2):
    H = home(); hcut = int(figure(H[..., 3] > 128)[0] + STATIC * np.subtract(*figure(H[..., 3] > 128)[::-1]))
    rows = []
    for spec in specs:
        name, rest = spec.split("=")
        job, rng = rest.split(":")
        t0, t1 = map(float, rng.split("-"))
        fs = sorted(glob.glob(os.path.join(out, job, "reg", "f_*.png")))
        i0, i1 = int(round(t0 * 24)), min(len(fs) - 1, int(round(t1 * 24)))
        fr = [np.asarray(Image.open(fs[i]), dtype=float) for i in range(i0, i1 + 1, step)]
        n = len(fr)
        seq = []
        for j, f in enumerate(fr):
            w = 1.0
            if j < ease: w = j / ease                       # 0 at the first frame: exactly home
            if n - 1 - j < ease: w = min(w, (n - 1 - j) / ease)
            pa = f[..., 3:4] / 255 * w + H[..., 3:4] / 255 * (1 - w)
            rgb = (f[..., :3] * f[..., 3:4] / 255 * w + H[..., :3] * H[..., 3:4] / 255 * (1 - w)) / np.maximum(pa, 1e-3)
            seq.append(np.dstack([rgb, pa * 255]))
        rows.append((name, seq, job, t0, t1))
        print(f"{name}: {job} {t0:.2f}-{t1:.2f} s, {n} frames, seam-in {dist(fr[0], H, hcut):.1f}, seam-out {dist(fr[-1], H, hcut):.1f}")
    # frames flow row-major through a fixed-width atlas (a WebP side may not pass 16383 px); a gesture is a run
    cw, ch = CELL
    allf = [f for _, seq, *_ in rows for f in seq]
    nrows = (len(allf) + COLS - 1) // COLS
    atlas = Image.new("RGBA", (cw * COLS, ch * nrows), (0, 0, 0, 0))
    for i, f in enumerate(allf):
        atlas.alpha_composite(Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8)), ((i % COLS) * cw, (i // COLS) * ch))
    atlas.save(os.path.join(out, "king-idle8.png"))
    gs, at = [], 0
    for nm, seq, job, t0, t1 in rows:
        gs.append({"name": nm, "at": at, "frames": len(seq), "src": f"{job} {t0}-{t1}s"}); at += len(seq)
    meta = {"cell": list(CELL), "pivot": list(PIVOT), "fps": 24 / step, "cols": COLS, "rows": nrows, "gestures": gs}
    json.dump(meta, open(os.path.join(out, "king-idle8.json"), "w"), indent=1)
    # review: eight evenly spaced frames of every gesture, big enough to judge
    rv = Image.new("RGB", (8 * 200, 186 * len(rows)), (42, 30, 58))
    for r, (_, seq, *_) in enumerate(rows):
        for k in range(8):
            f = Image.fromarray(np.clip(np.round(seq[round(k * (len(seq) - 1) / 7)]), 0, 255).astype(np.uint8)).resize((200, 186), Image.LANCZOS)
            rv.paste(f, (k * 200, r * 186), f)
    rv.save(os.path.join(out, "review.png"))
    # a random mix, as the game plays it: shuffled bag, a short rest on the home frame between gestures
    rnd = random.Random(7); order = []
    for _ in range(2):
        bag = list(range(len(rows))); rnd.shuffle(bag); order += bag
    gif = []
    bg = Image.new("RGB", CELL, (42, 30, 58))
    def frame(a):
        b = bg.copy(); b.paste(Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)), (0, 0), Image.fromarray(np.clip(a[..., 3], 0, 255).astype(np.uint8)))
        return b.resize((cw // 2, ch // 2), Image.LANCZOS)
    for g in order:
        gif += [frame(H)] * rnd.randint(3, 10)
        gif += [frame(f) for f in rows[g][1]]
    gif[0].save(os.path.join(out, "king-idle8-mix.gif"), save_all=True, append_images=gif[1:], duration=round(1000 * step / 24), loop=0)
    print(json.dumps(meta)[:400])


if __name__ == "__main__":
    if sys.argv[1] == "prep": prep(sys.argv[2], sys.argv[3:])
    else: cut(sys.argv[2], sys.argv[3:])
