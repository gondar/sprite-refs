#!/usr/bin/env python3
"""Cut H3 clips of "home pose -> pose -> home pose -> pose …" (one pose per second) into gestures that all
start and end on ONE shared home frame, so a game can play them in any order with no seam. Packs an atlas.

usage: gestures.py OUT CLIP.mp4=name,name,name,name [CLIP2.mp4=…] [--pose-s 1.0] [--home STRIP.json[:FRAME]]
                   [--cell W,H --pivot X,Y] [--static 0.72] [--halo 16] [--step 2] [--ease 2] [--webp 70]

What it does, per clip (re-runnable; extracted frames are cached in OUT/<clip>/src):
  1. extract at 24 fps, key every frame on its OWN border (H3 drifts the background: magenta -> lavender ->
     teal/black in the second half of a clip), keep the largest blob.
  2. register every frame to the home frame. --static F: the bottom (1-F) of the figure never moves (a seated
     or standing character's legs/feet/throne) — its width gives the scale, its bottom centre the offset, per
     frame, median-smoothed (H3 zooms while it settles from the reference image). If a clip is framed so close
     that the figure touches the bottom edge, it fits one scale+offset on the UPPER body by silhouette overlap
     instead and the home frame supplies everything below the static line. --static 0 = no registration.
  3. clean: below the static line alpha is clipped to the home silhouette and colour is matched to it by
     per-channel gains (undoes drifting brightness: one gain per band of the body, interpolated per row — never per channel); above it alpha is clipped to the home silhouette dilated by
     --halo px (steam, glows, vignettes), anything the key colour is faded out, and everything 10 px inside the
     home silhouette is made opaque (a light drifted ground keys the stone's highlights half see-through).
  4. find the cuts: the distance of the moving part to the home frame, printed every 1/12 s; a cut is the
     minimum within +-0.35 s of each k * --pose-s. Never trust the prompt's clock — read the curve.
  5. keep every --step-th frame and crossfade --ease frames at each end INTO the home frame, so frame 0 and
     the last frame of every gesture ARE the home frame (2 frames; 3 ghosts visibly).
Output: OUT/atlas.png (+ .webp), OUT/atlas.json {cell, pivot, fps, cols, rows, gestures:[{name, at, frames}]}
(row-major, cols chosen so no side passes WebP's 16383 px), OUT/review.png (8 frames per gesture) and
OUT/mix.gif (a shuffled bag with rests, as a game plays it). Play: frame i is cell (i % cols, i // cols).

--home: a pack.py strip JSON (its PNG beside it) and a frame index — use the character's EXISTING idle frame
so the new gestures meet its other animations; without it, home = the first clip's frame 0 (the reference
image's framing). --cell/--pivot place that frame in a bigger cell (room for an arm or a tilt)."""
import argparse, glob, json, os, random, subprocess, importlib.util
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("key", os.path.join(HERE, "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)
FPS = 24


def figure(al):
    ys = np.where(al.any(1))[0]
    return ys.min(), ys.max()


def largest(k):
    al = k[..., 3] > 128
    lab, n = ndi.label(ndi.binary_dilation(al, iterations=3))
    if n > 1:
        big = 1 + int(np.argmax(ndi.sum(np.ones_like(lab), lab, range(1, n + 1))))
        k[..., 3] = np.where(lab == big, k[..., 3], 0)
    return k


def load_home(a):
    if a.home:
        path, _, fi = a.home.partition(":")
        meta = json.load(open(path)); strip = Image.open(path[:-5] + ".png").convert("RGBA")
        cw, ch = meta["cell"]; fi = int(fi or 0)
        f = strip.crop((fi * cw, 0, fi * cw + cw, ch)); pv = meta["pivot"]
        if a.cell:
            W, H = map(int, a.cell.split(",")); PV = list(map(float, a.pivot.split(",")))
            c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            c.alpha_composite(f, (int(round(PV[0] - pv[0])), int(round(PV[1] - pv[1])))); f, pv = c, PV
        return np.asarray(f, dtype=float), list(pv)
    return None, None


class Home:
    def __init__(self, H, pivot, static, halo):
        self.H, self.pivot = H, pivot
        ha = H[..., 3] > 128; self.ha = ha
        top, bot = figure(ha)
        self.cut = int(top + static * (bot - top)) if static else H.shape[0]
        if static:
            ys, xs = np.nonzero(ha[self.cut:])
            self.x0, self.x1, self.yb = xs.min(), xs.max(), ys.max() + self.cut
        self.mask = ndi.binary_dilation(ha, iterations=5)
        self.halo = ndi.binary_dilation(ha, iterations=halo)
        st = np.zeros_like(ha); st[self.cut:] = True
        self.stat = st & ndi.binary_erosion(ha, iterations=6)
        self.mean = H[self.stat][:, :3].mean(0) if self.stat.sum() > 500 else None
        self.body = ndi.binary_erosion(ha, iterations=8)
        self.inner = ndi.binary_erosion(ha, iterations=10)
        self.keyc = "green" if np.median(H[ha][:, 1]) > 250 else "magenta"   # (only used to fade key colour)

    def dist(self, im):
        """mean |premultiplied RGBA difference| over the moving part (above the static line), 1/4 resolution"""
        def pm(x): return np.dstack([x[:self.cut, :, :3] * x[:self.cut, :, 3:4] / 255, x[:self.cut, :, 3:4]])[::4, ::4]
        return float(np.abs(pm(im) - pm(self.H)).mean())


def static_geo(al, static):
    top, bot = figure(al); cut = int(top + static * (bot - top))
    ys, xs = np.nonzero(al[cut:])
    return xs.min(), xs.max(), ys.max() + cut


def upper_fit(k0, hm):
    """one scale + offset for a clip framed too close (camera locked): best silhouette overlap of its first
    frame's alpha with the home frame's, above the static line"""
    ref = hm.ha[:hm.cut]; ys, xs = np.nonzero(k0[..., 3] > 128); best = (-1, None)
    rtop, rcx = np.nonzero(ref.any(1))[0].min(), np.nonzero(ref.any(0))[0].mean()
    for s in np.arange(0.25, 1.6, 0.01):
        u, v = xs * s, ys * s
        for dv in range(-20, 21, 4):
            for du in range(-20, 21, 4):
                U0, V0 = rcx - u.mean() + du, rtop - v.min() + dv
                uu, vv = (u + U0).astype(int), (v + V0).astype(int)
                ok = (uu >= 0) & (uu < ref.shape[1]) & (vv >= 0) & (vv < hm.cut)
                m = np.zeros_like(ref); m[vv[ok], uu[ok]] = True
                iou = (m & ref).sum() / max(1, (m | ref).sum())
                if iou > best[0]: best = (iou, (s, U0, V0))
    print(f"  framed too close: upper-body fit, scale {best[1][0]:.2f}, overlap {best[0]:.3f}")
    return best[1]


def prep_clip(a, clip, hm):
    name = os.path.splitext(os.path.basename(clip))[0]
    src = os.path.join(a.out, name, "src"); os.makedirs(src, exist_ok=True)
    if not glob.glob(os.path.join(src, "f_*.png")):
        subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"fps={FPS}", os.path.join(src, "f_%03d.png")], check=True)
    raws = [np.array(Image.open(f).convert("RGB")) for f in sorted(glob.glob(os.path.join(src, "f_*.png")))]
    keyed = [largest(key.key_image(r, "border")[0]) for r in raws]
    if hm is None:      # home = this clip's first frame, cropped with a margin
        al = keyed[0][..., 3] > 40; ys, xs = np.nonzero(al); m = 40
        crop = keyed[0][max(0, ys.min() - m):ys.max() + 4, max(0, xs.min() - m):xs.max() + m + 1]
        H = crop.copy(); pv = [H.shape[1] / 2, H.shape[0] - 3]
        hm = Home(H, pv, a.static, a.halo)
    W, Hh = hm.H.shape[1], hm.H.shape[0]
    close = a.static and any((k[-3:, :, 3] > 128).any() for k in keyed[:3])
    if close: s0, U0, V0 = upper_fit(keyed[0], hm)
    elif a.static:
        g = np.array([static_geo(k[..., 3] > 128, a.static) for k in keyed], dtype=float)
        g = np.stack([ndi.median_filter(g[:, i], size=9, mode="nearest") for i in range(3)], 1)
    out, cur = [], []
    for i, k in enumerate(keyed):
        if close: s, cx, cy = s0, -U0 / s0, -V0 / s0                       # input = output / s + (cx, cy)
        elif a.static:
            x0, x1, yb = g[i]; s = (hm.x1 - hm.x0) / (x1 - x0)
            cx, cy = (x0 + x1) / 2 - (hm.x0 + hm.x1) / 2 / s, yb - hm.yb / s
        else:
            s, cx, cy = 1.0, 0, 0
        im = Image.fromarray(np.round(k).astype(np.uint8), "RGBA").transform((W, Hh), Image.AFFINE, (1 / s, 0, cx, 0, 1 / s, cy), Image.BICUBIC)
        im = np.asarray(im, dtype=float).copy(); al = im[..., 3]
        raw = np.asarray(Image.fromarray(raws[i]).transform((W, Hh), Image.AFFINE, (1 / s, 0, cx, 0, 1 / s, cy), Image.BICUBIC), dtype=float)
        c = hm.cut
        if a.static:
            al[c:] = np.where(hm.mask[c:], al[c:], 0)
            if close:   # no feet in this clip: fade into the home frame over 24 rows above the line
                w = np.clip((np.arange(Hh) - (c - 24)) / 24, 0, 1)[:, None]
                pa = al / 255 * (1 - w) + hm.H[..., 3] / 255 * w
                im[..., :3] = (im[..., :3] * (al / 255)[..., None] * (1 - w[..., None]) + hm.H[..., :3] * (hm.H[..., 3:4] / 255) * w[..., None]) / np.maximum(pa, 1e-3)[..., None]
                al = pa * 255
        al[:c] = np.where(hm.halo[:c], al[:c], 0)
        # inside the home silhouette the figure is opaque: a light drifted ground (pale green) sits close to the
        # stone's highlights in colour distance, and the key left the face 20 % see-through. Key only the edges.
        # … with the clip's ORIGINAL pixels there: the key's edge un-mixing, (pix - (1-a)·ground) / a, subtracts a
        # green ground from a pixel it wrongly called half transparent and paints the stone purple (and vice versa)
        al[hm.inner] = 255; im[hm.inner, :3] = raw[hm.inner]
        r_, g_, b_ = im[..., 0], im[..., 1], im[..., 2]
        ex = np.minimum(r_, b_) - g_ if hm.keyc == "magenta" else g_ - np.maximum(r_, b_)
        al *= np.clip(1 - (ex - 70) / 50, 0, 1)
        # brightness, not hue: one gain per horizontal band of the whole body (frame ∩ home), interpolated per row.
        # The home frame is itself lit by its magenta ground, so per-CHANNEL gains painted a neutral frame (shot on
        # a drifted green ground) magenta-purple; gains on the throne alone over-corrected the face.
        sel = hm.body & (al > 200)
        if sel.sum() > 500:
            ys = np.nonzero(sel.any(1))[0]; edges = np.linspace(ys.min(), ys.max() + 1, 5).astype(int)
            cy, gn = [], []
            for b0, b1 in zip(edges[:-1], edges[1:]):
                m = np.zeros_like(sel); m[b0:b1] = sel[b0:b1]
                if m.sum() > 200:
                    cy.append((b0 + b1) / 2); gn.append(np.repeat(hm.H[m][:, :3].mean() / max(im[m][:, :3].mean(), 1), 3))
            gn = np.array(gn); rows_ = np.arange(Hh)
            gain = np.stack([np.interp(rows_, cy, gn[:, ch]) for ch in range(3)], 1)[:, None, :]
            im[..., :3] = np.clip(im[..., :3] * gain, 0, 255)
        im[..., 3] = al
        out.append(im); cur.append(hm.dist(im))
    return name, out, cur, hm


