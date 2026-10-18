#!/usr/bin/env python3
"""Static lock: cut gestures out of FIRST+LAST-FRAME H3 clips so that only what really moves comes from the clip
and every other pixel is the home picture itself — the throne, legs and body cannot shimmer or drift in colour.

usage: lock.py OUT --home HOME.png --at X,Y [--keep PROP_MASK.png] CLIP.mp4=name,name,name,name [CLIP2.mp4=…]
               [--pose-s 1.0] [--thresh 30] [--grow 6] [--feather 3] [--cell 479,444 --pivot 245.6,442.8 --fig 327]
               [--step 2] [--webp 70]

--keep is a mask (frame-sized, white = prop) of what is NOT the character — a throne, a stand: there, pixels the
clip erases come back from home. Nowhere else: a head that moves leaves real empty space behind it.
HOME.png is the clean RGBA cut-out of the character that was composited onto the flat first/last frame picture at
offset X,Y (the same pixels the clip starts from). Per frame:
  1. difference to the clip's own first frame over the figure (max over RGB, blurred 1.5 px) -> moving mask = diff > --thresh, opened,
     closed, grown by --grow px, feathered by --feather px. Slow relighting of static parts stays under the
     threshold, so they come from home.
  2. colour of the moving area: per-channel gains (capped +-15 %) that undo the relighting since the clip's first
     frame, measured on a ring of body just outside the moving area.
  3. spill of the ground colour clamped at the outline and outside it; alpha outside the home silhouette (a head tilting past its outline) keyed against this frame's border colour.
  4. out = home where the mask is 0, the clip where it is 1, blended in between (premultiplied).
Cuts: the dip of the moving area nearest every k * --pose-s (+-0.5 s), printed. H3 in first+last mode does not
return to rest between gestures on the clock, so a cut that is not a full rest eases into home over --ease frames.
Packs like gestures.py: atlas.png/.webp + atlas.json + review.png + mix.gif, the figure scaled to --fig px tall and
its bottom centre on --pivot in a --cell cell (so it sits where the game's other King strips sit)."""
import argparse, glob, json, os, random, subprocess
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

