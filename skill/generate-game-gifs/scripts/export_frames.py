#!/usr/bin/env python3
"""Extract a GIF's frames to PNG, keeping timing — optionally keyed, cropped and resized for a game.

usage: export_frames.py IN.gif OUT_DIR [--key none|border] [--lo 40] [--hi 120]
                        [--crop union|none] [--pad 4] [--aspect W/H] [--height PX] [--anchor bottom|center]
                        [--despill blue|green|red] [--despill-margin 25] [--largest-component]
                        [--shift-hue FROM TO] [--hue-tol 25] [--min-sat 0.3]

Writes OUT_DIR/frame_000.png … and OUT_DIR/frames.json:
  {"source", "frames", "frameWidth", "frameHeight", "durationsMs", "loop", "key", "crop", "alignment"}
Every number in frames.json is measured from the file, never assumed.

--key border   GIF has no real alpha (1-bit palette transparency at best), so ask the model for a FLAT
               background and key it here: the key colour is the median of each frame's 4-px border, alpha
               ramps from 0 at RGB distance --lo to 1 at --hi, and edge pixels are un-mixed from the
               background colour (out = (pix - (1-a)*bg)/a) so no coloured fringe survives. Expect a soft
               edge and to lose anything close to the key colour (keep the key far from the character).
--despill C    the flat background lights the character's edges in its colour (a blue rim on black fur).
               Clamp that channel to max(other two) + --despill-margin, which removes a cast of the key colour
               and leaves other hues (violet keeps its blue while its red is high).
--largest-component  keep only the biggest connected opaque shape per frame: drops stray marks the model
               paints beside a character ("motion lines", sparkles). Do NOT use it when a sprite is meant to
               have separate parts (a thrown ball, floating sparks).
--shift-hue FROM TO  move saturated pixels within --hue-tol degrees of hue FROM to hue TO (saturation and
               value kept): matches one generation's eye/accent colour to another's. Separate generations
               drift (the same "lime-green eyes" came back at 82 and 134 degrees), and a character that
               changes eye colour between its walk and its idle reads as two characters.
--crop union   ONE crop box for all frames (the union of every frame's opaque/changed area): frames stay
               aligned to each other, so a sprite does not jitter. Never crop frames one by one.
--aspect W/H   pad the union box to this aspect (to fit an existing sprite box without stretching),
               keeping the --anchor edge (feet on the bottom for a standing character).
--height PX    resize every frame to this height (LANCZOS, on premultiplied alpha).
Alignment report: the bottom-most opaque row and the horizontal centre of mass per frame, so a frame that
"jumps" can be spotted before it ships.
"""
import argparse, json, os
import numpy as np
from PIL import Image, ImageSequence


def key_border(rgb, lo, hi):
    border = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
    bg = np.median(border, 0)
    d = np.sqrt(((rgb - bg) ** 2).sum(2))
    al = np.clip((d - lo) / (hi - lo), 0, 1)
    out = np.clip((rgb - (1 - al)[..., None] * bg) / np.maximum(al, 1e-3)[..., None], 0, 255)
    return np.dstack([out, al * 255]), bg


def largest_component(mask, grow=2):
    """The biggest 4-connected True region of mask, grown by `grow` px to keep its soft edge (no scipy)."""
    from collections import deque
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32); best, best_n, cur = 0, 0, 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        cur += 1; n = 0; q = deque([(y0, x0)]); lab[y0, x0] = cur
        while q:
            y, x = q.popleft(); n += 1
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = cur; q.append((yy, xx))
        if n > best_n:
            best, best_n = cur, n
    keep = lab == best
    for _ in range(grow):
        k = keep.copy()
        k[1:] |= keep[:-1]; k[:-1] |= keep[1:]; k[:, 1:] |= keep[:, :-1]; k[:, :-1] |= keep[:, 1:]
        keep = k
    return keep


def shift_hue(rgb, h_from, h_to, tol, min_sat):
    x = rgb / 255.0
    mx, mn = x.max(2), x.min(2); c = mx - mn
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    safe = np.where(c > 1e-6, c, 1)
    h = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    s = np.where(mx > 1e-6, c / np.maximum(mx, 1e-6), 0)
    dist = np.abs((h - h_from + 180) % 360 - 180)
    sel = (c > 1e-6) & (s >= min_sat) & (dist <= tol)
    w = np.clip(1 - (dist - tol * 0.6) / (tol * 0.4), 0, 1) * sel   # feather the band's edge
    h2 = (h + w * (((h_to - h_from + 180) % 360) - 180)) % 360
    hp = h2 / 60; xx = c * (1 - np.abs(hp % 2 - 1)); z = np.zeros_like(c)
    i = np.floor(hp).astype(int) % 6
    rr = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [c, xx, z, z, xx, c])
    gg = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [xx, c, c, xx, z, z])
    bb = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [z, z, xx, c, c, xx])
    out = np.dstack([rr + mn, gg + mn, bb + mn]) * 255
    return np.where(sel[..., None], out, rgb)


