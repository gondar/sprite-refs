#!/usr/bin/env python3
"""Pack exported frames (export_frames.py's folder) into a spritesheet + an animation manifest.

usage: build_spritesheet.py FRAMES_DIR OUT.(png|webp) --name NAME [--cols N] [--gap 0] [--quality 90]
                            [--duration-ms MS] [--no-loop] [--manifest OUT.json]

The sheet is a grid, left to right then top to bottom (--cols defaults to all frames in one row: a strip,
which is what a CSS `steps()` animation wants). WebP keeps full 8-bit alpha (GIF cannot), and is usually
5–20x smaller than the GIF it came from. The manifest records measured values only:

  {"name", "image", "frames", "frameWidth", "frameHeight", "cols", "rows", "gap",
   "frameDurationMs" (when every frame has the same duration), "durationsMs", "loop",
   "rects": [[x, y, w, h], ...], "bytes", "source"}

--duration-ms overrides the GIF timing (e.g. the game drives it from the tempo) and says so in
"timingOverridden". The script refuses frames of different sizes.
"""
import argparse, json, os, glob
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames_dir"); ap.add_argument("out")
    ap.add_argument("--name", required=True)
    ap.add_argument("--cols", type=int, default=0)
    ap.add_argument("--gap", type=int, default=0)
    ap.add_argument("--quality", type=int, default=90)
    ap.add_argument("--duration-ms", type=int, default=None)
    ap.add_argument("--no-loop", action="store_true")
    ap.add_argument("--manifest", default=None)
    a = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(a.frames_dir, "frame_*.png")))
    if not paths:
        raise SystemExit("no frame_*.png in %s" % a.frames_dir)
    fr = [Image.open(p).convert("RGBA") for p in paths]
    sizes = {f.size for f in fr}
    if len(sizes) != 1:
        raise SystemExit("frames differ in size: %s" % sorted(sizes))
    meta_in = {}
    mp = os.path.join(a.frames_dir, "frames.json")
    if os.path.exists(mp):
        meta_in = json.load(open(mp))
    w, h = fr[0].size
    n = len(fr); cols = a.cols or n; rows = (n + cols - 1) // cols; g = a.gap
    sheet = Image.new("RGBA", (cols * w + (cols - 1) * g, rows * h + (rows - 1) * g), (0, 0, 0, 0))
    rects = []
    for i, f in enumerate(fr):
        x, y = (i % cols) * (w + g), (i // cols) * (h + g)
        sheet.paste(f, (x, y)); rects.append([x, y, w, h])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    if a.out.lower().endswith(".webp"):
        sheet.save(a.out, "WEBP", quality=a.quality, method=6, exact=False)
    else:
        sheet.save(a.out, optimize=True)
    durs = meta_in.get("durationsMs") or [None] * n
    if a.duration_ms:
        durs = [a.duration_ms] * n
    loop = (not a.no_loop) and (meta_in.get("loop", 0) is not None)
    man = {"name": a.name, "image": os.path.basename(a.out), "frames": n, "frameWidth": w, "frameHeight": h,
           "cols": cols, "rows": rows, "gap": g,
           "frameDurationMs": durs[0] if len(set(durs)) == 1 else None, "durationsMs": durs,
           "loop": loop, "timingOverridden": bool(a.duration_ms), "rects": rects,
           "bytes": os.path.getsize(a.out), "source": meta_in.get("source")}
    out_m = a.manifest or os.path.splitext(a.out)[0] + ".json"
    json.dump(man, open(out_m, "w"), indent=2)
    print(json.dumps({k: man[k] for k in ("name", "image", "frames", "frameWidth", "frameHeight", "cols", "rows", "frameDurationMs", "loop", "bytes")}))


if __name__ == "__main__":
    main()
