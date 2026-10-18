#!/usr/bin/env python3
"""contacts.py NAME SHEET.png ENTRY.json OUTDIR [--paw] [--gaze]
Measure per-frame contact points on the packed cells (cell pixel coordinates):
  eye   : centre of the big dark iris (the largest dark filled blob in the head); blinks are interpolated
  nose  : the tip of the pink nose — of the pink blobs near the eye, the one furthest in FRONT (+x, she faces right),
          and of that blob the pixel furthest from the eye
  gaze  : unit vector eye -> nose tip (head direction), turned by the iris offset inside the eye white
  paw   : front paws — pink paw pixels away from the hind feet, the ear and the nose; their tip = mean of the pixels
          furthest along the reach direction (up-forward)
All tracks are median-filtered over 3 frames and checked for jumps (> 12 px frame to frame) which are printed.
Writes NAME.contacts.json and NAME_dots.jpg (every 2nd frame, dots drawn at 2x)."""
import sys, json, argparse, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('sheet'); ap.add_argument('entry'); ap.add_argument('out')
ap.add_argument('--paw', action='store_true'); ap.add_argument('--gaze', action='store_true')
ap.add_argument('--reach', default='0.45,-0.89', help='paw tip direction (unit-ish), cell coords')
a = ap.parse_args()
E = json.load(open(a.entry)); E = E[a.name] if a.name in E else E
cw, ch, cols, n = E['cw'], E['ch'], E['cols'], E['frames']
sheet = np.asarray(Image.open(a.sheet).convert('RGBA'), float)
cells = [sheet[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw] for i in range(n)]
ax_, ay_ = E['anchor']


def pinkmask(c):
    r, g, b, al = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    return (al > 200) & (r > 165) & (r - g > 45) & (r - g < 120) & (b > 0.72 * g) & (b < g + 10)


def eye_of(c):
    al = c[..., 3] > 230
    lum = c[..., :3] @ [0.3, 0.59, 0.11]
    dark = al & (lum < 85)
    dark = ndi.binary_opening(dark, iterations=2)
    lab, k = ndi.label(dark)
    if not k: return None, 0
    sz = ndi.sum(dark, lab, range(1, k + 1)); j = int(np.argmax(sz))
    if sz[j] < 25: return None, int(sz[j])
    cy, cx = ndi.center_of_mass(dark, lab, j + 1)
    return (cx, cy), int(sz[j])


eyes, sizes = [], []
for c in cells:
    e, s = eye_of(c); eyes.append(e); sizes.append(s)
# a blink: blob much smaller than the home iris -> treat as missing, interpolate
s0 = max(sizes[0], 1)
for i in range(n):
    if eyes[i] is None or sizes[i] < 0.45 * s0: eyes[i] = None
idx = [i for i in range(n) if eyes[i] is not None]
E_ = np.array([eyes[i] if eyes[i] is not None else (np.nan, np.nan) for i in range(n)], float)
for d in range(2):
    E_[:, d] = np.interp(range(n), idx, E_[idx, d])
blink = [i for i in range(n) if eyes[i] is None]

