#!/usr/bin/env python3
"""contacts2.py NAME SHEET.png ENTRY.json OUTDIR [--paw] [--gaze]
Per-frame contact points on the packed cells, in cell pixel coordinates (x right, y down, origin top-left of a cell).

Head tracker (eye + nose):
  frame 0 (home, side view facing right): eye = the big dark iris blob, nose = the pink blob furthest in front of
  the eye, its tip = the blob pixel furthest from the eye pushed out to the silhouette edge.
  every next frame: the head patch of the previous frame (a disc round eye+nose) is matched into this frame over
  translation AND rotation (cv2.matchTemplate, masked, +-30 deg in 3 deg steps) -> predicted eye and nose; then
  snapped: the iris blob near the predicted eye (when the eye is open), the pink blob near the predicted nose (tip
  along the eye->nose direction). Closed eyes, an open mouth or a paw at the face do not break it.
gaze = unit vector eye -> nose tip (the head's direction) turned by the iris offset in the eye white (where she looks).
paw  = the leading front-paw tip: forelimb pixels are the thin protrusions of the silhouette (alpha minus its opening
  by a disc), in front of the body core, away from the head, feet and tail; the tip = the protrusion pixel furthest
  from the body core.
Tracks are median-filtered over 3 frames; frame-to-frame steps above 14 px are listed for review.
Writes NAME.contacts.json and NAME_dots.jpg (every 2nd frame + the last, dots drawn on the cells)."""
import json, argparse, math
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('sheet'); ap.add_argument('entry'); ap.add_argument('out')
ap.add_argument('--paw', action='store_true'); ap.add_argument('--gaze', action='store_true'); ap.add_argument('--every', type=int, default=2)
a = ap.parse_args()
E = json.load(open(a.entry)); E = E.get(a.name, E)
cw, ch, cols, n = E['cw'], E['ch'], E['cols'], E['frames']
sheet = np.asarray(Image.open(a.sheet).convert('RGBA'), np.float32)
cells = [sheet[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw] for i in range(n)]
ax_, ay_ = E['anchor']
YY, XX = np.mgrid[0:ch, 0:cw]


def pinkmask(c):
    r, g, b, al = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    return (al > 200) & (r > 165) & (r - g > 45) & (r - g < 120) & (b > 0.72 * g) & (b < g + 10)


def irises(c):
    lum = c[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32)
    dark = ndi.binary_opening((c[..., 3] > 230) & (lum < 85), iterations=2)
    lab, k = ndi.label(dark)
    out = []
    for j in range(1, k + 1):
        m = lab == j; s = int(m.sum())
        if s >= 20: cy, cx = ndi.center_of_mass(m); out.append((cx, cy, s))
    return out


def pinkblobs(c):
    lab, k = ndi.label(ndi.binary_closing(pinkmask(c), iterations=1))
    out = []
    for j in range(1, k + 1):
        m = lab == j
        if m.sum() >= 5: cy, cx = ndi.center_of_mass(m); out.append((cx, cy, m))
    return out


def tip_of(m, ex, ey, v, c):
    py, px = np.nonzero(m); pr = (px - ex) * v[0] + (py - ey) * v[1]
    o = pr >= np.percentile(pr, 90); tx, ty = px[o].mean(), py[o].mean()
    for _ in range(10):
        qx, qy = int(round(tx + v[0])), int(round(ty + v[1]))
        if not (0 <= qx < cw and 0 <= qy < ch) or c[qy, qx, 3] < 128: break
        tx, ty = tx + v[0], ty + v[1]
    return tx, ty


def pm(c):  # premultiplied RGB on a neutral ground, for matching
    al = c[..., 3:4] / 255
    return (c[..., :3] * al + 128 * (1 - al)).astype(np.float32)


