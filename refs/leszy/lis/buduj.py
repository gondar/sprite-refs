"""Lis-wędrowiec z wideo MiniMax-H3 → paski WebP + lis.json + lis.js (format jak dotąd, czyta go P.lis w las.js).

Uruchamiaj z katalogu lis-wideo (scratchpad). Klipy: raw/<job>.mp4 → frames/<job>/src/f_%03d.png (24 fps, od 1).
Kroki na klatkę: klucz (magenta: excess, albo 'border' przy dryfującym tle) → zostaje sylwetka + lampka (bez śmieci
i rys) → bez półprzezroczystej poświaty dalej niż 2,5 px od ciała → szybka lampki z różu na bursztyn →
kolor dopasowany do klatki wzorcowej (Lab, średnia/odchylenie, cała animacja jedną transformacją) →
jedna skala dla całej postaci (stojący lis = WYS px; zoom klipu zmierzony z głowy, skala.py) →
„fixed” kotwica: jedna linia stóp na animację, oś x = środek tułowia; w pętlach usunięty liniowy dryf.
"""
import json, os, sys, base64, io, glob
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, '/home/user/MathGames/.claude/skills/sprite-pipeline/scripts'); import key

OUT = sys.argv[1] if len(sys.argv) > 1 else 'wynik'
WYS = 372            # stojący lis w px paska (jak dotąd ~370–375)
STOJACY_SRC = 505    # stojący lis w px klipu przy skali głowy 1,0 (klip A, 0,5 s)
A, B, C = '20261014-213834-e96c85', '20261014-214508-ff4073', '20261014-215541-028eda'
REF = (A, 14)        # klatka wzorcowa koloru (stoi, profil)

# nazwa: klip, klatki (indeksy 24 fps od 0), fps, tryb, skala głowy, klucz, dodatkowe pola
def R(t0, t1, step=1): return list(range(round(t0 * 24), round(t1 * 24), step))
ANIM = {
 'stoi':            dict(job=C, fr=R(0.10, 0.60), fps=12, tryb='pingpong', s=1.01, key='adapt'),
 'chod':            dict(job=C, fr=R(0.833, 1.958), fps=24, tryb='petla', s=1.05, key='adapt', xfade=5),
 'bieg':            dict(job=A, fr=R(2.083, 2.833), fps=24, tryb='petla', s=1.06, key='auto'),
 'obejrzenie-sie':  dict(job=B, fr=R(0.10, 1.10), fps=24, tryb='raz', s=1.03, key='auto'),
 'podnosi-lampke':  dict(job=B, fr=R(1.00, 1.60), fps=24, tryb='raz', s=1.05, key='auto'),
 'pisze-pazurem':   dict(job=B, fr=R(2.25, 3.10), fps=24, tryb='raz', s=1.113, key='auto'),
 'kucniecie':       dict(job=B, fr=R(3.10, 3.75), fps=24, tryb='raz', s=1.092, key='auto'),
 'kucniecie-oddech':dict(job=B, fr=R(3.75, 4.45), fps=12, tryb='pingpong', s=1.092, key='auto'),
}
for k, v in json.load(open('narz/wybor.json')).items() if os.path.exists('narz/wybor.json') else []:
    ANIM.setdefault(k, {}).update(v)


def src(job, i): return f'frames/{job}/src/f_{i + 1:03d}.png'


def warm(rgb):
    R_, G_, B_ = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    return (R_ > 200) & (G_ > 120) & (B_ < 170) & (R_ - B_ > 70)


def wytnij(path, k):
    a = np.array(Image.open(path).convert('RGB')).astype(np.float64)
    if k == 'border': r, _ = key.key_image(a, 'border', 40, 110)
    elif k == 'adapt':   # magenta blednie w klipie: progi z nadmiaru magenty na brzegu tej klatki
        b = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
        E = float(np.median(key.excess(b, 'magenta'))); hi = min(120, 0.72 * E); lo = max(12, hi - 75)
        r, _ = key.key_image(a, 'magenta', lo, hi)
    else: r, _ = key.key_image(a, 'magenta', 40, 120)
    al = r[..., 3]
    # szybka lampki prześwituje tłem → róż/fiolet; zamień na bursztyn (tylko piksele z wyraźnym nadmiarem magenty)
    rgb = r[..., :3]
    ex = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]
    pink = (ex > 25) & (rgb[..., 0] > 150) & (al > 60)
    lum = np.clip(rgb[..., 0] / 255, 0, 1)
    rgb[pink] = np.stack([255 * lum, 175 * lum, 70 * lum], -1)[pink]
    # składowe: największa + te ze świecącą szybką (lampka na kółku bywa oddzielona); rysy pazura i plamki — precz
    lab, n = ndi.label(ndi.binary_dilation(al > 40, iterations=2))
    if n > 1:
        size = ndi.sum(np.ones_like(lab), lab, range(1, n + 1)); big = 1 + int(np.argmax(size))
        wm = warm(rgb) & (al > 150)
        keep = [big] + [j + 1 for j in range(n) if j + 1 != big and wm[lab == j + 1].sum() > 25]
        al = np.where(np.isin(lab, keep), al, 0)
    # poświata: półprzezroczyste dalej niż 2,5 px od nieprzezroczystego
    d = ndi.distance_transform_edt(al < 200)
    al = np.where(d > 2.5, 0, al)
    return np.dstack([np.clip(rgb, 0, 255), al]).astype(np.float32)