noses, irisoff = [], []
prevc = preve = None; D0 = None
R = 3.2 * math.sqrt(s0 / math.pi) * 2.2   # search radius ~ a few iris radii
for i, c in enumerate(cells):
    ex, ey = E_[i]
    pk = pinkmask(c)
    yy, xx = np.mgrid[0:ch, 0:cw]
    near = pk & ((xx - ex) ** 2 + (yy - ey) ** 2 < R * R)
    lab, k = ndi.label(ndi.binary_closing(near, iterations=1))
    best = None
    for j in range(1, k + 1):
        m = lab == j
        if m.sum() < 6: continue
        my, mx = ndi.center_of_mass(m)
        dd = math.hypot(mx - ex, my - ey)
        if prevc is None:                   # first frame (home, side view): the blob furthest in front of the eye
            if mx - ex < 0: continue        # behind the eye: the ear
            sc = (mx - ex)
        else:
            # the head is rigid in side view: the nose sits at the home eye-nose distance (+-30 %); a paw or an open
            # mouth near the face sits elsewhere. Among those, temporal tracking: nearest to where the nose was.
            if abs(dd - D0) > 0.3 * D0: continue
            px_, py_ = prevc[0] + ex - preve[0], prevc[1] + ey - preve[1]
            sc = -math.hypot(mx - px_, my - py_) / D0 - abs(dd - D0) / D0
            if math.hypot(mx - px_, my - py_) > 0.9 * R: continue
        if best is None or sc > best[0]: best = (sc, m, (mx, my))
    if best is not None and prevc is None: D0 = math.hypot(best[2][0] - ex, best[2][1] - ey)
    if best is not None: prevc, preve = best[2], (ex, ey)
    if best is None:
        noses.append((np.nan, np.nan)); continue
    m = best[1]
    # the tip: the outline pixel of the blob furthest from the eye, refined to the alpha edge just beyond it
    py, px = np.nonzero(m); d = (px - ex) ** 2 + (py - ey) ** 2; o = np.argsort(d)[-max(3, len(d) // 12):]
    tx, ty = px[o].mean(), py[o].mean()
    v = np.array([tx - ex, ty - ey]); v /= np.linalg.norm(v) + 1e-6
    for step in range(0, 12):      # walk out to the silhouette edge
        qx, qy = int(round(tx + v[0])), int(round(ty + v[1]))
        if not (0 <= qx < cw and 0 <= qy < ch) or c[qy, qx, 3] < 128: break
        tx, ty = tx + v[0], ty + v[1]
    noses.append((tx, ty))
N = np.array(noses, float)
ok = ~np.isnan(N[:, 0]); miss = [i for i in range(n) if not ok[i]]
for d in range(2): N[:, d] = np.interp(range(n), np.nonzero(ok)[0], N[ok, d])


def med3(A):
    B = A.copy()
    for i in range(1, len(A) - 1): B[i] = np.median(A[i - 1:i + 2], 0)
    return B


N = med3(N); E2 = med3(E_)
res = {'nose': [[round(float(x), 1), round(float(y), 1)] for x, y in N]}
info = {'eye': [[round(float(x), 1), round(float(y), 1)] for x, y in E2], 'blink_frames': blink, 'nose_missing': miss}
if a.gaze:
    G = N - E2; G /= np.linalg.norm(G, axis=1, keepdims=True)
    # the head points eye->nose; cartoon eyes also roll: the iris offset from the eye-white centre adds to it
    # (measured, not assumed: the white ring's centroid vs the iris centroid)
    gz = []
    for i, c in enumerate(cells):
        ex, ey = E2[i]; r0 = math.sqrt(s0 / math.pi)
        x0, x1, y0, y1 = int(ex - 3 * r0), int(ex + 3 * r0), int(ey - 3 * r0), int(ey + 3 * r0)
        sub = c[max(0, y0):y1, max(0, x0):x1]
        lum = sub[..., :3] @ [0.3, 0.59, 0.11]
        white = (sub[..., 3] > 200) & (lum > 205) & (sub[..., 2] > 190)
        lab, k = ndi.label(white)
        g = G[i].copy()
        if k:
            sz = ndi.sum(white, lab, range(1, k + 1))
            # the sclera ring = the biggest white blob (the highlight dot is small); iris sits off its centre
            j = int(np.argmax(sz))
            if sz[j] > 0.25 * s0:
                wy, wx = ndi.center_of_mass(white, lab, j + 1)
                off = np.array([ex - (max(0, x0) + wx), ey - (max(0, y0) + wy)])
                if np.linalg.norm(off) > 0.15 * r0: g = g + 0.6 * off / np.linalg.norm(off)
        g /= np.linalg.norm(g); gz.append(g)
    Gz = med3(np.array(gz))
    Gz /= np.linalg.norm(Gz, axis=1, keepdims=True)
    res['gaze'] = [[round(float(x), 3), round(float(y), 3)] for x, y in Gz]
if a.paw:
    u = np.array(list(map(float, a.reach.split(',')))); u /= np.linalg.norm(u)
    P = []
    for i, c in enumerate(cells):
        pk = pinkmask(c) | ((c[..., 3] > 200) & (c[..., 0] > 200) & (c[..., 0] - c[..., 1] > 30) & (c[..., 2] > 0.6 * c[..., 1]) & (c[..., 0] - c[..., 1] < 120))
        ex, ey = E2[i]; nx, ny = N[i]
        yy, xx = np.mgrid[0:ch, 0:cw]
        r0 = math.sqrt(s0 / math.pi)
        pk &= yy < ay_ - 0.10 * ch                    # not the hind feet
        pk &= ~(((xx - ex) ** 2 + (yy - ey) ** 2) < (4.2 * r0) ** 2)   # not the ear / nose / face
        pk &= ~(((xx - nx) ** 2 + (yy - ny) ** 2) < (2.0 * r0) ** 2)
        pk &= xx > ex - 3 * r0                          # front of the body (the tail is behind)
        pk = ndi.binary_opening(pk, iterations=1)
        lab, k = ndi.label(ndi.binary_dilation(pk, iterations=2))
        if k:
            sz = ndi.sum(pk, lab, range(1, k + 1)); keep = [j + 1 for j in range(k) if sz[j] >= 6]
            pk &= np.isin(lab, keep)
        py, px = np.nonzero(pk)
        if len(px) < 6: P.append((np.nan, np.nan)); continue
        pr = px * u[0] + py * u[1]; o = pr >= np.percentile(pr, 85)
        P.append((px[o].mean(), py[o].mean()))
    P = np.array(P, float); ok = ~np.isnan(P[:, 0])
    info['paw_missing'] = [i for i in range(n) if not ok[i]]
    for d in range(2): P[:, d] = np.interp(range(n), np.nonzero(ok)[0], P[ok, d])
    P = med3(P)
    res['paw'] = [[round(float(x), 1), round(float(y), 1)] for x, y in P]
for k_ in ('nose', 'paw'):
    if k_ in res:
        A = np.array(res[k_]); j = np.linalg.norm(np.diff(A, axis=0), axis=1)
        info[k_ + '_max_step'] = round(float(j.max()), 1); info[k_ + '_jumps'] = [int(i) for i in np.nonzero(j > 12)[0]]
json.dump({'contacts': res, 'info': info}, open(f'{a.out}/{a.name}.contacts.json', 'w'))
print(a.name, json.dumps(info)[:600])
# dots sheet: every 2nd frame at 2x? keep it readable: cells at 1x, 8 per row, dots big
pick = list(range(0, n, 2)) + ([n - 1] if (n - 1) % 2 else [])
per = 8; rows = math.ceil(len(pick) / per); sc = 1.0
im = Image.new('RGB', (cw * per, ch * rows), (236, 230, 214)); d = ImageDraw.Draw(im)
for k, i in enumerate(pick):
    ox, oy = (k % per) * cw, (k // per) * ch
    cc = Image.fromarray(cells[i].astype(np.uint8), 'RGBA'); im.paste(cc, (ox, oy), cc)
    d.text((ox + 4, oy + 3), str(i), fill=(60, 40, 30))
    x, y = res['nose'][i]; d.ellipse((ox + x - 4, oy + y - 4, ox + x + 4, oy + y + 4), fill=(255, 0, 160), outline=(0, 0, 0))
    ex, ey = E2[i]; d.ellipse((ox + ex - 2, oy + ey - 2, ox + ex + 2, oy + ey + 2), fill=(0, 200, 255))
    if 'gaze' in res:
        gx, gy = res['gaze'][i]; d.line((ox + x, oy + y, ox + x + gx * 60, oy + y + gy * 60), fill=(0, 140, 0), width=3)
        d.ellipse((ox + x + gx * 60 - 5, oy + y + gy * 60 - 5, ox + x + gx * 60 + 5, oy + y + gy * 60 + 5), fill=(255, 210, 0), outline=(0, 0, 0))
    if 'paw' in res:
        x, y = res['paw'][i]; d.ellipse((ox + x - 5, oy + y - 5, ox + x + 5, oy + y + 5), fill=(255, 210, 0), outline=(0, 0, 0))
    d.line((ox + ax_ - 5, oy + ay_, ox + ax_ + 5, oy + ay_), fill=(220, 0, 0)); d.line((ox + ax_, oy + ay_ - 5, ox + ax_, oy + ay_ + 5), fill=(220, 0, 0))
im.save(f'{a.out}/{a.name}_dots.jpg', quality=88)
