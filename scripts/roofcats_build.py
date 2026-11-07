#!/usr/bin/env python3
"""Rooftop cats (MusicGames ukulele-warmup/roofs.js): H3 clips -> keyed, trimmed, anchored frames -> one atlas per cat.

usage: roofcats_build.py OUTDIR  (reads raw/<job>.mp4 for the jobs named in CLIPS below)

Every clip was made from keyframes on ONE 1280x720 canvas (refs/ukuziom/ghost-roofs/h3/): the cat's feet at
(640, 650) when it sits or crouches, the leap pose 130 px ahead/behind and 150 px up. H3 returns 1344x768, i.e.
the canvas x1.05. So every frame is placed by the same rule and the parts meet: a frame's offset is measured from
the anchor (640, 650) in canvas px, then scaled by SCALE to atlas px.

Keying: the ground is flat blue; alpha falls with blue's dominance over red and green (dom = B - max(R, G):
~110 on the ground, <= 10 on fur, white and black). Edge pixels are despilled (B clamped to max(R, G) + 6).
Trimming (transitions): the frames before the first and after the last real movement are dropped (mean abs
difference to the previous frame on the alpha, > MOVE).
Writes OUTDIR/cat-<cat>.webp (atlas) and OUTDIR/cats.js: window.ROOFCATS = {plate, <cat>: {img, size, clips: {name: [[x,y,w,h,dx,dy], ...]}, touch, out, in}}
— dx, dy: the frame's top-left relative to the anchor, atlas px."""
import json, os, subprocess, sys, numpy as np
from PIL import Image

CLIPS = {
    "ginger": {"look": "20261107-020532-d532bd", "groom": "20261107-033954-ba0a94", "crouch": "20261107-033418-2306ef",
               "takeoff": "20261107-033419-92efeb", "landing": "20261107-033421-7e10a3"},
    "tux": {"look": "20261107-033423-40a12c", "groom": "20261107-033424-7e9d52", "crouch": "20261107-033426-5bb06b",
               "takeoff": "20261107-033428-c1d634", "landing": "20261107-033429-f9fffa"},
}
# the crouch frame (24 fps source) closest to the takeoff's first frame after one wiggle: mean |alpha| difference
# 0.0097 (ginger) and 0.0082 (tux) against 0.004 at the clip's own end, measured 2026-11-07
CROUCH_END = {"ginger": 40, "tux": 42}
TRANS = {"crouch", "takeoff", "landing"}
STEP = {"look": 2, "groom": 2, "crouch": 2, "takeoff": 2, "landing": 2}   # 24 fps source -> 12 fps (idle thinned below)
SCALE = 0.32          # atlas px per canvas px (the shipped stills are 0.5 of the sheet = 0.5 canvas px)
VX = 1344 / 1280      # video px per canvas px
AX, AY = 640, 650     # the anchor, canvas px
MOVE = 0.004


