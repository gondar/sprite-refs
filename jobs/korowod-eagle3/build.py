#!/usr/bin/env python3
"""Korowód eagle3: cut keyed clips (frames.py output) into clips that start/end on the CLEAN pictures, put every
frame in ONE uniform cell centred on ONE anchor (the body centre shared by all three pictures, prep.py), pack pages
<= 4096 px, write eagle.json + the stills (same cell, anchor at the centre: the game draws stills centred and frames
by the anchor, so they coincide) + the menu card + review sheets/GIFs.
usage: build.py SPEC.json
SPEC: {"work": dir of clip dirs, "cell_max": 448, "q": 70, "aq": 80, "fps": 12, "out": dir, "review": dir,
       "clips": [{"name", "src", "idx": [...] | "from","to","step", "start": pose, "end": pose, "loop": bool,
                  "ease": 2, "down": k, "hold": n}]}"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
S = json.load(open(sys.argv[1])); W = S["work"]
A = "/home/user/sprite-refs/refs/korowod/eagle3/anim"; P = json.load(open(A + "/place.json"))
pics = {k: np.asarray(Image.open(f"{A}/place-{k}.png").convert("RGBA"), float) for k in ["home", "perch", "herb"]}
WORK = pics["home"].shape[0]; f = WORK / P["S"]; AX, AY = P["anchor"][0] * f, P["anchor"][1] * f
load = lambda src, i: np.asarray(Image.open(f"{W}/{src}/k_{i:03d}.png").convert("RGBA"), float)
def blend(a, b, w):  # premultiplied: w of a, 1-w of b
    fa, ga = a[..., 3:] / 255, b[..., 3:] / 255; pa = fa * w + ga * (1 - w)
    return np.dstack([(a[..., :3] * fa * w + b[..., :3] * ga * (1 - w)) / np.maximum(pa, 1e-3), pa * 255])
clips = []
for c in S["clips"]:
    idx = c.get("idx") or list(range(c["from"], c["to"] + 1, c.get("step", 2)))
    seq = [load(c["src"], i) for i in idx]; st, en, e, n = pics[c["start"]], pics[c["end"]], c.get("ease", 2), len(seq)
    if c.get("pin0", True): seq[0] = st
    if c.get("pin1", True): seq[-1] = en
    for j in range(1, e + 1):                   # ease the clip's own render into the clean pictures
        w = j / (e + 1)
        if c.get("pin0", True) and j < n - 1: seq[j] = blend(seq[j], st, w)
        if c.get("pin1", True) and n - 1 - j > 0: seq[n - 1 - j] = blend(seq[n - 1 - j], en, w)
    if c.get("loop"): seq = seq[:-1]
    seq += [en] * c.get("hold", 0); clips.append((c, seq, idx))
allf = [x for _, s, _ in clips for x in s] + list(pics.values())
m = np.zeros((WORK, WORK), bool)
for x in allf: m |= x[..., 3] > 8
ys, xs = np.nonzero(m); pad = 4
hw = max(AX - xs.min(), xs.max() - AX) + pad; hh = max(AY - ys.min(), ys.max() - AY) + pad   # half sizes about the anchor
x0, y0, x1, y1 = AX - hw, AY - hh, AX + hw, AY + hh
sc = S["cell_max"] / max(2 * hw, 2 * hh); CW, CH = int(round(2 * hw * sc)), int(round(2 * hh * sc))
M = int(max(0, -x0, -y0, x1 - WORK, y1 - WORK)) + 2       # the cell is symmetric about the anchor: pad the canvas
def cellify(x):
    im = Image.fromarray(np.pad(np.clip(np.round(x), 0, 255).astype(np.uint8), ((M, M), (M, M), (0, 0))), "RGBA")
    return im.resize((CW, CH), Image.LANCZOS, box=(x0 + M, y0 + M, x1 + M, y1 + M))
cells = [cellify(x) for _, s, _ in clips for x in s]
out = S["out"]; os.makedirs(out, exist_ok=True)
cols = 4096 // CW; maxr = 4096 // CH; npg = -(-len(cells) // (cols * maxr)); rows = -(-len(cells) // (cols * npg))
for fn in os.listdir(out):
    if fn.startswith("eagle-p") and fn.endswith(".webp"): os.remove(os.path.join(out, fn))
pages = []; per = cols * rows
for p in range(npg):
    chunk = cells[p * per:(p + 1) * per]; r = -(-len(chunk) // cols)
    pg = Image.new("RGBA", (cols * CW, r * CH), (0, 0, 0, 0))
    for j, cc in enumerate(chunk): pg.paste(cc, ((j % cols) * CW, (j // cols) * CH))
    fn = f"eagle-p{p}.webp"; pg.save(os.path.join(out, fn), "WEBP", quality=S.get("q", 70), method=6, alpha_quality=S.get("aq", 80))
    pages.append({"src": f"art/korowod/{fn}", "cols": cols, "rows": r})
man = {"cell": [CW, CH], "anchor": [round((AX - x0) * sc, 1), round((AY - y0) * sc, 1)], "fps": S.get("fps", 12),
       "pages": pages, "clips": {}}
at = 0
for c, s, idx in clips:
    e = {"at": at, "frames": len(s)}
    if "down" in c: e["down"] = c["down"]
    man["clips"][c["name"]] = e; at += len(s)
json.dump(man, open(os.path.join(out, "eagle.json"), "w"), indent=1)
for k, fn in [("home", "eagle.webp"), ("perch", "eagle-perch.webp"), ("herb", "eagle-herb.webp")]:
    cellify(pics[k]).save(os.path.join(out, fn), "WEBP", quality=88, method=6, alpha_quality=95)
# menu card: the home bird from the full-resolution cut-out, square, ~300 px
hp = Image.open(f"{A}/../home.png").convert("RGB")
sys.path.insert(0, "/home/user/sprite-refs/jobs/korowod-eagle"); from ekey import key
k = Image.fromarray(np.round(key(np.asarray(hp, float), min_area=2000)).astype(np.uint8), "RGBA"); bb = k.getbbox()
side = max(bb[2] - bb[0], bb[3] - bb[1]) + 40; cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
k.resize((300, 300), Image.LANCZOS, box=(cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)).save(os.path.join(out, "eagle-card.webp"), "WEBP", quality=88, method=6, alpha_quality=95)
# review: contact sheet + GIF per clip on sky, the anchor marked on the sheet
rv = S["review"]; os.makedirs(rv, exist_ok=True); sky = (150, 185, 225, 255); i = 0
for c, s, _ in clips:
    sq = cells[i:i + len(s)]; i += len(s); tw = 200; th = round(tw * CH / CW); nc = 8
    sh = Image.new("RGB", (nc * tw, -(-len(sq) // nc) * th), (40, 40, 40)); dr = ImageDraw.Draw(sh)
    for j, x in enumerate(sq):
        bg = Image.new("RGBA", (CW, CH), sky); bg.alpha_composite(x); X, Y = (j % nc) * tw, (j // nc) * th
        sh.paste(bg.convert("RGB").resize((tw, th), Image.LANCZOS), (X, Y))
        ax, ay = X + man["anchor"][0] * tw / CW, Y + man["anchor"][1] * th / CH; dr.line((ax - 4, ay, ax + 4, ay), fill=(255, 0, 0)); dr.line((ax, ay - 4, ax, ay + 4), fill=(255, 0, 0))
        dr.text((X + 3, Y + 2), str(j) + (" DOWN" if c.get("down") == j else ""), fill=(255, 255, 0))
    sh.save(os.path.join(rv, f"{c['name']}-sheet.png"))
    gif = []
    for x in sq * (3 if c.get("loop") else 1):
        bg = Image.new("RGBA", (CW, CH), sky); bg.alpha_composite(x); gif.append(bg.convert("RGB").quantize(128))
    gif[0].save(os.path.join(rv, f"{c['name']}.gif"), save_all=True, append_images=gif[1:], duration=int(1000 / S.get("fps", 12)), loop=0)
tot = sum(os.path.getsize(os.path.join(out, fn)) for fn in os.listdir(out) if fn.startswith("eagle"))
print(json.dumps({k: v for k, v in man.items() if k != "clips"}), len(cells), "frames", f"{tot / 1e6:.2f} MB")
for k, v in man["clips"].items(): print(k, v)
