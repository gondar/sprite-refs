#!/usr/bin/env python3
"""Leszy: klucz z luminancji (ciemna postać na białym tle H3). src/f_*.png -> key/f_*.png (RGBA) + krzywa ruchu."""
import sys, glob, os, numpy as np
from PIL import Image
src = sys.argv[1]; out = os.path.join(os.path.dirname(src.rstrip('/')), 'key'); os.makedirs(out, exist_ok=True)
fs = sorted(glob.glob(os.path.join(src, 'f_*.png')))
small = []
for f in fs:
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
    b = np.concatenate([a[:6].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
    bg = np.median(b, 0); Lbg = bg.mean()
    L = a.mean(2)
    al = np.clip((Lbg - L - 8) / (Lbg - 18), 0, 1)
    al = al ** 0.9
    u = np.clip(L / 255, 0, 1)   # jasność w ciele (tekstura): ciemny granat jak pozy z img/
    rgb = np.stack([6 + 22 * u, 9 + 22 * u, 13 + 26 * u], 2)
    rgba = np.dstack([rgb, al * 255]).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(rgba).save(os.path.join(out, os.path.basename(f)))
    small.append(np.asarray(Image.fromarray((al * 255).astype(np.uint8)).resize((64, 112)), dtype=float))
step = 4
print('ruch/(1/6 s):', ' '.join(f'{i*step/24:.2f}:{np.abs(small[i+step]-small[i]).mean():.1f}' for i in range(0, len(small) - step, step)))