def cuts(cur, n, pose_s):
    """cut k at the minimum of the distance within +-0.35 s of k * pose_s (k = 0..n)"""
    res, w = [], int(0.35 * FPS)
    for k in range(n + 1):
        c = min(len(cur) - 1, int(round(k * pose_s * FPS)))
        lo, hi = max(0, c - w), min(len(cur), c + w + 1)
        res.append(lo + int(np.argmin(cur[lo:hi])))
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("clips", nargs="+")
    ap.add_argument("--pose-s", type=float, default=1.0); ap.add_argument("--home"); ap.add_argument("--cell"); ap.add_argument("--pivot")
    ap.add_argument("--static", type=float, default=0.72); ap.add_argument("--halo", type=int, default=16)
    ap.add_argument("--step", type=int, default=2); ap.add_argument("--ease", type=int, default=2); ap.add_argument("--webp", type=int, default=70)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    H, pv = load_home(a)
    hm = Home(H, pv, a.static, a.halo) if H is not None else None
    rows = []
    for spec_ in a.clips:
        clip, _, names = spec_.partition("=")
        names = names.split(",")
        name, frames, cur, hm = prep_clip(a, clip, hm)
        base = float(np.percentile(cur, 10))
        print(f"{name}: distance to home every 1/12 s:", " ".join(f"{j / FPS:.2f}:{cur[j]:.1f}" for j in range(0, len(cur), 2)))
        cs = cuts(cur, len(names), a.pose_s)
        for k, nm in enumerate(names):
            i0, i1 = cs[k], cs[k + 1]
            flag = "  <- does not come home, check the clip" if max(cur[i0], cur[i1]) > 1.6 * base + 1 else ""
            print(f"  {nm}: {i0 / FPS:.2f}-{i1 / FPS:.2f} s, ends at {cur[i0]:.1f} / {cur[i1]:.1f} (floor {base:.1f}){flag}")
            fr = frames[i0:i1 + 1:a.step]; n = len(fr); seq = []
            for j, f in enumerate(fr):
                w = min(1.0, j / a.ease, (n - 1 - j) / a.ease) if a.ease else 1.0
                pa = f[..., 3:4] / 255 * w + hm.H[..., 3:4] / 255 * (1 - w)
                rgb = (f[..., :3] * f[..., 3:4] / 255 * w + hm.H[..., :3] * hm.H[..., 3:4] / 255 * (1 - w)) / np.maximum(pa, 1e-3)
                seq.append(np.dstack([rgb, pa * 255]))
            rows.append((nm, seq, f"{name} {i0 / FPS:.2f}-{i1 / FPS:.2f}s"))
    Hh, W = hm.H.shape[:2]
    allf = [f for _, s, _ in rows for f in s]
    cols = min(len(allf), 16383 // W); nr = (len(allf) + cols - 1) // cols
    atlas = Image.new("RGBA", (W * cols, Hh * nr), (0, 0, 0, 0))
    u8 = lambda f: Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8))
    for i, f in enumerate(allf): atlas.alpha_composite(u8(f), ((i % cols) * W, (i // cols) * Hh))
    atlas.save(os.path.join(a.out, "atlas.png"))
    if a.webp: atlas.save(os.path.join(a.out, "atlas.webp"), "WEBP", quality=a.webp, method=6, alpha_quality=90)
    gs, at = [], 0
    for nm, s, src in rows: gs.append({"name": nm, "at": at, "frames": len(s), "src": src}); at += len(s)
    meta = {"cell": [W, Hh], "pivot": [round(v, 1) for v in hm.pivot], "fps": FPS / a.step, "cols": cols, "rows": nr, "gestures": gs}
    json.dump(meta, open(os.path.join(a.out, "atlas.json"), "w"), indent=1)
    tw, th = 200, round(200 * Hh / W)
    rv = Image.new("RGB", (8 * tw, th * len(rows)), (42, 30, 58))
    for r, (_, s, _) in enumerate(rows):
        for k in range(8):
            f = u8(s[round(k * (len(s) - 1) / 7)]).resize((tw, th), Image.LANCZOS); rv.paste(f, (k * tw, r * th), f)
    rv.save(os.path.join(a.out, "review.png"))
    rnd, order, gif = random.Random(7), [], []
    for _ in range(2):
        bag = list(range(len(rows))); rnd.shuffle(bag); order += bag
    bg = Image.new("RGB", (W, Hh), (42, 30, 58))
    def fr_(x):
        b = bg.copy(); im = u8(x); b.paste(im, (0, 0), im); return b.resize((W // 2, Hh // 2), Image.LANCZOS)
    for g in order:
        gif += [fr_(hm.H)] * rnd.randint(3, 10) + [fr_(f) for f in rows[g][1]]
    gif[0].save(os.path.join(a.out, "mix.gif"), save_all=True, append_images=gif[1:], duration=round(1000 * a.step / FPS), loop=0)
    print(json.dumps({k: meta[k] for k in ("cell", "pivot", "fps", "cols", "rows")}), len(allf), "frames")


if __name__ == "__main__":
    main()
