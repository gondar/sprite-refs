#!/usr/bin/env python3
"""Leszy z wideo H3 -> paski WebP + leszy-anim.json + leszy-anim.js (Teledysk.LESZY_ANIM).
Klatki z key/ (klucz z luminancji), jedna skala dla wszystkich, kamera stała -> zaczep stały na klip (stopy w 1. klatce),
oczy z śledzenia głowy (sledz.py), krawędzie kadru H3 wygaszone w mgłę."""
import json, os, sys, glob, base64, io, numpy as np
from PIL import Image
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
Q = int(os.environ.get('Q', 72)); STEP = 2; FPS = 24 / STEP
H_OUT = float(os.environ.get('HOUT', 400))
KL = {'c1': '20261014-214756-cfbeb8', 'c2': '20261014-214757-535e4f'}
def sm(a, b, x): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def front_c2(i): return sm(22, 31, i) * (1 - sm(47, 56, i))
# nazwa: (klip, od, do (włącznie), pętla, uwaga)
SEG = {
    'stoi':   ('c1', 1, 22, True, 'stoi z profilu, oddycha (pętla)'),
    'kroczy': ('c1', 20, 60, True, 'ciężki krok w miejscu (pętla: jeden pełny cykl)'),
    'siega':  ('c1', 58, 82, False, 'unosi ramię i sięga daleko przed siebie, szpony; ostatnią klatkę trzymać'),
    'cofa':   ('c1', 82, 107, False, 'cofa się, zasłania głowę przedramieniem'),
    'glowa':  ('c2', 20, 58, False, 'odwraca głowę do widza (oczy przodem) i z powrotem'),
    'szuka':  ('c2', 56, 84, False, 'pochyla się nisko, głowa wysunięta — szuka'),
    'kuca':   ('c2', 82, 107, False, 'kuca, dłoń na ziemi, węszy trop; ostatnią klatkę trzymać'),
}
cache = {}
def frame(c, i):
    k = (c, i)
    if k not in cache:
        a = np.asarray(Image.open(f'{W}/frames/{KL[c]}/key/f_{i:03d}.png')).astype(np.float32)
        h, w = a.shape[:2]; f = np.ones((h, w), np.float32)
        e = 36; r = np.linspace(0, 1, e)
        f[:e] *= r[:, None]; f[:, -e:] *= r[::-1][None]; f[:, :e] *= r[None]
        a[..., 3] *= f; cache[k] = a
    return cache[k]
oczy = {c: json.load(open(f'{W}/frames/{c}-oczy.json')) for c in KL}
# linia stóp i wysokość stojącego: klip c1, klatka 1
def stopy(c):
    al = frame(c, 1)[..., 3] / 255; rows = np.nonzero((al > 0.9).sum(1) >= 4)[0]; return rows.max()
BASE = {c: stopy(c) for c in KL}
al1 = frame('c1', 1)[..., 3]; top1 = np.nonzero((al1 > 100).sum(1) >= 1)[0].min()
H_STAND = BASE['c1'] - top1; S = H_OUT / H_STAND
print('stopy', BASE, 'wysokość stojącego', H_STAND, 'skala', round(S, 4))
def stopa_x(c, i):
    al = frame(c, i)[..., 3] / 255; b = BASE[c]; band = al[b - 40:b + 1] > 0.6
    xs = np.nonzero(band.any(0))[0]; return (xs.min() + xs.max()) / 2
def thumb(c, i):
    a = frame(c, i); return np.asarray(Image.fromarray(a[..., 3].astype(np.uint8)).resize((48, 84)), dtype=float)
def petla(c, a, b, minlen):
    best = None
    for i in range(a, b + 1):
        for j in range(i + minlen, b + 1):
            d = np.abs(thumb(c, i) - thumb(c, j)).mean()
            if best is None or d < best[0]: best = (d, i, j)
    return best
meta = {'version': 1, 'opis': 'Leszy z wideo MiniMax-H3 (manekin dorosłych proporcji). Paski poziome (klatka i: x = i*w). '
        'pivot = [x stóp, linia stóp] w komórce (dół komórki = stopy); oczy = [x, y] środka między oczami w komórce na klatkę; '
        'rozstaw = odstęp oczu [px]; profil 0…1 (1 = z boku, dalsze oko ciemniejsze); skala = wys. komórki / wys. stojącego.',
        'wysStojacego': round(H_OUT), 'fps': FPS, 'animacje': {}}