# ---- frame 0
c0 = cells[0]
ir = max(irises(c0), key=lambda t: t[2]); ex, ey, S0 = ir
cand = [b for b in pinkblobs(c0) if b[0] > ex and math.hypot(b[0] - ex, b[1] - ey) < 6 * math.sqrt(S0)]
nb = max(cand, key=lambda b: b[0] - ex)
v = np.array([nb[0] - ex, nb[1] - ey]); v /= np.linalg.norm(v)
nx, ny = tip_of(nb[2], ex, ey, v, c0)
D0 = math.hypot(nx - ex, ny - ey); r0 = math.sqrt(S0 / math.pi)
eyes, noses, closed, snapped = [(ex, ey)], [(nx, ny)], [], []
lastopen = 0
ex0, ey0, nx0, ny0 = ex, ey, nx, ny; NOSE0 = int(nb[2].sum())
eb = max([b for b in pinkblobs(c0) if b[0] < ex], key=lambda b: b[2].sum()); ear0 = (eb[0], eb[1]); EAR0 = int(eb[2].sum())
DE0 = math.hypot(ear0[0] - ex, ear0[1] - ey); lastear = ear0; lastang = 0.0
for i in range(1, n):
    cc = cells[i]; pex, pey = eyes[-1]; pnx, pny = noses[-1]
    # whole-body motion since the last frame (a pounce moves ~80 px in one frame): the shift of the front half's
    # alpha centroid; the eye and nose searches start from the last positions moved by it
    def front(c):
        al = c[..., 3] > 128; cx0 = XX[al].mean(); m = al & (XX > cx0); return XX[m].mean(), YY[m].mean()
    f1, f0 = front(cc), front(cells[i - 1]); gdx, gdy = f1[0] - f0[0], f1[1] - f0[1]
    pex, pey, pnx, pny = pex + gdx, pey + gdy, pnx + gdx, pny + gdy
    if lastear is not None: lastear = (lastear[0] + gdx, lastear[1] + gdy)
    # eye: the open iris nearest the predicted eye
    iris = [b for b in irises(cc) if math.hypot(b[0] - pex, b[1] - pey) < 0.6 * D0 and b[2] > 0.45 * S0]
    if iris:
        b = min(iris, key=lambda b: math.hypot(b[0] - pex, b[1] - pey)); qex, qey = b[0], b[1]; lastopen = i
    else:
        # closed or squeezed eye: match the eye region (brow, cheek, lid) of the last open frame, translation only
        closed.append(i); lc = cells[lastopen]; lex, ley = eyes[lastopen]; rr = int(2.6 * r0); SR = 45
        A = cv2.copyMakeBorder(pm(lc), 200, 200, 200, 200, cv2.BORDER_CONSTANT, value=(128, 128, 128))
        Aa = cv2.copyMakeBorder(lc[..., 3], 200, 200, 200, 200, cv2.BORDER_CONSTANT, value=0)
        B = cv2.copyMakeBorder(pm(cc), 200, 200, 200, 200, cv2.BORDER_CONSTANT, value=(128, 128, 128))
        tx0, ty0 = int(lex) + 200 - rr, int(ley) + 200 - rr
        T = A[ty0:ty0 + 2 * rr, tx0:tx0 + 2 * rr]; Tm = (Aa[ty0:ty0 + 2 * rr, tx0:tx0 + 2 * rr] > 128).astype(np.float32)
        wx0, wy0 = int(pex) + 200 - rr - SR, int(pey) + 200 - rr - SR
        W = B[wy0:wy0 + 2 * rr + 2 * SR, wx0:wx0 + 2 * rr + 2 * SR]
        res_ = cv2.matchTemplate(W, T, cv2.TM_SQDIFF, mask=np.repeat(Tm[..., None], 3, 2))
        _, _, loc, _ = cv2.minMaxLoc(res_)
        qex, qey = wx0 + loc[0] + rr - 200 + (lex - int(lex)), wy0 + loc[1] + rr - 200 + (ley - int(ley))
    # nose: the head is rigid — the home eye->ear->nose geometry, placed by this frame's eye and inner-ear blob,
    # predicts the nose; a nose-sized pink blob near the prediction gives the exact tip. A paw on the nose makes the
    # blob too big (merged) -> the prediction stands.
    pbs = pinkblobs(cc)
    ears = [b for b in pbs if b[2].sum() > 0.5 * EAR0 and math.hypot(b[0] - qex, b[1] - qey) < 1.6 * DE0 and math.hypot(b[0] - qex, b[1] - qey) > 0.6 * DE0]
    if ears and lastear is not None:
        b = min(ears, key=lambda b: math.hypot(b[0] - lastear[0] - (qex - pex), b[1] - lastear[1] - (qey - pey)))
        ang = math.atan2(b[1] - qey, b[0] - qex) - math.atan2(ear0[1] - ey0, ear0[0] - ex0)
        lastear = (b[0], b[1])
    else:
        ang = lastang; lastear = (lastear[0] + qex - pex, lastear[1] + qey - pey)
    lastang = ang
    vx, vy = nx0 - ex0, ny0 - ey0
    px_, py_ = qex + vx * math.cos(ang) - vy * math.sin(ang), qey + vx * math.sin(ang) + vy * math.cos(ang)
    cand = [b for b in pbs if 0.45 * NOSE0 < b[2].sum() < 1.7 * NOSE0 and math.hypot(b[0] - px_, b[1] - py_) < 0.4 * D0]
    if cand:
        b = min(cand, key=lambda b: math.hypot(b[0] - px_, b[1] - py_))
        v = np.array([px_ - qex, py_ - qey]); v /= np.linalg.norm(v) + 1e-6
        qnx, qny = tip_of(b[2], qex, qey, v, cc); snapped.append(i)
    else:
        qnx, qny = px_, py_
    eyes.append((qex, qey)); noses.append((qnx, qny))


