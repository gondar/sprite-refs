"""onion.py CLIP OUT.png: static art (at output scale, placed by the same anchor) | frame 0 | onion skin (static red, frame cyan) | rim close-up 2x."""
import json, sys, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ART = "/home/user/MusicGames/fingerpick-warmup/art/wsrod-nocnej-ciszy"
name, out = sys.argv[1], sys.argv[2]
R = json.load(open(os.path.join(HERE, "process-results.json")))[name]
f0 = Image.open(os.path.join(HERE, "frames", name, "frame_000.png")).convert("RGBA")
aj = json.load(open(os.path.join(ART, "art.json")))["cast"][R["static"]]
st = Image.open(os.path.join(ART, aj["file"])).convert("RGBA"); k = R["outScale"]
st = st.resize((round(st.width * k), round(st.height * k)), Image.LANCZOS)
key = "seat" if "seat" in R["anchors"] else "feet"
ax, ay = R["anchors"][key]; sx, sy = aj["anchor"][key]
canvas = Image.new("RGBA", f0.size, (0, 0, 0, 0)); canvas.alpha_composite(st, (round(ax - sx * k), round(ay - sy * k))) if (ax - sx * k) >= 0 and (ay - sy * k) >= 0 else canvas.paste(st, (round(ax - sx * k), round(ay - sy * k)), st)
bg = lambda im: (lambda b: (b.alpha_composite(im), b)[1])(Image.new("RGBA", im.size, (38, 48, 82, 255)))
a1 = np.array(canvas)[..., 3] > 127; a2 = np.array(f0)[..., 3] > 127
on = np.zeros(a1.shape + (3,), np.uint8); on[a1] = (200, 60, 60); on[a2] = (60, 200, 220); on[a1 & a2] = (230, 230, 230)
crop = f0.crop((f0.width // 3, 0, f0.width // 3 + f0.width // 2, f0.height // 3)); crop = bg(crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST))
tiles = [bg(canvas), bg(f0), Image.fromarray(on).convert("RGBA"), crop]
W = sum(t.width for t in tiles) + 12; H = max(t.height for t in tiles)
c = Image.new("RGB", (W, H)); x = 0
for t in tiles: c.paste(t.convert("RGB"), (x, 0)); x += t.width + 4
c.save(out)
