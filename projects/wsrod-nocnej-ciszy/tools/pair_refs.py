"""pair_refs.py: the wake's two reference pictures on ONE shared 960 px square — the sleeping dog (dog-sleep GIF frame 0)
and the sitting dog (dog-sit GIF frame 0) each placed exactly where the game draws them (process-results: static px =
scale·gif px + offset), so frame 1 and frame 8 of the wake are asked for at the right size and on the same ground line.
Writes refs/dog-wake-from.png and refs/dog-wake-to.png. No network."""
import json, os
import numpy as np
from PIL import Image, ImageSequence
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(HERE, "process-results.json")))
def f0(name):
    return next(ImageSequence.Iterator(Image.open(os.path.join(HERE, "gifs", name + ".gif")))).convert("RGBA")
def place(name):   # -> image in static-cell px and its top-left there
    im = f0(name); s = R[name]["scale"]; dx, dy = R[name]["offset"]
    if name == "dog-sleep":   # its offset is in cell space after the feet anchor (see process.py); same formula
        pass
    big = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return big, (dx, dy)
items = [place(n) for n in ("dog-sleep", "dog-sit")]
boxes = []
for big, (dx, dy) in items:
    x0, y0, x1, y1 = big.getchannel("A").getbbox(); boxes.append((x0 + dx, y0 + dy, x1 + dx, y1 + dy))
X0 = min(b[0] for b in boxes); Y0 = min(b[1] for b in boxes); X1 = max(b[2] for b in boxes); Y1 = max(b[3] for b in boxes)
side = max(X1 - X0, Y1 - Y0); k = 880 / side
ox = (960 - (X1 - X0) * k) / 2 - X0 * k; oy = 960 - 40 - Y1 * k
for (big, (dx, dy)), out in zip(items, ("dog-wake-from.png", "dog-wake-to.png")):
    sm = big.resize((round(big.width * k), round(big.height * k)), Image.LANCZOS)
    cv = Image.new("RGBA", (960, 960), (0, 0, 0, 0)); cv.alpha_composite(sm, (int(round(dx * k + ox)), int(round(dy * k + oy))))
    cv.save(os.path.join(HERE, "refs", out)); print(out, cv.getchannel("A").getbbox())
