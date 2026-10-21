"""Blue-dominance key for the eagle (white / black ink / gold on flat blue). Used for the design pictures and per video frame."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

def bg_of(rgb):
    b = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    return np.median(b, 0)

def key(rgb, bg=None, lo=30, hi=None, min_area=400, choke=0.0):
    rgb = rgb.astype(float)
    if bg is None: bg = bg_of(rgb)
    dbg = bg[2] - max(bg[0], bg[1])                     # how much blue dominates on the ground (~100)
    if hi is None: hi = dbg * 0.8
    dom = rgb[..., 2] - rgb[..., :2].max(2)
    a = np.clip((hi - dom) / (hi - lo), 0, 1)
    # drop specks: keep components of the solid mask above min_area (and everything within 3 px of them)
    lab, n = ndi.label(a > 0.5)
    if n:
        sz = ndi.sum(np.ones_like(a), lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.nonzero(sz >= min_area)[0])
        a = a * ndi.binary_dilation(keep, iterations=3)
    if choke: a = np.clip((a - choke) / (1 - choke), 0, 1)
    # un-mix the ground from edge pixels, then clamp any blue left over to the other two channels
    am = np.maximum(a, 1e-3)[..., None]
    col = np.clip((rgb - (1 - a[..., None]) * bg) / am, 0, 255)
    col = np.where(a[..., None] > 0.02, col, 0)
    mx = col[..., :2].max(2)
    edge = a < 0.98
    col[..., 2] = np.where(edge, np.minimum(col[..., 2], mx + 8), col[..., 2])
    return np.dstack([col, a * 255])
