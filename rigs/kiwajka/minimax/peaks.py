"""peaks.py PACKDIR OUTDIR: for every gesture, its peak cell at 2x next to the raw clip frame it came from (cropped to the
same region, same scale) -> OUTDIR/peak-<g>.png; plus a strip of every 2nd frame -> OUTDIR/row-<g>.png"""
import json, sys, os, re, subprocess
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(D)
F = json.load(open(D + '/fit.json')); s, tx, ty = F['s'], F['tx'], F['ty']
pk, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
m = json.load(open(pk + '/atlas.json')); A = Image.open(pk + '/atlas.png'); W, H = m['cell']
tx += m['box'][0] - 16; ty += m['box'][1] - 12
CLIPS = json.load(open(D + '/clips.json'))      # gesture -> [lockdir, job, first source frame (24 fps), step]
for g in m['gestures']:
    PK = dict(x.split('=') for x in os.environ.get('PEAKS', '').split(',') if x)
    k = int(PK.get(g['name'], g['peak'])); i = g['at'] + k
    c = A.crop(((i % m['cols']) * W, (i // m['cols']) * H, (i % m['cols'] + 1) * W, (i // m['cols'] + 1) * H))
    bg = Image.new('RGBA', (W, H), (47, 107, 216, 255)); bg.alpha_composite(c)
    lockdir, job, f0, step = CLIPS[g['name']]
    src = f'{SP}/{lockdir}/{job}/src/f_{f0 + k * step + 1:03d}.png'
    raw = Image.open(src).convert('RGB')
    # the cell's region in the frame: frame = (cell - t) / s
    box = (-tx / s, -ty / s, (W - tx) / s, (H - ty) / s)
    rc = raw.crop(tuple(round(v) for v in box)).resize((2 * W, 2 * H), Image.LANCZOS)
    im = Image.new('RGB', (4 * W + 10, 2 * H), (30, 30, 30))
    im.paste(bg.convert('RGB').resize((2 * W, 2 * H), Image.LANCZOS), (0, 0)); im.paste(rc, (2 * W + 10, 0))
    im.save(f"{out}/peak-{g['name']}.png")
    n = g['frames']; sel = list(range(0, n, 2)) + ([n - 1] if (n - 1) % 2 else [])
    row = Image.new('RGB', (len(sel) * W, H), (90, 90, 90))
    for j, kk in enumerate(sel):
        ii = g['at'] + kk; cc = A.crop(((ii % m['cols']) * W, (ii // m['cols']) * H, (ii % m['cols'] + 1) * W, (ii // m['cols'] + 1) * H))
        t = Image.new('RGBA', (W, H), (90, 90, 90, 255)); t.alpha_composite(cc); row.paste(t.convert('RGB'), (j * W, 0))
    row.save(f"{out}/row-{g['name']}.png")
    print(g['name'], 'peak', k, 'src', os.path.basename(src))
