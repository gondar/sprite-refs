"""bbox.py LOCKDIR...: per gesture, the union bbox of every frame in the shipped cell's coordinates (cutout cell: box at 16,12)"""
import json, sys
import numpy as np
from PIL import Image
F = json.load(open(__file__.rsplit('/', 1)[0] + '/fit.json')); s, tx, ty = F['s'], F['tx'], F['ty']
for d in sys.argv[1:]:
    m = json.load(open(d + '/atlas.json')); A = np.asarray(Image.open(d + '/atlas.png'))[..., 3]; W, H = m['cell']
    for g in m['gestures']:
        x0 = y0 = 1e9; x1 = y1 = -1; per = []
        for k in range(g['frames']):
            i = g['at'] + k; a = A[(i // m['cols']) * H:(i // m['cols'] + 1) * H, (i % m['cols']) * W:(i % m['cols'] + 1) * W] > 40
            ys, xs = np.nonzero(a); x0 = min(x0, xs.min()); x1 = max(x1, xs.max()); y0 = min(y0, ys.min()); y1 = max(y1, ys.max())
            per.append(round(xs.max() * s + tx - 16))
        print(d, g['name'], 'box-relative x %.0f..%.0f y %.0f..%.0f' % (x0 * s + tx - 16, x1 * s + tx - 16, y0 * s + ty - 12, y1 * s + ty - 12), 'right edge per frame', per)
