#!/usr/bin/env python3
"""Register an edit of a reference picture back onto the reference (similarity: scale, rotation, shift).

Nano Banana returns edits at its own canvas size (1024²) and often slightly shifted or zoomed. We fit
src_xy = s·R(θ)·edit_xy + t by minimising the colour difference inside a region of the reference that the edit
did NOT change (a mask you give: the throne + legs for a body edit, the head minus the eyes for a face edit).
Coarse (1/4 res) Nelder-Mead, then refined at 1/2 res.

usage (library): warp, params = register(ref_rgb, edit_rgb, mask) ; warp(edit_rgba) -> array in ref coords"""
import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import minimize


def _mat(p):
    s, th, tx, ty = p
    c, si = np.cos(th), np.sin(th)
    return np.array([[s * c, -s * si], [s * si, s * c]]), np.array([tx, ty])


def warp_to_ref(img, p, shape, order=1):
    """img (h,w,C) in edit coords -> (H,W,C) in ref coords. ndi works in (row, col) = (y, x)."""
    A, t = _mat(p)                       # src = A·e + t (x,y)  ->  e = A^-1 (src - t)
    Ai = np.linalg.inv(A)
    # convert to (y,x) ordering
    P = np.array([[0, 1], [1, 0]])
    M = P @ Ai @ P; off = -(P @ Ai @ t)
    out = np.stack([ndi.affine_transform(img[..., c].astype(float), M, offset=off, output_shape=shape, order=order,
                                         mode="constant", cval=0) for c in range(img.shape[2])], -1)
    return out


def register(ref, edit, mask, p0=None, verbose=True):
    H, W = ref.shape[:2]
    if p0 is None: p0 = [W / edit.shape[1], 0.0, 0.0, 0.0]
    best = np.array(p0, float)
    for f, iters in ((4, 400), (2, 200)):
        r = ndi.gaussian_filter(ref[::f, ::f].astype(float), (1.5, 1.5, 0))
        e = ndi.gaussian_filter(edit.astype(float), (f * 0.75, f * 0.75, 0))
        m = mask[::f, ::f].astype(bool)
        def cost(q):
            p = [q[0], q[1], q[2], q[3]]
            A, t = _mat(p)
            pp = [p[0], p[1], p[2] / f, p[3] / f]
            A2, t2 = _mat(pp)
            # edit at full res -> ref at /f: scale s/f
            w = warp_to_ref(e, [p[0] / f, p[1], p[2] / f, p[3] / f], r.shape[:2])
            d = np.abs(w - r).mean(2)[m]
            return d.mean()
        scl = np.array([0.01, 0.005, 4, 4])
        res = minimize(lambda z: cost(best + z * scl), np.zeros(4), method="Nelder-Mead",
                       options={"maxiter": iters, "xatol": 0.05, "fatol": 0.01, "initial_simplex": np.vstack([np.zeros(4), np.eye(4) * 1.5])})
        best = best + res.x * scl
        if verbose: print(f"   1/{f}: s={best[0]:.4f} rot={np.degrees(best[1]):.2f}° t=({best[2]:.1f},{best[3]:.1f}) err={res.fun:.2f}")
    return (lambda img, order=1: warp_to_ref(img, best, (H, W), order)), best


if __name__ == "__main__":
    # register.py REF.png --out refs/cutout/<char>/register.json EDIT.png[=body|lower] ...
    #   body  = fit on the whole figure (face edits: the changed eyes/mouth are a small share, L1 ignores them)
    #   lower = fit on the bottom 38 % of the figure (edits that change the upper body: a removed figure, an arm)
    # Merges into --out (key = edit file name without .png), so new edits can be added later.
    import argparse, json, os, sys
    from PIL import Image
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import key
    # register.py REF.png --home STRIP.json:FRAME --cell W,H --pivot X,Y --out rigs/<char>/home_fit.json
    #   fits the picture into the game cell onto an existing home frame (pack.py strip), silhouette + colour
    ap = argparse.ArgumentParser(); ap.add_argument("ref"); ap.add_argument("edits", nargs="*")
    ap.add_argument("--out", required=True); ap.add_argument("--key", default="magenta")
    ap.add_argument("--home"); ap.add_argument("--cell"); ap.add_argument("--pivot"); a = ap.parse_args()
    src = np.array(Image.open(a.ref).convert("RGB")).astype(float)
    ka, _ = key.key_image(src, a.key); sil = ka[..., 3] > 128
    if a.home:
        path, _, fi = a.home.partition(":"); meta = json.load(open(path)); cw, chh = meta["cell"]; fi = int(fi or 0)
        f = Image.open(path[:-5] + ".png").convert("RGBA").crop((fi * cw, 0, fi * cw + cw, chh)); pv = meta["pivot"]
        W, H = map(int, a.cell.split(",")); PV = list(map(float, a.pivot.split(",")))
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); c.alpha_composite(f, (int(round(PV[0] - pv[0])), int(round(PV[1] - pv[1]))))
        h = np.array(c).astype(float); hp = np.dstack([h[..., :3] * h[..., 3:] / 255, h[..., 3]])
        sp = np.dstack([ka[..., :3] * ka[..., 3:] / 255, ka[..., 3]])
        hy, hx = np.nonzero(h[..., 3] > 128); sy, sx = np.nonzero(sil)
        s0 = (np.ptp(hy) + np.ptp(hx)) / (np.ptp(sy) + np.ptp(sx))
        p = [s0, 0, hx.min() - sx.min() * s0, hy.min() - sy.min() * s0]
        m = ndi.binary_dilation(h[..., 3] > 10, iterations=6)
        for _ in range(3): w, p = register(hp, sp, m, p0=list(p))
        r = w(sp)[..., 3] > 128; hm = h[..., 3] > 128
        print(f"home fit IoU {(r & hm).sum() / (r | hm).sum():.3f}")
        json.dump({"src_to_cell": [float(v) for v in p]}, open(a.out, "w")); sys.exit()
    body = ndi.binary_erosion(sil, iterations=6); ys = np.nonzero(sil)[0]
    lower = body & (np.arange(src.shape[0])[:, None] > ys.min() + 0.62 * (ys.max() - ys.min()))
    R = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for e in a.edits:
        path, _, mode = e.partition("="); name = os.path.splitext(os.path.basename(path))[0]
        print(name); _, p = register(src, np.array(Image.open(path).convert("RGB")).astype(float), lower if mode == "lower" else body)
        R[name] = [float(v) for v in p]
    json.dump(R, open(a.out, "w"), indent=1)
