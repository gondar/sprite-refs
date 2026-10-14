#!/usr/bin/env python3
"""Śledzenie głowy (oka) po kanale alfa: szablon z poprzedniej klatki, NCC w oknie ±R. -> oczy.json {klatka: [x, y]}"""
import sys, glob, json, numpy as np
from PIL import Image
from numpy.lib.stride_tricks import sliding_window_view as sw
d, x0, y0, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
fs = sorted(glob.glob(d + '/f_*.png'))
def A(f): a = np.asarray(Image.open(f))[..., 3].astype(np.float32) / 255; return a[::2, ::2]
P, R = 36, 14     # pół szablonu, promień szukania (w px po zmniejszeniu ×2)
x, y = x0 / 2, y0 / 2
prev = A(fs[0]); first = None; res = {}
for i, f in enumerate(fs):
    a = A(f)
    if i == 0: pos = (x, y)
    else:
        xi, yi = int(round(x)), int(round(y))
        tpl = prev[yi - P:yi + P, xi - P:xi + P]
        tpl = 0.7 * tpl + 0.3 * first
        win = np.pad(a, P + R, mode='constant')[yi - R:yi + R + 2 * P + P + R, xi - R:xi + R + 2 * P + P + R]
        win = np.pad(a, P + R + 2)[yi + 2 - R:yi + 2 + R + 2 * P + 2 * R, xi + 2 - R:xi + 2 + R + 2 * P + 2 * R]
        sub = np.pad(a, 200)[yi + 200 - R - P:yi + 200 + R + P, xi + 200 - R - P:xi + 200 + R + P]
        V = sw(sub, (2 * P, 2 * P))
        t = (tpl - tpl.mean()); tn = np.sqrt((t * t).sum()) + 1e-6
        Vm = V - V.mean(axis=(2, 3), keepdims=True)
        s = (Vm * t).sum(axis=(2, 3)) / (np.sqrt((Vm * Vm).sum(axis=(2, 3))) * tn + 1e-6)
        dy, dx = np.unravel_index(np.argmax(s), s.shape)
        x, y = xi - R + dx, yi - R + dy
    if first is None: xi, yi = int(round(x)), int(round(y)); first = a[yi - P:yi + P, xi - P:xi + P].copy()
    res[i + 1] = [float(x * 2), float(y * 2)]; prev = a
json.dump(res, open(out, 'w'))
print(' '.join(f'{k}:{int(v[0])},{int(v[1])}' for k, v in list(res.items())[::8]))