def premul_resize(im, size):
    a = np.asarray(im, dtype=np.float32) / 255.0
    pm = Image.fromarray((np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]]) * 255).round().astype(np.uint8), "RGBA")
    r = np.asarray(pm.resize(size, Image.LANCZOS), dtype=np.float32) / 255.0
    al = r[..., 3:4]
    rgb = np.where(al > 1e-4, r[..., :3] / np.maximum(al, 1e-4), 0)
    return Image.fromarray((np.dstack([np.clip(rgb, 0, 1), al]) * 255).round().astype(np.uint8), "RGBA")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gif"); ap.add_argument("out_dir")
    ap.add_argument("--key", choices=["none", "border"], default="none")
    ap.add_argument("--lo", type=float, default=40); ap.add_argument("--hi", type=float, default=120)
    ap.add_argument("--crop", choices=["union", "none"], default="none")
    ap.add_argument("--pad", type=int, default=4)
    ap.add_argument("--aspect", default=None, help="W/H, e.g. 148/100")
    ap.add_argument("--anchor", choices=["bottom", "center"], default="bottom")
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--despill", choices=["blue", "green", "red"], default=None)
    ap.add_argument("--despill-margin", type=float, default=25)
    ap.add_argument("--largest-component", action="store_true")
    ap.add_argument("--shift-hue", nargs=2, type=float, default=None, metavar=("FROM", "TO"))
    ap.add_argument("--hue-tol", type=float, default=25)
    ap.add_argument("--min-sat", type=float, default=0.3)
    a = ap.parse_args()

    im = Image.open(a.gif)
    durs, frames, bgs = [], [], []
    for f in ImageSequence.Iterator(im):
        durs.append(f.info.get("duration"))
        rgba = np.asarray(f.convert("RGBA"), dtype=np.float32)
        if a.key == "border":
            k, bg = key_border(rgba[..., :3], a.lo, a.hi)
            bgs.append([round(float(x), 1) for x in bg])
            rgba = k
        if a.despill:
            c = {"red": 0, "green": 1, "blue": 2}[a.despill]
            others = [i for i in range(3) if i != c]
            rgba[..., c] = np.minimum(rgba[..., c], np.maximum(rgba[..., others[0]], rgba[..., others[1]]) + a.despill_margin)
        if a.shift_hue:
            rgba[..., :3] = shift_hue(rgba[..., :3], a.shift_hue[0], a.shift_hue[1], a.hue_tol, a.min_sat)
        if a.largest_component:
            rgba[..., 3] = np.where(largest_component(rgba[..., 3] > 24), rgba[..., 3], 0)
        frames.append(rgba)
    H, W = frames[0].shape[:2]
    if any(f.shape[:2] != (H, W) for f in frames):
        raise SystemExit("frames differ in size — refusing to export misaligned frames")

    box = (0, 0, W, H)
    if a.crop == "union":
        m = np.zeros((H, W), bool)
        for f in frames:
            m |= f[..., 3] > 24
        if a.key == "none":   # opaque GIF: crop to what changes across frames instead
            st = np.stack([f[..., :3] for f in frames]); m = (st.max(0) - st.min(0)).max(2) > 24
        ys, xs = np.nonzero(m)
        if len(xs):
            x0, x1, y0, y1 = xs.min() - a.pad, xs.max() + 1 + a.pad, ys.min() - a.pad, ys.max() + 1 + a.pad
            if a.aspect:
                n, d = (float(v) for v in a.aspect.split("/")); asp = n / d
                bw, bh = x1 - x0, y1 - y0
                if bw / bh < asp:
                    grow = asp * bh - bw; x0 -= grow / 2; x1 += grow / 2
                else:
                    grow = bw / asp - bh
                    if a.anchor == "bottom": y0 -= grow
                    else: y0 -= grow / 2; y1 += grow / 2
            box = tuple(int(round(v)) for v in (x0, y0, x1, y1))
    os.makedirs(a.out_dir, exist_ok=True)
    out_frames, bottoms, cxs = [], [], []
    for i, f in enumerate(frames):
        img = Image.fromarray(f.round().astype(np.uint8), "RGBA").crop(box)   # crop may pad outside: transparent
        if a.height:
            img = premul_resize(img, (max(1, round(img.width * a.height / img.height)), a.height))
        img.save(os.path.join(a.out_dir, "frame_%03d.png" % i))
        al = np.asarray(img)[..., 3] > 24
        ys, xs = np.nonzero(al)
        bottoms.append(int(ys.max()) if len(ys) else None)
        cxs.append(round(float(xs.mean()), 1) if len(xs) else None)
        out_frames.append(img)
    fw, fh = out_frames[0].size
    meta = {"source": os.path.abspath(a.gif), "frames": len(out_frames), "frameWidth": fw, "frameHeight": fh,
            "durationsMs": durs, "loop": im.info.get("loop"), "key": a.key, "despill": a.despill, "largestComponent": a.largest_component, "shiftHue": a.shift_hue, "keyColours": bgs[:1] + (["varies"] if len({tuple(b) for b in bgs}) > 1 else []) if bgs else None,
            "crop": {"mode": a.crop, "box": list(box)},
            "alignment": {"bottomRow": bottoms, "centreX": cxs,
                          "bottomSpreadPx": (max(b for b in bottoms if b is not None) - min(b for b in bottoms if b is not None)) if any(b is not None for b in bottoms) else None}}
    json.dump(meta, open(os.path.join(a.out_dir, "frames.json"), "w"), indent=2)
    print(json.dumps({k: meta[k] for k in ("frames", "frameWidth", "frameHeight", "durationsMs", "loop")} | {"bottomSpreadPx": meta["alignment"]["bottomSpreadPx"]}))


if __name__ == "__main__":
    main()
