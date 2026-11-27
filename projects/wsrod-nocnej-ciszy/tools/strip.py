"""strip.py GIF OUT.png [--ref REF.png] [--frames 0,1,2,3] [--h 700]: frames side by side on the scene's night blue,
the reference first, each scaled to the same height, frame numbers in the corner. For looking, not shipping."""
import argparse
from PIL import Image, ImageDraw, ImageSequence
ap = argparse.ArgumentParser(); ap.add_argument("gif"); ap.add_argument("out"); ap.add_argument("--ref")
ap.add_argument("--frames"); ap.add_argument("--h", type=int, default=700); a = ap.parse_args()
fr = [f.convert("RGBA") for f in ImageSequence.Iterator(Image.open(a.gif))]
idx = [int(x) for x in a.frames.split(",")] if a.frames else range(len(fr))
tiles = ([("ref", Image.open(a.ref).convert("RGBA"))] if a.ref else []) + [(str(i), fr[i]) for i in idx]
out = []
for n, im in tiles:
    bb = im.getchannel("A").getbbox() if n != "ref" else im.getchannel("A").getbbox()
    k = a.h / im.height; t = im.resize((max(1, round(im.width * k)), a.h), Image.LANCZOS)
    bg = Image.new("RGBA", t.size, (38, 48, 82, 255)); bg.alpha_composite(t); d = ImageDraw.Draw(bg); d.text((6, 6), n, fill=(255, 255, 0, 255)); out.append(bg)
W = sum(t.width for t in out) + 4 * len(out); c = Image.new("RGB", (W, a.h), (0, 0, 0)); x = 0
for t in out: c.paste(t, (x, 0)); x += t.width + 4
c.save(a.out)
