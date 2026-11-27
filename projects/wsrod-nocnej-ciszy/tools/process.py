"""process.py — turn the raw gpt-image-2.6 GIFs of „Wśród nocnej ciszy” into game frames registered to the static art.

For each clip (CLIPS below):
  1. rim: strip the frame's own outer paper rim back to the black ink outline (grown inward from outside through
     non-ink pixels, a few px deep), then lay ONE cream rim of the static art's width around it, with a fixed
     torn-paper wobble (the same noise field for every frame, so the rim does not boil);
  2. scale: register frame 0 to the static picture it replaces (silhouette IoU over scale + offset), or, for a
     pose the static art does not have, take the sibling clip's scale corrected by a feature that does not change
     with pose (ukulele area for the fox, the hand-checked head width for the dog);
  3. cell: every frame is placed in the static picture's own cell coordinates (anchor = art.json's anchor), then
     scaled by OUT_SCALE (0.5 → a ~512 px tall cell) and cropped to the union box of all frames + a pad;
  4. writes frames/<clip>/frame_NNN.png + frames.json in export_frames.py's format, so the skill's
     build_spritesheet.py packs it, and prints the check numbers (size drift, feet spread, edge fringe, seam).
No network. Run from the project folder: python3 tools/process.py [clip ...]
"""
import json, math, os, sys
import numpy as np, scipy.ndimage as nd
from PIL import Image, ImageSequence

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = "/home/user/MusicGames/fingerpick-warmup/art/wsrod-nocnej-ciszy"
OUT_SCALE = 0.5
PAD = 6   # px at output scale
CREAM = (239, 228, 200)

# the dog-wake cells (see CLIPS); SEQ_WAKE in the environment overrides it for trying sequences
SEQ_WAKE = json.loads(os.environ['SEQ_WAKE']) if os.environ.get('SEQ_WAKE') else [(0, 1), (1, 1), (2, 1), (3, .93), (3, 1), (4, 1), (5, 1), (6, 1), (7, .93), (7, 1), (8, .94), (11, .94), (11, 1.01), (11, 1)]

# clip: gif, static picture it is registered to / sized against, how its scale is found, anchor rule, timing
CLIPS = {
    "fox-sit":     dict(static="fox", reg="iou", anchor="static", ms=150, loop=True),
    "fox-sing":    dict(static="fox-sing", reg="iou", anchor="static", ms=150, loop=True),
    "fox-tiptoe":  dict(static="fox", reg=("feature", "fox-sit", "mustard"), anchor="feet-walk", ms=110, loop=True),
    "fox-stand":   dict(static="fox", reg=("feature", "fox-sit", "mustard"), anchor="feet", ms=160, loop=True),
    "dog-sit":     dict(static="dog", reg="iou", anchor="static", ms=160, loop=True),
    "dog-bark":    dict(static="dog", reg="iou", anchor="static", ms=120, loop=True),
    "dog-sleep":   dict(static="dog", reg=("same", "dog-sit"), anchor="feet-front", ms=180, loop=True),
    # 2026-11-27: the two clips the 401 held back. Registered to the sibling strip they cross-fade with (its frame 0
    # in static-cell space), so the hand-over lands on the same silhouette: the wake's LAST frame on dog-sit's frame 0,
    # the standing song's frame 0 on fox-stand's frame 0.
    # dog-wake is a one-shot between two strips: gif frame 0 is registered on dog-sleep's frame 0, the last on dog-sit's,
    # the frames between get a transform interpolated by how far he has sat up (figure height), and the two end cells
    # ARE those strips' frames (ends="exact"), so the page's hand-over in and out is pixel-identical.
    # 12-frame GIF (c4), 14 cells (SEQ_WAKE). The review asked for no step over ~23 (mean |Δ| at 844×390) and no height
    # step over 8 px, and the end painted from dog-sit's own pixels: cell 0 = dog-sleep f0, GIF 1–2, GIF 3 at 0.93 tall
    # then GIF 3 (an in-between the GIF lacks), GIF 4–6, GIF 7 at 0.93 then GIF 7, GIF 8 at 0.94, then dog-sit f0 at 0.94
    # and 1.01 tall (the last of the rise and a small settle) and dog-sit f0 itself. Chosen with the reviewer's metric
    # offline over the candidates (scratch proxy), then measured in the page.
    "dog-wake":    dict(static="dog", reg=("ends", "dog-sleep", "dog-sit"), anchor="static", ms=80, loop=False, outer_ink=6, ends="exact",
                        sequence=SEQ_WAKE),
    "fox-stand-sing": dict(static="fox", reg=("clip", "fox-stand", 0), anchor="feet", ms=150, loop=True, feet_on=True),
    "hen-idle":    dict(static="hen", reg="iou", anchor="static", ms=160, loop=True, out=.25),
    "duck-idle":   dict(static="duck", reg="iou", anchor="static", ms=160, loop=True, out=.25),
    "rabbit-idle": dict(static="rabbit", reg="iou", anchor="static", ms=160, loop=True, out=.25),
}
# hand correction for poses whose scale cannot be measured from a shared feature (set after looking; see notes)
SCALE_FIX = {"dog-sleep": 1.08}   # head foreshortened lying down reads smaller, paws read larger: split the difference (eye judgement)


