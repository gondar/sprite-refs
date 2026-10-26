#!/usr/bin/env python3
"""Pack the donkey play's lock.py atlases into Palce's strips: one WebP per clip, a grid of equal cells cropped to
what the clip's frames cover, the figure at REF px (frame 0's height), at most 4096 px a side (phones), with the
feet `anchor` in strip pixels — the STRIP format of stajenka.html plus `cols`.

Run from the sprite-refs root:  python3 scripts/wintertown_h3_pack.py [OUT_ROOT]
Reads review/wintertown/h3/{donkey,townsman}/atlas(-clean).png + atlas.json (lock.py, then wintertown_strip_clean.py).
Writes fingerpick-warmup/art/wintertown/{donkey-a,donkey-b,townsman-a,townsman-b}.webp, their entries in
art.json, prints the STRIP lines and each gesture's frame range in its strip."""
import json, os, sys
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "../MusicGames"
PALCE = os.path.join(OUT, "fingerpick-warmup/art/wintertown")
SETS = {   # strip: (lock.py atlas dir, gestures in it, figure height in the strip, WebP quality)
    "donkey-a": ("review/wintertown/h3/donkey", ["bray", "lean"], 240, 50),
    "donkey-b": ("review/wintertown/h3/donkey", ["buck", "hop"], 240, 50),
    "townsman-a": ("review/wintertown/h3/townsman", ["haulfall"], 250, 62),
    "townsman-b": ("review/wintertown/h3/townsman", ["shovestartle"], 250, 62)}
KEEP = 2   # of every 3 frames of lock.py's 12 fps (8 fps): the game spreads them over the act's beats
J = json.load(open(os.path.join(PALCE, "art.json")))
lines = {}
for name, (d, gest, ref, q) in SETS.items():
    A = json.load(open(d + "/atlas.json")); CW, CH = A["cell"]; PX, PY = A["pivot"]
    src = Image.open(d + ("/atlas-clean.png" if os.path.exists(d + "/atlas-clean.png") else "/atlas.png")).convert("RGBA")
    gs = [g for g in A["gestures"] if g["name"] in gest]
    sub = {g["name"]: [i for j, i in enumerate(range(g["at"], g["at"] + g["frames"])) if j % 3 < KEEP or j == g["frames"] - 1] for g in gs}
    idx = [i for g in gs for i in sub[g["name"]]]
    cells = [src.crop(((i % A["cols"]) * CW, (i // A["cols"]) * CH, (i % A["cols"] + 1) * CW, (i // A["cols"] + 1) * CH)) for i in idx]
    # frame 0's figure height sets the scale; the crop is the union of every frame's alpha
    a0 = np.asarray(cells[0].getchannel("A")) > 40; ys = np.nonzero(a0.any(1))[0]; k = ref / (ys.max() - ys.min() + 1)
    box = None
    for c in cells:
        b = c.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0, x1, y1 = box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4
    cw, ch = round((x1 - x0) * k), round((y1 - y0) * k)
    cols = max(1, min(len(cells), 4096 // cw)); rows = (len(cells) + cols - 1) // cols
    if rows * ch > 4096: sys.exit(f"{name}: {rows} rows of {ch} px do not fit 4096")
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    for j, c in enumerate(cells):
        sheet.paste(c.crop((x0, y0, x1, y1)).resize((cw, ch), Image.LANCZOS), ((j % cols) * cw, (j // cols) * ch))
    out = os.path.join(PALCE, name + ".webp")
    sheet.save(out, "WEBP", quality=q, method=6, alpha_quality=70)
    kb = round(os.path.getsize(out) / 1024)
    anchor = [round((PX - x0) * k, 1), round((PY - y0) * k, 1)]
    J["art"][name] = {"cell": [cw, ch], "frames": len(cells), "cols": cols, "anchor": anchor, "ref": ref, "kb": kb}
    at, rng = 0, {}
    for g in gs: rng[g["name"]] = [at, at + len(sub[g["name"]]) - 1]; at += len(sub[g["name"]])
    lines[name] = {"cell": [cw, ch], "frames": len(cells), "cols": cols, "ref": ref, "anchor": anchor}
    print(name, sheet.size, kb, "KB", rng)
json.dump(J, open(os.path.join(PALCE, "art.json"), "w"), indent=1)
print(json.dumps(lines, separators=(",", ":")))
