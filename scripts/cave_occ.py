"""Occluders for the Mountain King's cave creatures (MusicGames fingerpick-warmup, ?p=mountain-king): alpha masks of
rock that is already in the painting (art/cave.webp, 1920x1072), so a creature drawn behind it is ERASED where the
rock is (destination-out) and the painting's own pixels stay — no seam by construction (the rosary lamb's occ.py).

Each nook: ("gc", pts, band) refined by GrabCut inside +-band px of the polygon edge, or ("poly", pts) as drawn;
pts in painting fractions. Writes <out>/occ-<id>.png (white, alpha = how much the rock hides, cropped to its box)
and occ.json {id: {x, y, w, h}} in fractions, plus check-<id>.jpg (mask edge in red over the painting, 2x).
usage: python3 scripts/cave_occ.py CAVE.webp OUTDIR [REVIEWDIR]"""
import sys, os, json, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SPEC = {
  # N1: the big boulder on the left; creatures rise from behind its top edge
  "n1": [("gc", [(0.055, 0.274), (0.09, 0.262), (0.11, 0.254), (0.15, 0.249), (0.17, 0.251), (0.186, 0.259), (0.205, 0.269),
                 (0.218, 0.281), (0.223, 0.30), (0.223, 0.40), (0.055, 0.40)], 5)],
  # N2: the tall spire left of the throne; creatures lean out past its edges
  "n2": [("gc", [(0.311, 0.414), (0.318, 0.407), (0.324, 0.41), (0.328, 0.44), (0.332, 0.49), (0.336, 0.55), (0.341, 0.60),
                 (0.343, 0.66), (0.288, 0.66), (0.293, 0.56), (0.299, 0.48), (0.305, 0.44)], 4)],
  # N3: the small spire and its foot
  "n3": [("gc", [(0.346, 0.52), (0.351, 0.512), (0.356, 0.525), (0.36, 0.553), (0.371, 0.565), (0.377, 0.58), (0.382, 0.61),
                 (0.386, 0.66), (0.338, 0.66), (0.342, 0.57)], 4)],
  # N4: the rock right of the throne, beside the big crystal; creatures rise from behind it
  "n4": [("gc", [(0.638, 0.537), (0.652, 0.50), (0.664, 0.476), (0.683, 0.462), (0.699, 0.467), (0.708, 0.50), (0.712, 0.66),
                 (0.62, 0.66), (0.626, 0.58)], 5)],
  # N5: the mine's door frame: the left post, the lintel and the right jamb (a creature inside stands behind them)
  "n5": [("poly", [(0.722, 0.385), (0.746, 0.385), (0.746, 0.628), (0.722, 0.628)]),
         ("poly", [(0.715, 0.335), (0.83, 0.335), (0.83, 0.398), (0.715, 0.398)]),
         ("gc", [(0.812, 0.395), (0.835, 0.395), (0.84, 0.66), (0.80, 0.66), (0.81, 0.57)], 4)],
  # N6: the big boulder on the right; creatures rise from behind its top edge
  "n6": [("gc", [(0.862, 0.449), (0.874, 0.439), (0.886, 0.43), (0.91, 0.42), (0.94, 0.408), (0.97, 0.40), (1.0, 0.395),
                 (1.0, 0.72), (0.862, 0.72)], 5)],
}

def polymask(pts, W, H):
    im = Image.new("L", (W * 4, H * 4), 0)
    ImageDraw.Draw(im).polygon([(x * W * 4, y * H * 4) for x, y in pts], fill=255)
    return np.array(im.resize((W, H), Image.LANCZOS)).astype(float) / 255

def build(img, shapes):
    H, W = img.shape[:2]; m = np.zeros((H, W))
    for sh in shapes:
        kind, pts = sh[0], sh[1]; P = polymask(pts, W, H)
        if kind == "gc":
            band = sh[2]; inside = P > .5
            gm = np.full((H, W), cv2.GC_BGD, np.uint8)
            gm[ndi.binary_dilation(inside, iterations=band)] = cv2.GC_PR_BGD
            gm[inside] = cv2.GC_PR_FGD
            gm[ndi.binary_erosion(inside, iterations=band, border_value=1)] = cv2.GC_FGD
            bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
            cv2.grabCut(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), gm, None, bg, fg, 4, cv2.GC_INIT_WITH_MASK)
            g = ((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)).astype(float)
            lab, n = ndi.label(g > .5)                     # keep the piece(s) touching the polygon's sure core
            core = ndi.binary_erosion(inside, iterations=band, border_value=1)
            keep = np.isin(lab, np.unique(lab[core & (lab > 0)])); g = keep.astype(float)
            g = ndi.binary_fill_holes(g > .5).astype(float)
            P = ndi.gaussian_filter(g, 0.9)
        m = np.maximum(m, P)
    return np.clip(m, 0, 1)

if __name__ == "__main__":
    cave, out = sys.argv[1], sys.argv[2]; rev = sys.argv[3] if len(sys.argv) > 3 else out
    os.makedirs(out, exist_ok=True); os.makedirs(rev, exist_ok=True)
    img = np.array(Image.open(cave).convert("RGB")); H, W = img.shape[:2]; meta = {}
    for id, shapes in SPEC.items():
        m = build(img, shapes); ys, xs = np.where(m > 0.01)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        a = (m[y0:y1, x0:x1] * 255).round().astype(np.uint8)
        rgba = np.dstack([np.full_like(a, 255)] * 3 + [a])
        Image.fromarray(rgba).save(os.path.join(out, "occ-%s.png" % id), optimize=True)
        meta[id] = {"x": round(x0 / W, 5), "y": round(y0 / H, 5), "w": round((x1 - x0) / W, 5), "h": round((y1 - y0) / H, 5)}
        pad = 40; cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
        crop = img[cy0:cy1, cx0:cx1].copy().astype(float); mm = m[cy0:cy1, cx0:cx1]
        edge = (mm > .5) ^ ndi.binary_erosion(mm > .5, iterations=1)
        crop = crop * (1 - 0.35 * mm[..., None]) + np.array([60, 200, 255]) * 0.35 * mm[..., None]; crop[edge] = [255, 0, 0]
        Image.fromarray(crop.astype(np.uint8)).resize(((cx1 - cx0) * 2, (cy1 - cy0) * 2), Image.NEAREST).save(os.path.join(rev, "check-%s.jpg" % id), quality=85)
    json.dump(meta, open(os.path.join(out, "occ.json"), "w"), indent=1)
    print(json.dumps(meta))
