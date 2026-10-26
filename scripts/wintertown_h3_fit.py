#!/usr/bin/env python3
"""The donkey play's H3 clips come back 1344 x 768 from 1280 x 720 home pictures: fit each home cut-out to a clip's
first frame (one scale, one offset, found by matching the figure's silhouette) and write it at the clip's size, so
lock.py can take --home <name>-home-cut.png --at X,Y.

Run from the sprite-refs root:  python3 scripts/wintertown_h3_fit.py donkey raw/<clip>.mp4
                                python3 scripts/wintertown_h3_fit.py townsman raw/<clip>.mp4"""
import io, json, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "scripts")
from wintertown_donkey_h3 import cut, off_blue, OUT  # noqa: E402

who, clip = sys.argv[1], sys.argv[2]
if who == "donkey": fig, frac = cut("refs/wintertown/gen/sheet-animals-big2.webp", 4, 3, 0, 0), .6
else: fig, frac = off_blue(OUT + "townsman-edit-raw.png"), .64
W0, H0 = 1280, 720
k = frac * H0 / fig.height
fig = fig.resize((round(fig.width * k), round(fig.height * k)), Image.LANCZOS)
x0, y0 = round(W0 * .5 - fig.width / 2), round(H0 * .84 - fig.height)      # where on_blue put it
png = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
f0 = Image.open(io.BytesIO(png)).convert("RGB")
W, H = f0.size
a = np.asarray(f0).astype(int); fm = (a[..., 2] - np.maximum(a[..., 0], a[..., 1])) < 60   # not blue = figure
best = None
for s in np.arange(1.03, 1.09, .0025):
    fw, fh = round(fig.width * s), round(fig.height * s)
    m = np.asarray(fig.resize((fw, fh)).getchannel("A")) > 128
    cx, cy = (x0 + fig.width / 2) * s, (y0 + fig.height) * s                 # bottom centre, scaled
    for dx in range(-30, 31, 2):
        for dy in range(-30, 31, 2):
            X, Y = round(cx - fw / 2 - (W0 * s - W) / 2 + dx), round(cy - fh - (H0 * s - H) / 2 + dy)
            if X < 0 or Y < 0 or X + fw > W or Y + fh > H: continue
            sub = fm[Y:Y + fh, X:X + fw]
            iou = (sub & m).sum() / max(1, (sub | m).sum())
            if not best or iou > best[0]: best = (iou, s, X, Y, fw, fh)
iou, s, X, Y, fw, fh = best
# refine to 1 px
for dx in range(-2, 3):
    for dy in range(-2, 3):
        m = np.asarray(fig.resize((fw, fh)).getchannel("A")) > 128; sub = fm[Y + dy:Y + dy + fh, X + dx:X + dx + fw]
        if sub.shape != m.shape: continue
        v = (sub & m).sum() / max(1, (sub | m).sum())
        if v > best[0]: best = (v, s, X + dx, Y + dy, fw, fh)
iou, s, X, Y, fw, fh = best
out = OUT + "%s-home-cut.png" % who
fig.resize((fw, fh), Image.LANCZOS).save(out)
print(json.dumps({"home": out, "at": [X, Y], "scale": round(float(s), 4), "iou": round(float(iou), 3), "size": [fw, fh]}))