FPS = 24


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("clips", nargs="+")
    ap.add_argument("--home", required=True); ap.add_argument("--keep"); ap.add_argument("--at", required=True)
    ap.add_argument("--pose-s", type=float, default=1.0); ap.add_argument("--thresh", type=float, default=30)
    ap.add_argument("--grow", type=int, default=6); ap.add_argument("--feather", type=float, default=3)
    ap.add_argument("--cell", default="479,444"); ap.add_argument("--pivot", default="245.6,442.8"); ap.add_argument("--fig", type=float, default=327)
    ap.add_argument("--step", type=int, default=2); ap.add_argument("--reach", type=int, default=24); ap.add_argument("--dump"); ap.add_argument("--nogain", action="store_true"); ap.add_argument("--lut", action="store_true"); ap.add_argument("--ease", type=int, default=3)
    ap.add_argument("--open-end", action="store_true", help="half of a chained gesture: ease into home at the START only; the end is a drawn peak pose that the next half starts from"); ap.add_argument("--webp", type=int, default=70); ap.add_argument("--t0", type=float, default=0); ap.add_argument("--t1", type=float, default=99)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    cut = np.asarray(Image.open(a.home).convert("RGBA"), dtype=float); ox, oy = map(int, a.at.split(","))
    rows = []
    for spec in a.clips:
        clip, _, names = spec.partition("="); names = names.split(",")
        name = os.path.splitext(os.path.basename(clip))[0]
        src = os.path.join(a.out, name, "src"); os.makedirs(src, exist_ok=True)
        if not glob.glob(os.path.join(src, "f_*.png")):
            subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-vf", f"fps={FPS}", os.path.join(src, "f_%03d.png")], check=True)
        fs = sorted(glob.glob(os.path.join(src, "f_*.png")))
        fs = fs[int(round(a.t0 * FPS)):int(round(a.t1 * FPS)) + 1]
        W, H = Image.open(fs[0]).size
        home = np.zeros((H, W, 4)); home[oy:oy + cut.shape[0], ox:ox + cut.shape[1]] = cut
        ha = home[..., 3] / 255; fig = ha > 0.5
        body = ndi.binary_erosion(fig, iterations=4)
        keep = (np.asarray(Image.open(a.keep).convert("L"), dtype=float) > 128) if a.keep else np.zeros_like(fig)
        region = ndi.binary_dilation(fig, iterations=a.reach)       # where a gesture may reach past the outline
        frames, masks = [], []
        # motion is measured against the clip's OWN first frame (the model's render of the picture): measured against
        # the picture, its repaint differences alone lit up ~20k px at rest and the cuts missed the home pose
        f0 = np.asarray(Image.open(fs[0]).convert("RGB"), dtype=float)
        lut = None
        if a.lut:  # per-channel linear map clip-render -> painted home, fitted on the figure in frame 0
            sel = ndi.binary_erosion(fig, iterations=3)
            lut = [np.polyfit(f0[..., c][sel], home[..., c][sel], 1) for c in range(3)]
            print("lut", [np.round(l, 3).tolist() for l in lut])
            f0 = np.dstack([np.polyval(lut[c], f0[..., c]) for c in range(3)]).clip(0, 255)
        edge = fig & ~ndi.binary_erosion(fig, iterations=3)
        for f in fs:
            rgb = np.asarray(Image.open(f).convert("RGB"), dtype=float)
            if lut is not None: rgb = np.dstack([np.polyval(lut[c], rgb[..., c]) for c in range(3)]).clip(0, 255)
            d = ndi.gaussian_filter(np.abs(rgb - f0).max(2) * fig, 1.5)
            # outside the outline: compare with this frame's flat ground instead (something moved INTO the ground)
            border = np.concatenate([rgb[:6].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
            bg = np.median(border, 0)
            out_d = np.sqrt(((rgb - bg) ** 2).sum(2))
            moved_out = (~fig) & region & (out_d > 60) & (rgb[..., int(np.argmax(bg))] - np.delete(rgb, int(np.argmax(bg)), 2).max(2) < 40)
            m = ((d > a.thresh) & fig) | moved_out
            m = ndi.binary_closing(ndi.binary_opening(m, iterations=2), iterations=3)
            m = ndi.binary_dilation(m, iterations=a.grow) & region
            # nothing in the home picture may vanish: where the clip shows bare ground INSIDE the home outline (the model
            # erased a corner of the throne behind a raised arm or the crown), home stays
            # — but only for the PROP (--keep: a mask of what is not the character, e.g. the throne). Applied to the whole
            # outline, it pasted the home crown back where the head had just moved away from: two crowns.
            kq = int(np.argmax(bg)); gone = fig & ((rgb[..., kq] - np.delete(rgb, kq, 2).max(2)) > 40)
            m &= ~ndi.binary_dilation(gone & keep, iterations=2)
            mf = np.clip(ndi.gaussian_filter(m.astype(float), a.feather), 0, 1)
            # local colour match on a ring of body just outside the moving area
            ring = m & body          # the moving area itself, against the same pixels of the clip's first frame
            if ring.sum() > 300 and not a.nogain:
                # relighting SINCE THE START, measured model-render against model-render (the clip's own first frame):
                # measured against the painted picture, local detail differences (crown glow, edges) became an orange cast
                g = np.clip(f0[ring].mean(0) / np.maximum(rgb[ring].mean(0), 1), 0.85, 1.15); rgb = np.clip(rgb * g, 0, 255)
            # alpha: opaque inside the outline; outside it, keyed on how much the ground's channel DOMINATES (not on
            # distance from the ground colour): the model casts soft shadows on the backdrop, and a darker blue is still
            # backdrop — a distance key kept it and the spill clamp turned it teal
            kc0 = int(np.argmax(bg)); o0 = [c for c in range(3) if c != kc0]
            dom = rgb[..., kc0] - rgb[..., o0].max(2)
            # inside the home outline the figure is opaque — except where the character moved away and left bare ground
            fa = np.where(fig & ~(gone & ~keep), 1.0, np.clip((60 - dom) / 40, 0, 1))
            # spill: the ground's dominant channel bleeds into glows and edges (a blue rim round the crown) — clamp
            # it to the other two channels wherever the pixel is at the outline or outside it
            kc = int(np.argmax(bg)); oth = [c for c in range(3) if c != kc]
            mx = rgb[..., oth].max(2)
            sp = (~fig) | edge | (rgb[..., kc] - mx > 25)      # outline, outside, or a clear excess (crown glow)
            rgb[..., kc] = np.where(sp, np.minimum(rgb[..., kc], mx), rgb[..., kc])
            # the home's soft outer fringe must not linger where the part moved away (a faint ghost outline)
            mx2 = np.clip(ndi.gaussian_filter(ndi.binary_dilation(m, iterations=4).astype(float), 1), 0, 1)
            hx = np.where(ha < 0.99, ha * (1 - mx2), ha)
            pa = hx * (1 - mf) + fa * mf
            col = (home[..., :3] * hx[..., None] * (1 - mf[..., None]) + rgb * fa[..., None] * mf[..., None]) / np.maximum(pa, 1e-3)[..., None]
            frames.append(np.dstack([col, pa * 255])); masks.append(mf.sum())
        print(f"{name}: moving area (px) every 1/12 s:", " ".join(f"{j / FPS:.2f}:{masks[j] / 1000:.0f}k" for j in range(0, len(fs), 2)))
        w = int(0.5 * FPS); cuts = []
        for k in range(len(names) + 1):
            c = min(len(fs) - 1, int(round(k * a.pose_s * FPS))); lo, hi = max(0, c - w), min(len(fs), c + w + 1)
            cuts.append(lo + int(np.argmin(masks[lo:hi])))
        for k, nm in enumerate(names):
            i0, i1 = cuts[k], cuts[k + 1]
            print(f"  {nm}: {i0 / FPS:.2f}-{i1 / FPS:.2f} s, moving area at the cuts {masks[i0] / 1000:.1f}k / {masks[i1] / 1000:.1f}k px")
            seq = frames[i0:i1 + 1:a.step]; n = len(seq)
            if a.open_end: seq[0] = home
            # the ends ARE home; a cut that is not a full rest eases into it over --ease frames
            for j in range(n):
                w = min(1.0, j / a.ease, (n - 1 - j) / a.ease if not a.open_end else 1.0)
                if w < 1:
                    f = seq[j]; pa = f[..., 3:4] / 255 * w + ha[..., None] * (1 - w)
                    rgb = (f[..., :3] * f[..., 3:4] / 255 * w + home[..., :3] * ha[..., None] * (1 - w)) / np.maximum(pa, 1e-3)
                    seq[j] = np.dstack([rgb, pa * 255])
            if a.dump:
                os.makedirs(a.dump, exist_ok=True)
                for j, f in enumerate(seq): Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8), "RGBA").save(os.path.join(a.dump, f"{nm}_{j:03d}.png"))
            rows.append((nm, seq, f"{name} {i0 / FPS:.2f}-{i1 / FPS:.2f}s"))
    # place: scale the figure to --fig px, bottom centre on the pivot
    CW, CH = map(int, a.cell.split(",")); PX, PY = map(float, a.pivot.split(","))
    ys, xs = np.nonzero(fig); s = a.fig / (ys.max() - ys.min() + 1); bx, by = (xs.min() + xs.max()) / 2, ys.max()
    aff = (1 / s, 0, bx - PX / s, 0, 1 / s, by - PY / s)
    def place(f): return Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8), "RGBA").transform((CW, CH), Image.AFFINE, aff, Image.BICUBIC)
    allf = [place(f) for _, sq, _ in rows for f in sq]
    cols = min(len(allf), 16383 // CW); nr = (len(allf) + cols - 1) // cols
    atlas = Image.new("RGBA", (CW * cols, CH * nr), (0, 0, 0, 0))
    for i, f in enumerate(allf): atlas.alpha_composite(f, ((i % cols) * CW, (i // cols) * CH))
    atlas.save(os.path.join(a.out, "atlas.png"))
    if a.webp: atlas.save(os.path.join(a.out, "atlas.webp"), "WEBP", quality=a.webp, method=6, alpha_quality=90)
    gs, at = [], 0
    for nm, sq, srcs in rows: gs.append({"name": nm, "at": at, "frames": len(sq), "src": srcs}); at += len(sq)
    json.dump({"cell": [CW, CH], "pivot": [PX, PY], "fps": FPS / a.step, "cols": cols, "rows": nr, "gestures": gs}, open(os.path.join(a.out, "atlas.json"), "w"), indent=1)
    tw, th = 200, round(200 * CH / CW); rv = Image.new("RGB", (8 * tw, th * len(rows)), (42, 30, 58)); i = 0
    for r, (_, sq, _) in enumerate(rows):
        for k in range(8):
            f = allf[i + round(k * (len(sq) - 1) / 7)].resize((tw, th), Image.LANCZOS); rv.paste(f, (k * tw, r * th), f)
        i += len(sq)
    rv.save(os.path.join(a.out, "review.png"))
    print(len(allf), "frames,", cols, "x", nr)


if __name__ == "__main__":
    main()
