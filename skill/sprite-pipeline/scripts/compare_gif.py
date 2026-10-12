#!/usr/bin/env python3
"""Side-by-side animated GIF of several packed strips, each playing at its own frame count, all on one clock.
usage: compare_gif.py OUT.gif --fps 8 --scale 2 --bg 2a1e3a LABEL=STRIP.png[:META.json] ...
The canvas loops after lcm-free 24 ticks (3 s at 8 fps): enough to see every loop's seam several times."""
import sys, json, argparse
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("items", nargs="+")
ap.add_argument("--fps", type=float, default=8); ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--bg", default="2a1e3a"); ap.add_argument("--ticks", type=int, default=24)
a = ap.parse_args()
bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4))
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
cols = []
for it in a.items:
    label, path = it.split("=", 1)
    meta = json.load(open(path[:-4] + ".json"))
    cw, ch = meta["cell"]; S = Image.open(path).convert("RGBA")
    fr = [S.crop((i * cw, 0, (i + 1) * cw, ch)) for i in range(meta["frames"])]
    if meta.get("pingpong"): fr += fr[-2:0:-1]
    cols.append((label, fr, cw, ch))
W = sum(c[2] for c in cols) * a.scale + 10 * (len(cols) + 1); H = max(c[3] for c in cols) * a.scale + 30
frames = []
for t in range(a.ticks):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im); x = 10
    for label, fr, cw, ch in cols:
        c = fr[t % len(fr)].resize((cw * a.scale, ch * a.scale), Image.LANCZOS)
        im.paste(c, (x, 24 + H - 30 - ch * a.scale), c); d.text((x, 5), label, fill=(240, 230, 210), font=f)
        x += cw * a.scale + 10
    frames.append(im)
frames[0].save(a.out, save_all=True, append_images=frames[1:], duration=round(1000 / a.fps), loop=0)
print(a.out, W, H)
