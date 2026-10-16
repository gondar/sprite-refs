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