def load_gif(path):
    g = Image.open(path)
    return [np.array(f.convert("RGBA")) for f in ImageSequence.Iterator(g)]


def static_info(name):
    aj = json.load(open(os.path.join(ART, "art.json")))["cast"][name]
    im = np.array(Image.open(os.path.join(ART, aj["file"])).convert("RGBA"))
    return aj, im


def lum(a):
    return a[..., :3].astype(float) @ np.array([.3, .59, .11])


def rim_width(a):
    A = a[..., 3] > 127; ink = (lum(a) < 70) & A
    d = nd.distance_transform_edt(~ink); edge = A & ~nd.binary_erosion(A)
    return float(np.median(d[edge])), float(np.percentile(d[edge], 80))


OUTER_INK = 0   # px: a frame drawn as a sticker with a thin dark line OUTSIDE its cream rim (dog-wake) — eat that first


def core_mask(a, depth):
    """alpha minus its outer paper rim: grow from outside into the figure through non-ink pixels, `depth` px
    (after OUTER_INK px of growth through ink only: a no-op where the rim touches the outside, as it should)."""
    A = a[..., 3] > 127; ink = (lum(a) < 80) & A
    out = ~A; passable = ~ink
    grown = out.copy()
    for _ in range(OUTER_INK):
        grown = nd.binary_dilation(grown) & (ink | out)
    out = grown
    for _ in range(int(math.ceil(depth))):
        grown = nd.binary_dilation(grown) & (passable | out)
    core = A & ~grown
    core = nd.binary_closing(core, iterations=1) & A
    # keep only real parts (drop specks the stripping isolates)
    lab, n = nd.label(core)
    if n > 1:
        sizes = nd.sum(core, lab, range(1, n + 1)); keep = np.isin(lab, 1 + np.nonzero(sizes > 400)[0])
        core = core & keep
    return core