def med3(A):
    B = A.copy()
    for i in range(1, len(A) - 1): B[i] = np.median(A[i - 1:i + 2], 0)
    return B


EY = np.array(eyes); NO = np.array(noses)   # no smoothing: a median over fast frames puts points off the body
res = {'nose': [[round(float(x), 1), round(float(y), 1)] for x, y in NO]}
info = {'eye_closed_frames': closed, 'nose_unsnapped': [i for i in range(1, n) if i not in snapped]}
if a.gaze:
    # gaze angle = head angle + iris roll, both RELATIVE TO HOME, where she looks straight ahead (+x): in side view the
    # eye->nose line itself points ~15 deg down, and the iris sits off the eye-white centre even at rest.
    def iris_off(i, c):
        ex, ey = EY[i]
        x0, x1, y0, y1 = int(ex - 3 * r0), int(ex + 3 * r0), int(ey - 3 * r0), int(ey + 3 * r0)
        sub = c[max(0, y0):y1, max(0, x0):x1]
        lum = sub[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32)
        white = (sub[..., 3] > 200) & (lum > 205) & (sub[..., 2] > 190)
        lab, k = ndi.label(white)
        if not k: return None
        sz = ndi.sum(white, lab, range(1, k + 1)); j = int(np.argmax(sz))
        if sz[j] < 0.25 * S0: return None
        wy, wx = ndi.center_of_mass(white, lab, j + 1)
        return np.array([ex - (max(0, x0) + wx), ey - (max(0, y0) + wy)]) / r0
    off0 = iris_off(0, cells[0]); off0 = off0 if off0 is not None else np.zeros(2)
    h0 = math.atan2(NO[0][1] - EY[0][1], NO[0][0] - EY[0][0])
    G = []; lastoff = np.zeros(2)
    for i, c in enumerate(cells):
        h = math.atan2(NO[i][1] - EY[i][1], NO[i][0] - EY[i][0]) - h0
        o = iris_off(i, c) if i not in closed else None
        d = (o - off0) if o is not None else lastoff
        lastoff = d
        # the iris shift, rotated into the head frame: its component across the head direction tilts the gaze
        across = -d[0] * math.sin(h + h0) + d[1] * math.cos(h + h0)
        ang = h + max(-0.35, min(0.35, 0.5 * math.atan(across)))   # the iris adds at most ~20 deg
        G.append((math.cos(ang), math.sin(ang)))
    res['gaze'] = [[round(float(x), 3), round(float(y), 3)] for x, y in G]
    info['gaze_ref'] = 'home looks straight ahead = [1,0]; head angle relative to home + iris roll'