def frames(path):
    w, h = 1344, 768
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def key(rgb):
    f = rgb.astype(np.float32); r, g, b = f[..., 0], f[..., 1], f[..., 2]
    dom = b - np.maximum(r, g)
    a = np.clip((75 - dom) / 45, 0, 1)
    b2 = np.where(a < 1, np.minimum(b, np.maximum(r, g) + 6), b)
    out = np.dstack([r, g, b2, a * 255])
    out[a == 0] = 0
    return out


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    ALL = {}
    for cat, clips in CLIPS.items():
        cells, meta = [], {}
        for name, job in clips.items():
            fr = frames(f"raw/{job}.mp4")
            al = [key(x)[..., 3] / 255 for x in fr[::2]]
            lo, hi = 0, len(fr) - 1
            if name in TRANS:
                d = [np.abs(al[i] - al[i - 1]).mean() for i in range(1, len(al))]
                mv = [i for i, x in enumerate(d) if x > MOVE]
                lo, hi = max(0, (mv[0]) * 2 - 2), min(len(fr) - 1, (mv[-1] + 1) * 2 + 2)
                # the bottom centre of the cat per frame (video px): a takeoff ends when it has arrived where it
                # stays (H3 holds the flying pose for a second and more), a landing starts when it leaves its
                # hovering pose
                def bc(a):   # centroid x and the 97th-percentile bottom (the scarf and tail do not move them much)
                    ys, xs = np.nonzero(a > 0.5); return np.array([xs.mean(), np.percentile(ys, 97)]) if len(xs) else np.array([0, 0])
                pts = [bc(key(fr[i])[..., 3] / 255) for i in range(len(fr))]
                if name == "crouch":   # one hip wiggle, cut where the pose is closest to the takeoff's first frame
                    hi = CROUCH_END[cat]
                if name == "takeoff":   # cut while still rising: the flight in code carries it on
                    end = pts[hi][1]; hi = next(i for i in range(lo, hi + 1) if pts[i][1] <= end + 22)
                if name == "landing":   # start just past the apex H3 adds, already falling
                    ap = min(range(lo, hi + 1), key=lambda i: pts[i][1]); lo = next(i for i in range(ap, hi + 1) if pts[i][1] >= pts[ap][1] + 10)
            seq = []
            for i in range(lo, hi + 1, STEP[name]):
                k = key(fr[i]); im = Image.fromarray(k.astype(np.uint8), "RGBA")
                im = im.resize((round(im.width * SCALE / VX), round(im.height * SCALE / VX)), Image.LANCZOS)
                bb = im.split()[-1].point(lambda v: 255 if v > 8 else 0).getbbox()
                if not bb: continue
                c = im.crop(bb)
                seq.append((c, bb[0] - AX * SCALE, bb[1] - AY * SCALE))
            if name == "landing":
                # the settle after the touch-down: H3 shifts the paws back about 10 px in one frame. Spread that
                # drift evenly from the touch to the last frame, so the paws ease back instead of popping
                def paw(c, dx):   # front-paw x: the rightmost opaque pixel in the bottom 12 % of the frame
                    a = np.array(c.split()[-1]) > 128; r0 = int(a.shape[0] * 0.88)
                    cols = np.nonzero(a[r0:].any(0))[0]; return dx + (cols.max() if len(cols) else 0)
                t = next(i for i, (c, dx, dy) in enumerate(seq) if dy + c.height >= -3)
                px = [paw(c, dx) for c, dx, dy in seq]; n = len(seq) - 1
                for i in range(t + 1, n):
                    want = px[t] + (px[n] - px[t]) * (i - t) / (n - t)
                    c, dx, dy = seq[i]; seq[i] = (c, dx + (want - px[i]), dy)
            meta[name] = seq
            print(cat, name, f"frames {lo}-{hi} -> {len(seq)}")
        # pack: shelves, max width 2048
        allc = [(n, i, s) for n, seq in meta.items() for i, s in enumerate(seq)]
        x = y = sh = 0; W = 2048; pos = {}
        for n, i, (c, dx, dy) in allc:
            if x + c.width > W: x, y, sh = 0, y + sh + 2, 0
            pos[(n, i)] = (x, y); x += c.width + 2; sh = max(sh, c.height)
        assert y + sh <= 4096, "atlas taller than 4096 px: lower SCALE"
        atlas = Image.new("RGBA", (W, y + sh))
        out = {"scale": SCALE, "anchor": [AX * SCALE, AY * SCALE], "fps": 12, "clips": {}}
        for n, i, (c, dx, dy) in allc:
            px, py = pos[(n, i)]; atlas.paste(c, (px, py))
            out["clips"].setdefault(n, []).append([px, py, c.width, c.height, round(dx, 1), round(dy, 1)])
        atlas.save(f"{outdir}/cat-{cat}.webp", "WEBP", quality=72, alpha_quality=80, method=6)
        cl = out["clips"]
        bc = lambda f: [round(f[4] + f[2] / 2, 1), round(f[5] + f[3], 1)]   # bottom centre from the feet
        # the landing touches down at the first frame whose bottom is back on the ridge (within 3 atlas px)
        touch = next(i for i, f in enumerate(cl["landing"]) if f[5] + f[3] >= -3)
        # the takeoff's push-off: the first frame whose feet have left the ridge
        push = next(i for i, f in enumerate(cl["takeoff"]) if f[5] + f[3] < -3)
        ALL[cat] = {"img": f"cat-{cat}.webp", "size": list(atlas.size), "clips": cl, "touch": touch, "push": push,
                    "out": bc(cl["takeoff"][-1]), "in": bc(cl["landing"][0])}
        print(cat, "atlas", atlas.size, os.path.getsize(f"{outdir}/cat-{cat}.webp") // 1024, "KB", "touch", touch, "push", push, "out", ALL[cat]["out"], "in", ALL[cat]["in"])
    ALL["plate"] = round(0.3 / SCALE, 4)   # plate px per atlas px: the game's stills were 0.5 canvas px at 0.6 plate px each
    with open(f"{outdir}/cats.js", "w") as f:
        f.write("/* written by gondar/sprite-refs scripts/roofcats_build.py — the rooftop cats' clips (ukulele-warmup/roofs.js) */\n")
        f.write("window.ROOFCATS = " + json.dumps(ALL, separators=(",", ":")) + ";\n")


if __name__ == "__main__":
    main(sys.argv[1])