def lab_stats(frames):
    px = np.concatenate([cv2.cvtColor(np.ascontiguousarray(f[..., :3].astype(np.uint8)), cv2.COLOR_RGB2LAB)[f[..., 3] > 230] for f in frames])
    return px.mean(0), px.std(0)


def kolor(frames, ref):
    m, s = lab_stats(frames); rm, rs = ref
    out = []
    for f in frames:
        lab = cv2.cvtColor(np.ascontiguousarray(f[..., :3].astype(np.uint8)), cv2.COLOR_RGB2LAB).astype(np.float32)
        lab = (lab - m) * (rs / np.maximum(s, 1)) + rm
        rgb = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
        out.append(np.dstack([rgb, f[..., 3]]))
    return out


def tulow_x(al):
    ys, xs = np.nonzero(al > 128); top, bot = ys.min(), ys.max(); h = bot - top
    sel = (ys > top + 0.25 * h) & (ys < top + 0.55 * h)
    return xs[sel].mean()


def lampka(cell):
    """środek świecącej szyby: ciepłe jasne piksele w ciemnej oprawie (≥ 30 % ciemnego obrzeża).
    Futro na pysku też bywa ciepłe i jasne, ale wokół niego jest futro, nie oprawa (≤ 27 % ciemnego)."""
    c = cell.astype(int); R, G, B, Al = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    m = (R > 195) & (G > 120) & (B < 170) & (R - B > 70) & (Al > 200)
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(ndi.binary_dilation(m, iterations=2))
    ok = []
    for j in range(1, n + 1):
        comp = m & (lab == j)
        if comp.sum() < 15: continue
        ring = ndi.binary_dilation(comp, iterations=3) & ~ndi.binary_dilation(comp, iterations=1)
        op = Al[ring] > 100
        if not op.any(): continue
        if ((R + G + B)[ring][op] / 3 < 70).mean() >= 0.3: ok.append(comp)
    if not ok: return None
    big = max(ok, key=lambda q: q.sum()); by, bx = [v.mean() for v in np.nonzero(big)]
    sel = [q for q in ok if np.hypot(*(np.array([v.mean() for v in np.nonzero(q)]) - [by, bx])) < 25]
    ys, xs = np.nonzero(np.any(sel, 0))
    return [round(float(xs.mean()), 1), round(float(ys.mean()), 1)]


def wypelnij(l, petla):
    """brakujące położenia lampki (za ciałem) — interpolacja między sąsiednimi klatkami (w pętli cyklicznie)"""
    n = len(l); idx = [i for i in range(n) if l[i]]
    if not idx: return l
    out = []
    for i in range(n):
        if l[i]: out.append(l[i]); continue
        prv = [j for j in idx if j < i]; nxt = [j for j in idx if j > i]
        if petla:
            p = prv[-1] if prv else idx[-1] - n; q = nxt[0] if nxt else idx[0] + n
        else:
            p = prv[-1] if prv else nxt[0]; q = nxt[0] if nxt else prv[-1]
        P, Q = l[p % n], l[q % n]; u = 0 if q == p else (i - p) / (q - p)
        out.append([round(P[0] + (Q[0] - P[0]) * u, 1), round(P[1] + (Q[1] - P[1]) * u, 1)])
    return out


