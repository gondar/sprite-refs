"""Zenek Kosmita for the a ↔ F film (MusicGames ukulele-warmup/film.js): MiniMax-H3 clips → keyed frame sheets.

Clips (first frame = last frame = refs/ukuziom/zenek-home-blue.png, flat blue ground; prompts in
jobs/prompts/ukuziom/zenek-*.txt):
  run         jogging in place — one stride (two steps) cut as a loop starting on a foot contact
  wave        wave + head tilt (the 2026-10-31 clip)
  cheer       jump with fists up + clap
  dance       hip-wiggle dance + a full spin
  float       thumbs up and wink + floating up weightless
  airuke      strumming an imaginary ukulele + a bow

Every frame is keyed on how much blue DOMINATES (B − max(R, G)): the ground and the model's soft shadow are blue-dominant,
the silver suit, the green head and the yellow antenna balls are not. Only the blue region connected to the frame's
border is ground (the dark eyes never key away); the edge gets a soft alpha and its blue spill is pulled down to
max(R, G). All clips share one crop box (the union of the figure over every frame, padded) and one scale, so Zenek is the
same size in every animation and his feet stand on the same line.

Run:  python3 scripts/zenek_film.py OUTDIR [--height 400]
Out:  OUTDIR/zenek-<name>.webp (a grid of cells) + OUTDIR/zenek-film.json (cell, cols, frames, fps, loop, contacts)
"""
import json, subprocess, sys, os, tempfile, glob
import numpy as np
from PIL import Image
from scipy import ndimage   # pip install scipy

RAW = os.path.join(os.path.dirname(__file__), "..", "raw")
CLIPS = {
    "run": "20261113-072509-bafd5c",
    "wave": "20261031-161921-1a2f72",
    "cheer": "20261113-072511-856de3",
    "dance": "20261113-072513-6b9ce8",
    "float": "20261113-072515-b8b7ad",
    "airuke": "20261113-075008-29d744",
}

def frames(job):
    d = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(RAW, job + ".mp4"), os.path.join(d, "f%04d.png")], check=True)
    return [np.asarray(Image.open(f).convert("RGB")).astype(np.int16) for f in sorted(glob.glob(os.path.join(d, "f*.png")))]

def key(a):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    dom = B - np.maximum(R, G)
    lab, _ = ndimage.label(dom > 45)                            # blue regions; the ground is the one(s) touching the border
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    ground = np.isin(lab, edge[edge > 0])
    alpha = np.clip((70 - dom) / 40.0, 0, 1)                 # soft edge from the blue dominance
    alpha = np.where(ground, np.minimum(alpha, 0.0), 1.0)      # ground: gone; everything not reached from the border: kept
    # the edge band: pixels next to the ground take the soft alpha
    g = ground.astype(np.uint8); band = np.zeros_like(g)
    band[1:, :] |= g[:-1, :]; band[:-1, :] |= g[1:, :]; band[:, 1:] |= g[:, :-1]; band[:, :-1] |= g[:, 1:]
    soft = (band == 1) & ~ground
    alpha = np.where(soft, np.clip((80 - dom) / 50.0, 0, 1), alpha)
    out = a.copy(); mx = np.maximum(R, G)
    spill = (alpha < 1) & (B > mx)
    out[..., 2] = np.where(spill, mx + (B - mx) * 0.15, B)    # despill the edge
    return np.dstack([np.clip(out, 0, 255), (alpha * 255).round()]).astype(np.uint8)

def bbox(rgba):
    ys, xs = np.nonzero(rgba[..., 3] > 24)
    return xs.min(), ys.min(), xs.max(), ys.max()

def best_loop(fr, period_guess=23, search=(18, 30)):
    """the run: a stride loop that starts on a foot contact (the head at its lowest) and joins back on itself best"""
    small = [np.asarray(Image.fromarray(f[..., :3]).convert("L").resize((96, 96))).astype(float) for f in fr]
    tops = [bbox(f)[1] for f in fr]
    best = None
    for s in range(12, len(fr) - search[1] - 12):
        if not (tops[s] >= max(tops[s - 2:s + 3])): continue   # a contact: the head at a local lowest point (largest y)
        for P in range(*search):
            d = np.abs(small[s] - small[s + P]).mean()
            if best is None or d < best[0]: best = (d, s, P)
    d, s, P = best
    mid = s + int(np.argmax([tops[s + k] if abs(k - P / 2) < 3 else -1 for k in range(P)]))
    return s, P, mid - s, d

def main():
    out = sys.argv[1]; H = 400
    if "--height" in sys.argv: H = int(sys.argv[sys.argv.index("--height") + 1])
    os.makedirs(out, exist_ok=True)
    keyed = {n: [key(f) for f in frames(j)] for n, j in CLIPS.items() if os.path.exists(os.path.join(RAW, j + ".mp4"))}
    # one crop box for all: the union of every frame's figure, padded
    bx = [bbox(f) for fr in keyed.values() for f in fr]
    x0, y0 = min(b[0] for b in bx) - 8, min(b[1] for b in bx) - 8
    x1, y1 = max(b[2] for b in bx) + 8, max(b[3] for b in bx) + 8
    home = keyed["run"][0]; hb = bbox(home)
    fig = hb[3] - hb[1]                                       # the standing figure, antenna ball to sole
    sc = H / fig
    cw, ch = int(round((x1 - x0) * sc)), int(round((y1 - y0) * sc))
    meta = {"cell": [cw, ch], "figure": H, "feet": round((hb[3] - y0) * sc, 1), "cx": round(((hb[0] + hb[2]) / 2 - x0) * sc, 1), "fps": 24, "clips": {}}
    for n, fr in keyed.items():
        sel = list(range(len(fr)))
        info = {}
        if n == "run":
            s, P, c2, d = best_loop(fr)
            sel = list(range(s, s + P)); info = {"loop": True, "contacts": [0, c2], "joinMAE": round(float(d), 2)}
        cols = min(12, len(sel)); rows = (len(sel) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
        for k, i in enumerate(sel):
            im = Image.fromarray(fr[i]).crop((x0, y0, x1, y1)).resize((cw, ch), Image.LANCZOS)
            sheet.paste(im, ((k % cols) * cw, (k // cols) * ch))
        sheet.save(os.path.join(out, "zenek-" + n + ".webp"), quality=78, method=6)
        meta["clips"][n] = {"src": "zenek-" + n + ".webp", "n": len(sel), "cols": cols, **info}
        print(n, len(sel), info)
    json.dump(meta, open(os.path.join(out, "zenek-film.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k != "clips"}))

if __name__ == "__main__":
    main()