def noise_field(shape, seed=7):
    rng = np.random.default_rng(seed)
    small = rng.standard_normal((shape[0] // 24 + 2, shape[1] // 24 + 2))
    big = np.array(Image.fromarray(small.astype(np.float32), mode="F").resize((shape[1], shape[0]), Image.BICUBIC))
    fine = nd.gaussian_filter(rng.standard_normal(shape), 1.2)
    f = big / (big.std() + 1e-6) * .7 + fine / (fine.std() + 1e-6) * .3
    return np.clip(f, -2.5, 2.5)


def rebuild_rim(a, rim_px, noise, depth):
    """a: RGBA uint8 (GIF space). Returns RGBA with a uniform cream rim rim_px wide (GIF px)."""
    core = core_mask(a, depth)
    d = nd.distance_transform_edt(~core)
    r = rim_px * (1 + .22 * noise)
    rim = (d > 0) & (d <= r)
    out = np.zeros_like(a)
    out[core] = a[core]
    out[core, 3] = 255
    out[rim, :3] = CREAM; out[rim, 3] = 255
    return out, core


def mask_from(a):
    return a[..., 3] > 127


def place(mask_src, s, dx, dy, shape):
    """nearest-neighbour similarity warp of a boolean mask into `shape` (dst = s*src + d)."""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    sx = ((xx - dx) / s).round().astype(int); sy = ((yy - dy) / s).round().astype(int)
    ok = (sx >= 0) & (sy >= 0) & (sx < mask_src.shape[1]) & (sy < mask_src.shape[0])
    out = np.zeros(shape, bool); out[ok] = mask_src[sy[ok], sx[ok]]
    return out


def register_iou(gmask, smask, k0=1.0):
    """scale s (static px per GIF px) and offset (dx,dy) maximising IoU, coarse on /4 masks then refined on /2."""
    def down(m, k):
        return np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((m.shape[1] // k, m.shape[0] // k), Image.BILINEAR)) > 127
    best = None
    for k, s_range, t_rad, t_step in ((4, np.arange(.80 * k0, 1.30 * k0, .02 * k0), 0, 0), (2, None, 6, 1)):
        g, st = down(gmask, k), down(smask, k)
        if s_range is None:
            s0 = best[1]; s_range = np.arange(s0 - .02, s0 + .021, .005)
        for s in s_range:
            gy, gx = np.nonzero(g); sy_, sx_ = np.nonzero(st)
            base_dx = sx_.mean() - s * gx.mean(); base_dy = sy_.mean() - s * gy.mean()
            if best is not None and k == 2:
                base_dx = best[2] / k; base_dy = best[3] / k
            for ddx in range(-t_rad, t_rad + 1, t_step or 1):
                for ddy in range(-t_rad, t_rad + 1, t_step or 1):
                    dx, dy = base_dx + ddx, base_dy + ddy
                    w = place(g, s, dx, dy, st.shape)
                    iou = (w & st).sum() / max(1, (w | st).sum())
                    if best is None or iou > best[0] or (best[0] == iou):
                        if best is None or iou > best[0]:
                            best = (iou, s, dx * k, dy * k)
    return best


def feature_area(a, kind):
    rgb = a[..., :3].astype(float) / 255; A = a[..., 3] > 127
    mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / (mx + 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if kind == "mustard":   # the ukulele's yellow body: r high, g mid-high, b low
        m = A & (sat > .45) & (mx > .55) & (g > .45) & (g < .85 * r + .1) & (g > .5 * r) & (b < .45)
    else:
        raise ValueError(kind)
    return int(m.sum())


def resize_rgba(a, size):
    """premultiplied LANCZOS resize."""
    f = a.astype(np.float32) / 255; f[..., :3] *= f[..., 3:4]
    chans = [np.array(Image.fromarray(f[..., i], mode="F").resize(size, Image.LANCZOS)) for i in range(4)]
    o = np.stack(chans, -1); o[..., 3] = np.clip(o[..., 3], 0, 1)
    rgb = np.where(o[..., 3:4] > 1e-4, o[..., :3] / np.maximum(o[..., 3:4], 1e-4), 0)
    out = np.concatenate([np.clip(rgb, 0, 1), o[..., 3:4]], -1)
    return (out * 255 + .5).astype(np.uint8)


def warp_rgba(a, s, dx, dy, shape):
    """place a GIF-space RGBA into static-cell space (dst = s*src + d), at static resolution, via a premultiplied resize."""
    H, W = shape
    nw, nh = max(1, round(a.shape[1] * s)), max(1, round(a.shape[0] * s))
    big = resize_rgba(a, (nw, nh))
    out = np.zeros((H, W, 4), np.uint8)
    ox, oy = int(round(dx)), int(round(dy))
    x0, y0 = max(0, ox), max(0, oy); x1, y1 = min(W, ox + nw), min(H, oy + nh)
    if x1 > x0 and y1 > y0:
        out[y0:y1, x0:x1] = big[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    return out


def edge_fringe(a):
    """edge pixels (alpha>0 next to alpha==0): share that read as night blue (b > r+25 and b > g+15) and as cream."""
    A = a[..., 3] > 0; edge = A & ~nd.binary_erosion(A)
    p = a[edge][:, :3].astype(int); n = len(p)
    blue = ((p[:, 2] > p[:, 0] + 25) & (p[:, 2] > p[:, 1] + 15)).sum()
    cream = ((np.abs(p - np.array(CREAM)).sum(1)) < 60).sum()
    dark = (p.sum(1) < 180).sum()
    return dict(edgePx=int(n), blueShare=round(blue / max(1, n), 4), creamShare=round(cream / max(1, n), 3), darkShare=round(dark / max(1, n), 3))


def squash(cell, sy):
    """the cell's figure scaled vertically by sy about its lowest opaque row (x untouched): an in-between for a rise,
    or the sitting dog's own pixels a touch short / a touch tall for the settle."""
    h, w = cell.shape[:2]; bottom = np.nonzero((cell[..., 3] > 127).any(1))[0].max() + 1
    nh = max(1, round(bottom * sy)); top = resize_rgba(cell[:bottom], (w, nh))
    out = np.zeros_like(cell); y0 = bottom - nh
    if y0 >= 0: out[y0:bottom] = top
    else: out[0:bottom] = top[-y0:]
    out[bottom:] = cell[bottom:]
    return out


def register_clip(results, sibn, frame, sim, s_rim, noise, depth):
    """register one GIF frame (with a provisional rim) on a processed sibling strip's frame 0, in static-cell space."""
    sib = results[sibn]; so = sib["outScale"]; offx, offy = 400, 200
    f0 = np.array(Image.open(os.path.join(HERE, "frames", sibn, "frame_000.png")).convert("RGBA"))
    big = resize_rgba(f0, (round(f0.shape[1] / so), round(f0.shape[0] / so)))
    T = np.zeros((sim.shape[0] + 400, sim.shape[1] + 800), bool)
    ox, oy = int(sib["cellOrigin"][0]) + offx, int(sib["cellOrigin"][1]) + offy
    T[oy:oy + big.shape[0], ox:ox + big.shape[1]] = big[..., 3] > 127
    prov, _ = rebuild_rim(frame, s_rim, noise, depth)
    iou, s, dx, dy = register_iou(mask_from(prov), T, 960 / frame.shape[1])   # a 768 px GIF draws the figure smaller
    return iou, s, dx - offx, dy - offy


def main(names):
    results = json.load(open(os.path.join(HERE, "process-results.json"))) if os.path.exists(os.path.join(HERE, "process-results.json")) else {}
    for name in names:
        cfg = CLIPS[name]
        global OUTER_INK; OUTER_INK = cfg.get("outer_ink", 0)
        frames = load_gif(os.path.join(HERE, "gifs", name + ".gif"))
        aj, sim = static_info(cfg["static"])
        s_rim, _ = rim_width(sim)
        g_rim_med, g_rim_hi = rim_width(frames[0])
        depth = g_rim_hi + 3
        noise = noise_field(frames[0].shape[:2])
        # scale first (needs the rim in static px / s): register on frame 0 rebuilt with a provisional rim
        reg = cfg["reg"]
        if reg == "iou":
            prov, _ = rebuild_rim(frames[0], s_rim, noise, depth)
            iou, s, dx, dy = register_iou(mask_from(prov), mask_from(sim))
            how = "iou %.3f" % iou
        elif reg[0] == "feature":
            sib = results[reg[1]]
            fa = np.mean([feature_area(f, reg[2]) for f in frames]); fs = sib["featureArea"][reg[2]]
            s = sib["scale"] * math.sqrt(fs / fa) * SCALE_FIX.get(name, 1.0); iou = None; dx = dy = None
            how = "feature %s: %.0f vs %s's %.0f px²" % (reg[2], fa, reg[1], fs)
        elif reg[0] == "clip":
            iou, s, dx, dy = register_clip(results, reg[1], frames[reg[2]], sim, s_rim, noise, depth)
            how = "iou %.3f on %s frame 0 (gif frame %d)" % (iou, reg[1], reg[2] % len(frames))
        elif reg[0] == "ends":
            ia, sa, xa, ya = register_clip(results, reg[1], frames[0], sim, s_rim, noise, depth)
            ib, sb, xb, yb = register_clip(results, reg[2], frames[-1], sim, s_rim, noise, depth)
            hs = [float(np.ptp(np.nonzero(mask_from(f).any(1))[0])) for f in frames]
            u = [min(1, max(0, (h - hs[0]) / (hs[-1] - hs[0]))) for h in hs]
            s = [sa + (sb - sa) * k for k in u]; dx = [xa + (xb - xa) * k for k in u]; dy = [ya + (yb - ya) * k for k in u]
            how = "ends: frame 0 iou %.3f on %s (scale %.3f), last iou %.3f on %s (scale %.3f), between by height" % (ia, reg[1], sa, ib, reg[2], sb)
        elif reg[0] == "same":
            s = results[reg[1]]["scale"] * SCALE_FIX.get(name, 1.0); iou = None; dx = dy = None
            how = "scale of %s × %.3f (checked by eye: head widths)" % (reg[1], SCALE_FIX.get(name, 1.0))
        S = s if isinstance(s, list) else [s] * len(frames)
        DX = dx if isinstance(dx, list) else [dx] * len(frames)
        DY = dy if isinstance(dy, list) else [dy] * len(frames)
        rim_gif = s_rim / float(np.median(S))
        built = [rebuild_rim(f, s_rim / si, noise, depth)[0] for f, si in zip(frames, S)]
        if reg[0] == "ends":
            # on the ground the whole way: each frame's lowest row on the line between the two strips' own lowest rows
            # (the blended transform alone left the middle of the rise floating up to 4 px at 844×390)
            def sib_bottom(n):
                sb = results[n]; m = np.array(Image.open(os.path.join(HERE, "frames", n, "frame_000.png")))[..., 3] > 127
                return sb["cellOrigin"][1] + (np.nonzero(m.any(1))[0].max() + .5) / sb["outScale"]
            b0, b1 = sib_bottom(reg[1]), sib_bottom(reg[2])
            for i, b in enumerate(built):
                mine = DY[i] + S[i] * (np.nonzero(mask_from(b).any(1))[0].max() + .5)
                DY[i] += b0 + (b1 - b0) * u[i] - mine
        if cfg.get("feet_on") and reg[0] == "clip":
            # the silhouette fit leaves the feet where the whole outline fits best; a standing pose must keep its feet on
            # the sibling's ground line (a cross-fade otherwise lifts him): move it down/up to the sibling's lowest row
            sib = results[reg[1]]; f0 = np.array(Image.open(os.path.join(HERE, "frames", reg[1], "frame_000.png")))[..., 3] > 127
            sib_bottom = sib["cellOrigin"][1] + (np.nonzero(f0.any(1))[0].max() + .5) / sib["outScale"]
            my_bottom = dy + s * (np.nonzero(mask_from(built[0]).any(1))[0].max() + .5)
            dy += sib_bottom - my_bottom; DY = [dy] * len(frames)
            how += ", feet put on %s's ground line (%+.1f static px)" % (reg[1], sib_bottom - my_bottom)
        # place into static-cell space
        if dx is None:
            # pose not in the static art: put the feet on the static's feet anchor
            feet = aj["anchor"].get("feet")
            ms = [mask_from(b) for b in built]
            bottom = max(np.nonzero(m.any(1))[0].max() for m in ms)
            if cfg["anchor"] == "feet-front":    # lying dog facing left: centre of the front paws on the ground
                m0 = ms[0]; rows = m0[bottom - int(60 / s * 1):bottom + 1]
                cols = np.nonzero(rows.any(0))[0]; front = cols[cols < cols.min() + int(170 / s)]
                ax_g = float(front.mean())
            else:                                 # standing / walking fox: under the hips (legs' mean column, all frames)
                xs = []
                for m in ms:
                    ys, xx = np.nonzero(m[bottom - int(200 / s):bottom + 1]); xs.append(xx.mean())
                ax_g = float(np.median(xs))
            dx = feet[0] - s * ax_g; dy = feet[1] - s * (bottom + .5)
        # union box in static space
        H = sim.shape[0] + 400; W = sim.shape[1] + 800; offx, offy = 400, 200   # roomy canvas around the static cell
        placed = [warp_rgba(b, si, xi + offx, yi + offy, (H, W)) for b, si, xi, yi in zip(built, S, DX, DY)]
        if cfg.get("ends") == "exact":   # the end cells are the neighbouring strips' own frames, placed by their cellOrigin
            for k, sibn in ((0, reg[1]), (len(placed) - 1, reg[2])):
                sib = results[sibn]; so = sib["outScale"]
                f0 = np.array(Image.open(os.path.join(HERE, "frames", sibn, "frame_000.png")).convert("RGBA"))
                big = resize_rgba(f0, (round(f0.shape[1] / so), round(f0.shape[0] / so)))
                cv = np.zeros((H, W, 4), np.uint8); ox, oy = int(sib["cellOrigin"][0]) + offx, int(sib["cellOrigin"][1]) + offy
                cv[oy:oy + big.shape[0], ox:ox + big.shape[1]] = big
                placed[k] = cv
        al = np.max([p[..., 3] for p in placed], 0) > 0
        ys, xs = np.nonzero(al)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        # output at the clip's scale (small animals: 0.25 → the same ~4 px per layout unit as the fox and dog)
        OUT = cfg.get("out", OUT_SCALE)
        padS = int(PAD / OUT)
        x0 -= padS; y0 -= padS; x1 += padS; y1 += padS
        x0 = max(0, x0); y0 = max(0, y0)
        if cfg.get("ends") == "exact":   # the end cells are pasted 1:1 below: keep their origins on whole output px
            step = round(1 / OUT); o = results[reg[1]]["cellOrigin"]
            x0 -= (x0 - offx - int(o[0])) % step; y0 -= (y0 - offy - int(o[1])) % step
        crop = [p[y0:y1, x0:x1] for p in placed]
        ow, oh = round((x1 - x0) * OUT), round((y1 - y0) * OUT)
        outs = [resize_rgba(c, (ow, oh)) for c in crop]
        if cfg.get("ends") == "exact":
            for k, sibn in ((0, reg[1]), (len(outs) - 1, reg[2])):
                o = results[sibn]["cellOrigin"]; f0 = np.array(Image.open(os.path.join(HERE, "frames", sibn, "frame_000.png")).convert("RGBA"))
                px, py = round((o[0] - (x0 - offx)) * OUT), round((o[1] - (y0 - offy)) * OUT)
                cell = np.zeros((oh, ow, 4), np.uint8)
                ys0, xs0 = max(0, py), max(0, px); ys1, xs1 = min(oh, py + f0.shape[0]), min(ow, px + f0.shape[1])
                cell[ys0:ys1, xs0:xs1] = f0[ys0 - py:ys1 - py, xs0 - px:xs1 - px]
                assert (f0[..., 3] > 0).sum() == (cell[..., 3] > 0).sum(), "end cell cut off"
                outs[k] = cell
        if cfg.get("sequence"):   # the shipped cells, in order: (cell index, vertical scale about its own feet row)
            outs = [outs[i] if sy == 1 else squash(outs[i], sy) for i, sy in cfg["sequence"]]
        # anchors (static-cell px → output px)
        anchors = {}
        for k, (axs, ays) in aj["anchor"].items():
            anchors[k] = [round(float((axs + offx - x0) * OUT), 1), round(float((ays + offy - y0) * OUT), 1)]
        if cfg["anchor"] != "static":
            anchors = {"feet": anchors["feet"]}
        od = os.path.join(HERE, "frames", name); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od):
            if f.startswith("frame_"): os.remove(os.path.join(od, f))
        for i, o in enumerate(outs):
            Image.fromarray(o).save(os.path.join(od, "frame_%03d.png" % i))
        # checks on the output frames
        ms = [o[..., 3] > 127 for o in outs]
        bb = [(np.nonzero(m.any(1))[0][[0, -1]], np.nonzero(m.any(0))[0][[0, -1]]) for m in ms]
        heights = [int(b[0][1] - b[0][0] + 1) for b in bb]; widths = [int(b[1][1] - b[1][0] + 1) for b in bb]
        bottoms = [int(b[0][1]) for b in bb]
        areas = [int(m.sum()) for m in ms]
        f32 = [o.astype(float) for o in outs]
        steps = [np.abs(f32[i + 1] - f32[i]).mean() for i in range(len(outs) - 1)]
        seam = np.abs(f32[0] - f32[-1]).mean()
        fringe = [edge_fringe(o) for o in outs]
        # static at output scale, for the "nothing jumps" number: figure height of the static vs frame 0
        sbb = np.nonzero((sim[..., 3] > 127).any(1))[0]
        check = dict(
            heightPx=heights, widthPx=widths, areaPx=areas,
            sizeDrift=dict(heightSpreadPct=round(100 * (max(heights) - min(heights)) / np.median(heights), 2),
                           areaSpreadPct=round(100 * (max(areas) - min(areas)) / np.median(areas), 2)),
            feetSpreadPx=int(max(bottoms) - min(bottoms)),
            seam=dict(medianStep=round(float(np.median(steps)), 3), seamStep=round(float(seam), 3),
                      ratio=round(float(seam / max(1e-6, np.median(steps))), 3)),
            edgeFringe=dict(blueShareMax=max(f["blueShare"] for f in fringe), creamShareMin=min(f["creamShare"] for f in fringe),
                            darkShareMax=max(f["darkShare"] for f in fringe)),
            staticFigureHeightAtOutPx=round((sbb[-1] - sbb[0] + 1) * OUT, 1),
            rim=dict(staticMedianPx=round(s_rim, 1), gifBeforeMedianPx=round(g_rim_med, 1), rebuiltAtGifPx=round(rim_gif, 2)),
        )
        meta = {"source": os.path.join("gifs", name + ".gif"), "frames": len(outs), "frameWidth": ow, "frameHeight": oh,
                "durationsMs": [cfg["ms"]] * len(outs), "loop": 0 if cfg["loop"] else None, "key": "palette-alpha+rim",
                "crop": "union", "alignment": {"bottomRow": bottoms, "bottomSpreadPx": check["feetSpreadPx"]}}
        json.dump(meta, open(os.path.join(od, "frames.json"), "w"), indent=1)
        fa = {"mustard": float(np.mean([feature_area(f, "mustard") for f in frames]))}
        results[name] = dict(static=cfg["static"], scale=s, registration=how, offset=[DX, DY] if isinstance(dx, list) else [dx, dy], cellOrigin=[x0 - offx, y0 - offy],
                             staticCell=[sim.shape[1], sim.shape[0]], outScale=OUT, anchors=anchors, featureArea=fa,
                             frameSize=[ow, oh], check=check)
        print(name, "scale %.4f" % float(np.median(S)), how, "out", (ow, oh), "anchors", anchors)
        print("   ", json.dumps({k: check[k] for k in ("sizeDrift", "feetSpreadPx", "seam", "edgeFringe", "rim")}))
        json.dump(results, open(os.path.join(HERE, "process-results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main(sys.argv[1:] or list(CLIPS))
