import json, sys, numpy as np
from PIL import Image
S = sys.argv[1]; OUT = sys.argv[2]
# name: (dir, [sheet frame idx in strip order], home idx, baselines: row-y-ranges -> baseline)
CH = {
 "leon":     ("leon3",     [3, 5, 4, 0, 2], 0, 240),
 "zenek":    ("zenek3",    [1, 2, 3, 0], 0, 240),
 "konfetka": ("konfetka3", [1, 2, 3, 0], 3, 240),
}
info = {}
for name, (d, order, home, CH_H) in CH.items():
    bbs = {}
    for line in open(f"{S}/{d}.txt"):
        k, _, _, y0, y1, _, x0, x1, *_ = line.split(); bbs[int(k)] = (int(y0), int(y1), int(x0), int(x1))
    # baseline per frame = the lowest bottom among the frames in the same sheet row (same y band)
    def base(k):
        y0, y1 = bbs[k][:2]; return max(b[1] for b in bbs.values() if abs((b[0] + b[1]) / 2 - (y0 + y1) / 2) < 250)
    fr = []
    for k in order:
        im = Image.open(f"{S}/{d}/f{k:02d}.png"); a = np.asarray(im)[..., 3] > 40
        ys, xs = np.nonzero(a); cx = xs.mean(); lift = base(k) - bbs[k][1]
        fr.append((im, cx, lift))
    tall = max(im.height + lift for im, cx, lift in fr)
    s = (CH_H - 8) / tall
    half = max(max(cx, im.width - cx) for im, cx, lift in fr) * s
    W = int(2 * half + 8); H = CH_H
    strip = Image.new("RGBA", (W * len(fr), H))
    for i, (im, cx, lift) in enumerate(fr):
        t = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        x = i * W + int(W / 2 - cx * s); y = int(H - 4 - lift * s - t.height)
        strip.alpha_composite(t, (max(x, i * W), max(y, 0)))
    strip.save(f"{OUT}/{name}-hop.webp", quality=80, alpha_quality=85, method=6)
    strip.save(f"{S}/{name}-hop.png")
    info[name] = dict(n=len(fr), cell=[W, H], home=home)
    print(name, info[name], strip.size)
json.dump(info, open(f"{S}/pack.json", "w"))
