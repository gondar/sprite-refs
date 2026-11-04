"""lock.py output at frame size (cell 768, identity placement) -> the shipped idle cell (276x268), rebased on the shipped
home (monkey.webp at 16,12), so the ends of every MiniMax gesture are the cutout atlas's cell 0 exactly.

usage: pack.py OUTDIR LOCKDIR[:gesture[@i0-i1]] ...   writes OUTDIR/atlas.png + atlas.json (score.py format),
       OUTDIR/frames/<g>_NN.png, OUTDIR/strip-<g>.png, OUTDIR/peak-<g>.png"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fit import place, cell as HOME0, big as REST_BIG
F = json.load(open(os.path.dirname(os.path.abspath(__file__)) + '/fit.json'))
S, TX, TY = F['s'], F['tx'], F['ty']
# the MiniMax atlas's own cell: the cutout cell (16,12 | 30,0 around the 230x256 box) grown for a hop and a cheer
ML, MT, MR, MB = map(int, os.environ.get('MARGINS', '28,40,30,0').split(','))
CW, CH = 230 + ML + MR, 256 + MT + MB
TX += ML - 16; TY += MT - 12
HOME = np.zeros((CH, CW, 4)); HOME[MT:MT + 256, ML:ML + 230] = HOME0[12:268, 16:246]
REST = place(REST_BIG, S, TX, TY, 3, CW, CH)


def rebase(c, thr=6, grow=2, feather=1.0):
    """where the placed clip frame equals the placed rest, the shipped home's own pixel"""
    dd = np.abs(c - REST).max(2)
    m = ndi.binary_dilation(ndi.binary_opening(dd > thr), iterations=grow)
    w = np.clip(ndi.gaussian_filter(m.astype(float), feather) * 1.5, 0, 1)[..., None]
    pa = c[..., 3:4] / 255 * w + HOME[..., 3:4] / 255 * (1 - w)
    rgb = (c[..., :3] * c[..., 3:4] / 255 * w + HOME[..., :3] * HOME[..., 3:4] / 255 * (1 - w)) / np.maximum(pa, 1e-3)
    return np.dstack([rgb, pa * 255])


out = sys.argv[1]; os.makedirs(out + '/frames', exist_ok=True)
frames, gs = [], []
for spec in sys.argv[2:]:
    d, _, sel = spec.partition(':')
    m = json.load(open(d + '/atlas.json')); A = Image.open(d + '/atlas.png'); W, H = m['cell']
    for g in m['gestures']:
        raw_ends = sel.endswith('!'); sel = sel.rstrip('!')   # '!': keep the clip's own ends (a chained half that ends on a drawn peak)
        sel0, _, ez = sel.partition('~'); es = int(ez.split(',')[0]) if ez else 0; ee = int(ez.split(',')[1]) if ez else 0
        name, rng = (sel0.partition('@')[0], sel0.partition('@')[2]) if sel0 else (g['name'], '')
        if sel and g['name'] != name: continue
        idx = list(range(g['frames']))
        if rng: a, b = map(int, rng.split('-')); idx = idx[a:b + 1]
        at = len(frames)
        for j, k in enumerate(idx):
            i = g['at'] + k
            f = A.crop(((i % m['cols']) * W, (i // m['cols']) * H, (i % m['cols'] + 1) * W, (i // m['cols'] + 1) * H))
            c = HOME.copy() if j in (0, len(idx) - 1) and not raw_ends else rebase(place(f, S, TX, TY, 3, CW, CH))
            # ~S,E: ease out of / into home over S frames at the start and E at the end (a cut that is not a full rest)
            w = min(1.0, j / es if es else 1.0, (len(idx) - 1 - j) / ee if ee else 1.0)
            if 0 < w < 1:
                pa = c[..., 3:4] / 255 * w + HOME[..., 3:4] / 255 * (1 - w)
                c = np.dstack([(c[..., :3] * c[..., 3:4] / 255 * w + HOME[..., :3] * HOME[..., 3:4] / 255 * (1 - w)) / np.maximum(pa, 1e-3), pa * 255])
            c = np.clip(np.round(c), 0, 255).astype(np.uint8); c[c[..., 3] < 6] = 0
            frames.append(c); Image.fromarray(c).save(f'{out}/frames/{name}_{j:02d}.png')
        gs.append({'name': name, 'at': at, 'frames': len(idx), 'src': g.get('src', d)})
cols = 8; nr = (len(frames) + cols - 1) // cols
atlas = Image.new('RGBA', (cols * CW, nr * CH))
for i, f in enumerate(frames): atlas.paste(Image.fromarray(f), ((i % cols) * CW, (i // cols) * CH))
atlas.save(out + '/atlas.png')
json.dump({'cell': [CW, CH], 'box': [ML, MT, 230, 256], 'cols': cols, 'rows': nr, 'fps': 12, 'gestures': gs}, open(out + '/atlas.json', 'w'), indent=1)
H0 = np.clip(np.round(HOME), 0, 255).astype(np.uint8)
for g in gs:
    st = Image.new('RGBA', (g['frames'] * CW, CH), (90, 90, 90, 255))
    best, bk = -1, 0
    for k in range(g['frames']):
        f = frames[g['at'] + k]; st.alpha_composite(Image.fromarray(f), (k * CW, 0))
        n = int((np.abs(f.astype(float) - H0).max(2) > 40).sum())
        if n > best: best, bk = n, k
    st.convert('RGB').save(f"{out}/strip-{g['name']}.png")
    feet = int((np.abs(frames[g['at'] + bk][-40:].astype(float) - H0[-40:]).max(2) > 40).sum())
    print(f"{g['name']}: {g['frames']} frames, peak {bk} changed px {best}, feet rows changed {feet}")
    g['peak'] = bk
json.dump({'cell': [CW, CH], 'box': [ML, MT, 230, 256], 'cols': cols, 'rows': nr, 'fps': 12, 'gestures': gs}, open(out + '/atlas.json', 'w'), indent=1)
