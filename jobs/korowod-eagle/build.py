#!/usr/bin/env python3
"""Korowód eagle: cut the keyed clips into clips that start/end on the clean pictures, put every frame in ONE
uniform cell on ONE anchor, pack pages and write eagle.json + the single pictures + review sheets/GIFs.

usage: build.py SPEC.json
SPEC: {"work": dir with <clip>/k_###.png, "pics": {"home": place-home.png, "perch": …, "herb": …},
       "centre": [x, y] (body centre in canvas px), "cell_max": 512, "out": game dir, "review": dir,
       "clips": [{"name": "flap", "src": "<clip dir>", "from": i0, "to": i1, "step": 2, "start": "home",
                  "end": "home", "loop": true, "ease": 2, "down": k (optional, cycle frame) , "hold": n}]}
For a loop the last (home) frame is dropped so the cycle can repeat without a doubled frame."""
import json, os, sys
import numpy as np
from PIL import Image

S = json.load(open(sys.argv[1]))
W = S["work"]
pics = {k: np.asarray(Image.open(v).convert("RGBA"), float) for k, v in S["pics"].items()}

def load(src, i): return np.asarray(Image.open(f"{W}/{src}/k_{i:03d}.png").convert("RGBA"), float)

def blend(f, g, w):  # premultiplied: w of f, 1-w of g
    fa, ga = f[..., 3:] / 255, g[..., 3:] / 255
    pa = fa * w + ga * (1 - w)
    rgb = (f[..., :3] * fa * w + g[..., :3] * ga * (1 - w)) / np.maximum(pa, 1e-3)
    return np.dstack([rgb, pa * 255])

clips = []
for c in S["clips"]:
    if "idx" in c: idx = c["idx"]
    else:
        idx = list(range(c["from"], c["to"] + 1, c.get("step", 2)))
        if idx[-1] != c["to"]: idx.append(c["to"])
    seq = [load(c["src"], i) for i in idx]
    st, en, e = pics[c["start"]], pics[c["end"]], c.get("ease", 2)
    n = len(seq)
    seq[0] = st; seq[-1] = en
    for j in range(1, e + 1):                       # ease the clip's own render into the clean pictures
        w = j / (e + 1)
        if j < n - 1: seq[j] = blend(seq[j], st, w)
        if n - 1 - j > 0: seq[n - 1 - j] = blend(seq[n - 1 - j], en, w)
    if c.get("loop"): seq = seq[:-1]
    seq += [en] * c.get("hold", 0)
    clips.append((c, seq, idx))

# one cell for every frame: union bbox of alpha over all frames, + pad, scaled to <= cell_max
allf = [f for _, s, _ in clips for f in s]
m = np.zeros(allf[0].shape[:2], bool)
for f in allf: m |= f[..., 3] > 8
ys, xs = np.nonzero(m); pad = 6
x0, y0, x1, y1 = xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad
cx, cy = S["centre"]
# keep the anchor at a fixed spot: make the box symmetric-ish is not needed, just record where it lands
bw, bh = x1 - x0, y1 - y0
sc = S["cell_max"] / max(bw, bh)
CW, CH = int(np.ceil(bw * sc)), int(np.ceil(bh * sc))
anchor = [round((cx - x0) * sc, 1), round((cy - y0) * sc, 1)]
def cellify(f):
    im = Image.fromarray(np.clip(np.round(f), 0, 255).astype(np.uint8), "RGBA").crop((x0, y0, x1, y1))
    return im.resize((CW, CH), Image.LANCZOS)          # Pillow resamples RGBA premultiplied
cells = [cellify(f) for f in allf]

out = S["out"]; os.makedirs(out, exist_ok=True)
cols = 4096 // CW; rows = 4096 // CH; per = cols * rows
npages = (len(cells) + per - 1) // per
# balance: use as few rows on the last page as needed
pages = []
for p in range(npages):
    chunk = cells[p * per:(p + 1) * per]
    r = (len(chunk) + cols - 1) // cols
    pg = Image.new("RGBA", (cols * CW, r * CH), (0, 0, 0, 0))
    for j, c in enumerate(chunk): pg.paste(c, ((j % cols) * CW, (j // cols) * CH))
    fn = f"eagle-p{p}.webp"; pg.save(os.path.join(out, fn), "WEBP", quality=S.get("q", 80), method=6, alpha_quality=S.get("aq", 90))
    pages.append({"src": f"art/korowod/{fn}", "cols": cols, "rows": r})
man = {"cell": [CW, CH], "anchor": anchor, "fps": S.get("fps", 12), "pages": [], "clips": {}}
# uniform cols*rows per page for the index formula floor(i/(C*R)): every page declares the same cols and rows
for p in pages: p["rows"] = rows if npages > 1 else p["rows"]
man["pages"] = pages
at = 0
for c, s, idx in clips:
    e = {"at": at, "frames": len(s)}
    if "down" in c: e["down"] = c["down"]
    if c.get("loop"): e["loop"] = True
    if c.get("hold"): e["hold"] = c["hold"]
    e["src"] = f'{c["src"]} {idx[0]}-{idx[-1]}'
    man["clips"][c["name"]] = e; at += len(s)
json.dump(man, open(os.path.join(out, "eagle.json"), "w"), indent=1)

# single pictures in the same cell (same anchor), so the game can swap them without a jump
for k, fn in [("home", "eagle.webp"), ("perch", "eagle-perch.webp"), ("herb", "eagle-herb.webp")]:
    cellify(pics[k]).save(os.path.join(out, fn), "WEBP", quality=88, method=6, alpha_quality=95)

# review: a strip per clip + GIF per clip on sky blue
rv = S["review"]; os.makedirs(rv, exist_ok=True)
tw = 160; th = round(tw * CH / CW); i = 0; sky = (150, 185, 225, 255)
strip = Image.new("RGB", (12 * tw, th * len(clips)), (40, 40, 40))
for r, (c, s, _) in enumerate(clips):
    seqc = cells[i:i + len(s)]
    for k in range(12):
        f = seqc[round(k * (len(seqc) - 1) / 11)].resize((tw, th), Image.LANCZOS)
        bg = Image.new("RGBA", (tw, th), sky); bg.alpha_composite(f); strip.paste(bg.convert("RGB"), (k * tw, r * th))
    gif = []
    for f in seqc * (3 if c.get("loop") else 1):
        bg = Image.new("RGBA", (CW, CH), sky); bg.alpha_composite(f); gif.append(bg.convert("RGB").quantize(128))
    gif[0].save(os.path.join(rv, f"{c['name']}.gif"), save_all=True, append_images=gif[1:], duration=int(1000 / S.get("fps", 12)), loop=0)
    i += len(s)
strip.save(os.path.join(rv, "contact.png"))
print(json.dumps({k: v for k, v in man.items() if k != "clips"}), len(cells), "frames")
for k, v in man["clips"].items(): print(k, v)