if a.paw:
    fig_h = ay_ - min(np.nonzero(cells[0][..., 3] > 128)[0])
    rad = max(5, int(round(0.055 * fig_h)))
    K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rad + 1, 2 * rad + 1))
    P = []; PP = []
    for i, c in enumerate(cells):
        al = (c[..., 3] > 128).astype(np.uint8)
        core = cv2.morphologyEx(al, cv2.MORPH_OPEN, K)
        lab, k = ndi.label(core)
        if k > 1: core = (lab == 1 + np.argmax(ndi.sum(core, lab, range(1, k + 1)))).astype(np.uint8)
        thin = (al > 0) & (core == 0)
        ccx = XX[core > 0].mean()
        ex, ey = EY[i]; nx, ny = NO[i]
        thin &= ~((XX < ex) & (((XX - ex) ** 2 + (YY - ey) ** 2) < (1.6 * D0) ** 2))   # ears (behind the eye)
        vx_, vy_ = (nx - ex) / D0, (ny - ey) / D0                                     # head axis; chin side = (-vy, vx)
        thin &= ((XX - nx) ** 2 + (YY - ny) ** 2) > (0.35 * D0) ** 2                  # the nose tip itself
        thin &= ~((((XX - nx) ** 2 + (YY - ny) ** 2) < (1.0 * D0) ** 2) & (((XX - nx) * -vy_ + (YY - ny) * vx_) > -0.1 * D0))  # mouth, chin
        thin &= YY < ay_ - 0.16 * fig_h                                                # hind legs, feet
        thin &= XX > ccx                                                               # front (the tail is behind)
        thin = ndi.binary_opening(thin, iterations=1)
        lab, k = ndi.label(thin)
        dist = ndi.distance_transform_edt(core == 0)
        tips = []
        for j in range(1, k + 1):
            m = lab == j; dm = np.where(m, dist, 0); mx = dm.max()
            if mx < 2: continue
            o = dm >= mx - 1.5; tx_, ty_ = XX[o].mean(), YY[o].mean()
            # a paw ends in pink fingers; a fur tuft or a whisker on the chest does not
            near_ = ((XX - tx_) ** 2 + (YY - ty_) ** 2 < 36) & (c[..., 3] > 150)
            r_, g_, b_ = c[..., 0][near_], c[..., 1][near_], c[..., 2][near_]
            npk=int(((r_ > 175) & (r_ - g_ > 45) & (b_ > 0.62 * g_) & (b_ < g_)).sum())
            if i in (9,15): print('dbg',i,round(mx,1),round(tx_),round(ty_),npk, c[int(ty_),int(tx_),:3].round())
            if npk < 3: continue
            tips.append((mx, tx_, ty_))
        tips = sorted(tips, reverse=True)[:2]                      # the two forelimbs reaching furthest
        tips = sorted([(x, y) for _, x, y in tips], key=lambda t: t[1])   # highest first
        PP.append([[round(float(x), 1), round(float(y), 1)] for x, y in tips])
        P.append(tips[0] if tips else (np.nan, np.nan))
    P = np.array(P, float); ok = ~np.isnan(P[:, 0]); info['paw_missing'] = [i for i in range(n) if not ok[i]]
    for d in range(2): P[:, d] = np.interp(range(n), np.nonzero(ok)[0], P[ok, d])
    res['paws'] = PP
    res['paw'] = [[round(float(x), 1), round(float(y), 1)] for x, y in P]
for k_ in ('nose', 'paw'):
    if k_ in res:
        A = np.array(res[k_]); j = np.linalg.norm(np.diff(A, axis=0), axis=1)
        info[k_ + '_max_step'] = round(float(j.max()), 1); info[k_ + '_steps_over_14'] = [int(x) + 1 for x in np.nonzero(j > 14)[0]]
info['eye'] = [[round(float(x), 1), round(float(y), 1)] for x, y in EY]
json.dump({'contacts': res, 'info': info}, open(f'{a.out}/{a.name}.contacts.json', 'w'))
print(a.name, json.dumps({k: v for k, v in info.items() if k != 'eye'}))
pick = list(range(0, n, a.every)) + ([n - 1] if (n - 1) % a.every else [])
per = 8; rows = math.ceil(len(pick) / per)
im = Image.new('RGB', (cw * per, ch * rows), (236, 230, 214)); d = ImageDraw.Draw(im)
for k, i in enumerate(pick):
    ox, oy = (k % per) * cw, (k // per) * ch
    cc = Image.fromarray(cells[i].astype(np.uint8), 'RGBA'); im.paste(cc, (ox, oy), cc)
    d.text((ox + 4, oy + 3), str(i), fill=(60, 40, 30))
    x, y = res['nose'][i]
    if 'gaze' in res:
        gx, gy = res['gaze'][i]; d.line((ox + x, oy + y, ox + x + gx * 50, oy + y + gy * 50), fill=(0, 140, 0), width=2)
        d.ellipse((ox + x + gx * 50 - 4, oy + y + gy * 50 - 4, ox + x + gx * 50 + 4, oy + y + gy * 50 + 4), fill=(0, 160, 0))
    d.ellipse((ox + x - 4, oy + y - 4, ox + x + 4, oy + y + 4), fill=(255, 0, 160), outline=(0, 0, 0))
    ex, ey = EY[i]; d.ellipse((ox + ex - 2, oy + ey - 2, ox + ex + 2, oy + ey + 2), fill=(0, 200, 255))
    if 'paw' in res:
        x, y = res['paw'][i]; d.ellipse((ox + x - 5, oy + y - 5, ox + x + 5, oy + y + 5), fill=(255, 210, 0), outline=(0, 0, 0))
    d.line((ox + ax_ - 5, oy + ay_, ox + ax_ + 5, oy + ay_), fill=(220, 0, 0)); d.line((ox + ax_, oy + ay_ - 5, ox + ax_, oy + ay_ + 5), fill=(220, 0, 0))
im.save(f'{a.out}/{a.name}_dots.jpg', quality=88)