js = {}
for name, (c, a, b, loop, uw) in SEG.items():
    drift = 0
    if name == 'kroczy':   # pół cyklu (jeden krok; w sylwetce nogi są nierozróżnialne), dryf ciała do przodu odjęty
        i0, j0, drift = 21, 51, 52.0
        idx = list(range(i0, j0, STEP)); print(name, 'krok', i0, j0, 'dryf', drift)
    elif loop:
        minlen = 14 if name == 'stoi' else 20
        d, i0, j0 = petla(c, a, b, minlen)
        idx = list(range(i0, j0, STEP)); print(name, 'pętla', i0, j0, 'szew', round(d, 2))
    else: idx = list(range(a, b + 1, STEP))
    def przes(f, dx):
        if not dx: return f
        o = np.zeros_like(f); d = int(round(dx))
        if d > 0: o[:, :-d] = f[:, d:]
        else: o[:, -d:] = f[:, :d]
        return o
    sh = {i: drift * (i - idx[0]) / (j0 - idx[0]) if drift else 0 for i in idx}
    fr = [przes(frame(c, i), sh[i]) for i in idx]
    if name == 'kroczy':   # szew pętli: ostatnie K klatek przenikają w poprzedniczki pierwszej klatki (koniec wpływa w początek)
        K = 3; n = len(fr)
        for m in range(K):
            al = (m + 1) / (K + 1); src_i = idx[0] - (K - m) * STEP
            pre = frame(c, src_i); A0, B0 = fr[n - K + m], pre
            pa = A0[..., 3:4] / 255; pb = B0[..., 3:4] / 255; aa = (1 - al) * pa + al * pb
            rgb = ((1 - al) * A0[..., :3] * pa + al * B0[..., :3] * pb) / np.maximum(aa, 1e-4)
            fr[n - K + m] = np.dstack([rgb, aa * 255]).astype(np.float32)
    al = np.max([f[..., 3] for f in fr], 0)
    ys, xs = np.nonzero(al > 8)
    x0, x1, y0 = xs.min() - 6, xs.max() + 6, max(0, ys.min() - 6); y1 = BASE[c] + 1
    px = stopa_x(c, idx[0])
    w = int(round((x1 - x0) * S)); h = int(round((y1 - y0) * S))
    cells = []; oc = []; rz = []; pr = []
    for i, f in zip(idx, fr):
        im = Image.fromarray(f.round().clip(0, 255).astype(np.uint8)).crop((x0, y0, x1, y1)).resize((w, h), Image.LANCZOS)
        cells.append(im)
        ex, ey = oczy[c][str(i)]; ex -= round(sh[i])
        fr_ = front_c2(i) if name == 'glowa' else 0.0
        oc.append([round((ex - x0) * S, 1), round((ey - y0) * S, 1)])
        rz.append(round(H_OUT * (0.011 + 0.021 * fr_), 1)); pr.append(round(1 - fr_, 2))
    strip = Image.new('RGBA', (w * len(cells), h))
    for k, im in enumerate(cells): strip.paste(im, (k * w, 0))
    buf = io.BytesIO(); strip.save(buf, 'WEBP', quality=Q, alpha_quality=int(os.environ.get("AQ", 80)), method=6)
    open(f'{OUT}/{name}.webp', 'wb').write(buf.getvalue())
    m = {'plik': name + '.webp', 'klatki': len(cells), 'fps': FPS, 'w': w, 'h': h, 'pivot': [round((px - x0) * S, 1), h],
         'petla': loop, **({'kroki': 1} if name == 'kroczy' else {}), 'skala': round(h / H_OUT, 4), 'oczy': oc, 'rozstaw': rz, 'profil': pr, 'uwaga': uw,
         'zrodlo': f'{KL[c]} klatki {idx[0]}–{idx[-1]} (24 fps, co {STEP})'}
    meta['animacje'][name] = m
    js[name] = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()
    print(f'{name}: {len(cells)} kl. {w}x{h} {len(buf.getvalue())//1024} KB')
json.dump(meta, open(f'{OUT}/leszy-anim.json', 'w'), ensure_ascii=False, indent=1)
full = dict(meta); full['obrazki'] = js
with open(f'{OUT}/leszy-anim.js', 'w') as f:
    f.write('/* Leszy — animacje z wideo MiniMax-H3 (paski WebP z alfą jako data URI). Generowane przez zbuduj.py (gondar/sprite-refs: refs/leszy/leszy/narzedzia/); nie edytować ręcznie. */\n')
    f.write('(function(){var T=window.Teledysk=window.Teledysk||{};T.LESZY_ANIM=' + json.dumps(full, ensure_ascii=False, separators=(',', ':')) + ';})();\n')
print('leszy-anim.js', os.path.getsize(f'{OUT}/leszy-anim.js') // 1024, 'KB')