ref_f = wytnij(src(*REF), 'auto'); REFST = lab_stats([ref_f])
os.makedirs(OUT, exist_ok=True)
wyn = {}
for name, a in ANIM.items():
    fr = [wytnij(src(a['job'], i), a['key']) for i in a['fr']]
    if a.get('xfade'):   # pętla bez skoku: pierwsze m klatek przenika się z m klatkami, które w klipie idą PO końcu pętli
        m = a['xfade']; ext = [wytnij(src(a['job'], a['fr'][-1] + 1 + i), a['key']) for i in range(m)]
        for i in range(m):
            w = (i + 1) / (m + 1)
            d = tulow_x(fr[i][..., 3]) - tulow_x(ext[i][..., 3])
            ys_e = np.nonzero(ext[i][..., 3] > 128)[0]; ys_f = np.nonzero(fr[i][..., 3] > 128)[0]
            ext[i] = cv2.warpAffine(ext[i], np.float32([[1, 0, d], [0, 1, ys_f.min() - ys_e.min()]]), ext[i].shape[1::-1],
                                    flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            pa, pb = ext[i].copy(), fr[i].copy()
            pa[..., :3] *= pa[..., 3:4] / 255; pb[..., :3] *= pb[..., 3:4] / 255
            q = pa * (1 - w) + pb * w; al_ = np.maximum(q[..., 3:4], 1e-3)
            q[..., :3] = np.where(q[..., 3:4] > 0.5, q[..., :3] * 255 / al_, 0); fr[i] = q
    fr = kolor(fr, REFST)
    sk = WYS / STOJACY_SRC / a['s']
    bots = np.array([np.nonzero(f[..., 3] > 128)[0].max() for f in fr])
    ground = float(np.percentile(bots, 90)) if a['tryb'] == 'petla' else float(np.median(bots))
    tx = np.array([tulow_x(f[..., 3]) for f in fr])
    dx = np.zeros(len(fr))
    if a['tryb'] == 'petla' and len(fr) > 2:   # liniowy dryf: klatka n byłaby z powrotem klatką 0
        n = len(fr); slope = (tx[-1] - tx[0] + (tx[-1] - tx[-2])) / n
        dx = -slope * np.arange(n); dx -= dx.mean()
    px = float(np.median(tx + dx)) if a['tryb'] != 'raz' else float(tx[0])
    # wspólne okno
    al = np.zeros(fr[0].shape[:2], bool)
    sh = []
    dy = (ground - bots) if a['tryb'] != 'petla' else np.zeros(len(fr))   # stoi / akcje w miejscu: stopy zawsze na linii
    for f, d, e_ in zip(fr, dx, dy):
        m = np.float32([[1, 0, d], [0, 1, e_]])
        g = cv2.warpAffine(f, m, (f.shape[1], f.shape[0]), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        sh.append(g); al |= g[..., 3] > 20
    ys, xs = np.nonzero(al)
    x0, x1, y0 = xs.min() - 3, xs.max() + 4, ys.min() - 3
    y1 = int(ground) + 3
    cw, ch = round((x1 - x0) * sk), round((y1 - y0) * sk)
    cells = []
    for g in sh:
        c = g[y0:y1, x0:x1]
        pm = c.copy(); pm[..., :3] *= pm[..., 3:4] / 255   # skalowanie na premultiplied (bez ciemnych obwódek)
        pm = cv2.resize(pm, (cw, ch), interpolation=cv2.INTER_AREA)
        a_ = np.maximum(pm[..., 3:4], 1e-3); pm[..., :3] = np.where(pm[..., 3:4] > 0.5, pm[..., :3] * 255 / a_, 0)
        cells.append(np.clip(pm, 0, 255).astype(np.uint8))
    order = list(range(len(cells)))
    if a['tryb'] == 'pingpong': order = order + order[-2:0:-1]
    cells = [cells[i] for i in order]
    strip = np.concatenate(cells, 1)
    Image.fromarray(strip).save(f'{OUT}/{name}.png')
    lam = wypelnij([lampka(c) for c in cells], a['tryb'] != 'raz')
    pivot = [round((px - x0) * sk, 1), round((ground - y0) * sk, 1)]
    wyn[name] = dict(klatki=len(cells), fps=a['fps'], w=cw, h=ch, pivot=pivot, petla=a['tryb'] != 'raz', lampka=lam,
                     zrodlo=f"{a['job']} {a['fr'][0] / 24:.2f}–{(a['fr'][-1] + 1) / 24:.2f} s")
    print(f"{name:17s} {len(cells):3d} kl. {a['fps']} fps  {cw}×{ch}  pivot {pivot}  lampka {sum(1 for c in cells if lampka(c))}/{len(cells)}")
json.dump(wyn, open(f'{OUT}/wynik.json', 'w'), ensure_ascii=False, indent=1)
