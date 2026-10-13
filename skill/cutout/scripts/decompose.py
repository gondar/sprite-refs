#!/usr/bin/env python3
"""Take a finished character picture apart into puppet layers, so the rest pose IS the original picture.

Inputs (all edits of the same reference picture by Nano Banana, same canvas):
  ref      the character on a flat key colour
  seg      the same picture recoloured as flat parts (colour per part, black background) — lines up to ~1 px
  fills    edits with a part removed and the hidden area painted in (e.g. "no hat, no wing") — the layer under
           a part comes from these, so moving the part reveals painted fur instead of a hole
  swaps    edits that change only the face (blink, sing) — become overlays cut where they differ from ref

usage: decompose.py SPEC.json OUTDIR
SPEC: {"ref": …, "seg": …, "key": "green", "colors": {"head": [255,0,0], …, "bg": [0,0,0]},
       "fills": {"nohat": "path", "body": "path"},                       # name -> edit picture
       "register": ["body"],                                              # fills that came back shifted/scaled
       "layers": [{"name": "body", "parts": ["body","feet"], "under": ["wing","head"], "from": "body",
                   "parent": null, "pivot": "bottom", "z": 1},
                  {"name": "head", "parts": ["head","hat"], "src": "nohat", "parent": "body",
                   "soft_into": ["body"], "z": 3}, …],
       "swaps": {"blink": {"src": "path", "parent": "head", "within": ["head"]}}}
Pivot of a layer = centre of its contact edge with the parent layer (or "bottom" / "centre").
Writes OUTDIR/pNN.png, pieces.json and rig.json (pivot == at, canvas pixels), check.png."""
import json, os, sys, importlib.util, numpy as np
from PIL import Image
from scipy import ndimage as ndi

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("key", os.path.join(here, "key.py"))
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

S = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
rgb = lambda p: np.array(Image.open(p).convert("RGB")).astype(float)


def keyed(p):
    a, _ = key.key_image(rgb(p), S.get("key", "auto"))
    a[..., 3] = np.clip((a[..., 3] - 64) / 191, 0, 1) * 255  # choke the soft edge: no light fringe on dark grounds
    return a


ref = keyed(S["ref"]); H, W = ref.shape[:2]
seg = rgb(S["seg"]); names = list(S["colors"]); C = np.array([S["colors"][n] for n in names], float)
lab = ((seg[:, :, None, :] - C[None, None]) ** 2).sum(3).argmin(2)
part = {n: lab == i for i, n in enumerate(names)}


def main_blobs(m):
    l, k = ndi.label(m)
    if k <= 1: return m
    sz = ndi.sum(m, l, range(1, k + 1)); return np.isin(l, 1 + np.nonzero(sz > 0.1 * sz.max())[0])


sil = ref[..., 3] > 128
# seg edges are guesses; snap: anything inside the real silhouette labelled bg goes to the nearest part
bgi = names.index("bg"); fix = sil & (lab == bgi)
if fix.any():
    _, (iy, ix) = ndi.distance_transform_edt(lab == bgi, return_indices=True)
    lab[fix] = lab[iy[fix], ix[fix]]
part = {n: (main_blobs(lab == i) if n != "bg" else lab == i) for i, n in enumerate(names)}


def register(img, target_mask):
    """Similarity-fit a fill that came back scaled/shifted: best IoU of its silhouette against the target."""
    m = img[..., 3] > 128; best = (0, 1, 0, 0)
    # compare the lower half only: fills often paint the part taller (body continued up under the head)
    tys = np.nonzero(target_mask)[0]; low = np.arange(H)[:, None] > (tys.min() + tys.max()) / 2
    target_mask = target_mask & low
    mys, mxs = np.nonzero(m); tyx = np.nonzero(target_mask)
    s0 = (tyx[1].max() - tyx[1].min()) / (np.ptp(mxs[mys > (mys.min() + mys.max()) / 2]) + 1)
    for s in np.arange(s0 - 0.08, s0 + 0.08, 0.01):
        z = ndi.zoom(m.astype(float), s, order=0) > 0.5
        zys, zxs = np.nonzero(z); zy, zx = zys.max(), zxs.mean()  # align bottoms (feet on the ground)
        ty, tx = tyx[0].max(), tyx[1].mean()
        for dy in range(-30, 31, 3):
            for dx in range(-30, 31, 3):
                oy, ox = int(round(ty - zy + dy)), int(round(tx - zx + dx))
                c = np.zeros((H, W), bool)
                ys, xs = np.nonzero(z); ys, xs = ys + oy, xs + ox; k = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
                c[ys[k], xs[k]] = True; c &= low
                iou = (c & target_mask).sum() / (c | target_mask).sum()
                if iou > best[0]: best = (iou, s, oy, ox)
    iou, s, oy, ox = best
    res = np.zeros_like(img)
    z = np.stack([ndi.zoom(img[..., c], s, order=1) for c in range(4)], -1)
    y0, x0 = max(0, oy), max(0, ox); y1, x1 = min(H, oy + z.shape[0]), min(W, ox + z.shape[1])
    res[y0:y1, x0:x1] = z[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    print(f"  registered: scale {s:.2f} shift ({ox},{oy}) IoU {iou:.3f}")
    return res


fills = {}
for n, p in S.get("fills", {}).items():
    f = keyed(p)
    if n in S.get("register", []):
        tgt = np.zeros((H, W), bool)
        for q in S["register"][n]:  # {"fill name": [parts its silhouette should cover]}
            tgt |= part[q]
        f = register(f, tgt)
    fills[n] = f

pieces, bones, layers = [], [], {}


def soften(alpha, mask, into, px):
    """Fade the layer's alpha over px pixels where it borders the `into` region (an inner seam), keep outer edges."""
    if not into.any(): return alpha
    d = ndi.distance_transform_edt(~into)
    return alpha * np.where(mask & (d < px + 2), np.clip(d / px, 0, 1), 1)


def save(name, img, mask):
    a = img.copy(); a[..., 3] = a[..., 3] * mask
    ys, xs = np.nonzero(a[..., 3] > 2)
    if not len(ys): raise SystemExit(f"layer {name} is empty")
    y0, y1, x0, x1 = max(0, ys.min() - 2), min(H, ys.max() + 3), max(0, xs.min() - 2), min(W, xs.max() + 3)
    pid = f"p{len(pieces):02d}"
    Image.fromarray(np.round(a[y0:y1, x0:x1]).astype(np.uint8)).save(os.path.join(out, pid + ".png"))
    pieces.append({"id": pid, "name": name, "bbox": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], "area": int((a[..., 3] > 128).sum())})
    layers[name] = a
    return pid


def contact(a, b, top=None):
    ring = ndi.binary_dilation(b, iterations=3) & a
    if top: ys = np.nonzero(ring)[0]; ring &= np.arange(H)[:, None] < ys.min() + top * (ys.max() - ys.min() + 1)
    ys, xs = np.nonzero(ring)
    return [float(xs.mean()), float(ys.mean())]


for L in S["layers"]:
    own = np.zeros((H, W), bool)
    for q in L["parts"]: own |= part[q]
    for q in L.get("exclude", []): own &= ~ndi.binary_dilation(part[q], iterations=3)  # never carry a neighbour's pixels
    under = np.zeros((H, W), bool)
    for q in L.get("under", []): under |= part[q]
    img = ref.copy()
    if L.get("src"): img = fills[L["src"]].copy()
    alpha_m = own.astype(float)
    if L.get("from"):  # visible pixels from the picture, hidden ones (under other parts) from a fill
        f = fills[L["from"]]
        inner = own & ~ndi.binary_dilation(under, iterations=9) if under.any() else own
        w = np.clip(ndi.distance_transform_edt(inner) / 10, 0, 1)[..., None] if under.any() else 1
        img = ref * w + f * (1 - w)
        img[..., 3] = np.maximum(ref[..., 3] * own, f[..., 3] * (under | own))
        alpha_m = ((own | under) & (img[..., 3] > 0)).astype(float)
        if L.get("fill_extra"):  # let the fill's own silhouette count (body painted taller under the head)
            alpha_m = np.maximum(alpha_m, (f[..., 3] > 128) & under)
        # seg edges between two parts can leave a 1-px crack; close it and make it opaque
        solid = ndi.binary_fill_holes(ndi.binary_closing(alpha_m > 0.5, iterations=3))
        crack = solid & (img[..., 3] < 250) & ndi.binary_erosion(solid, iterations=2)
        img[..., 3][crack] = 255; alpha_m = np.maximum(alpha_m, solid)
    else:
        alpha_m = ndi.gaussian_filter(own.astype(float), 0.7)  # antialias the seg edge
    for q in L.get("soft_into", []):
        alpha_m = soften(alpha_m, own, part[q] & ~own, L.get("soft_px", 10))
    if L.get("mirror_of"):  # far limb: mirrored copy of a near one, scaled
        src = layers[L["mirror_of"]]; img = np.roll(src[:, ::-1], L.get("mirror_dx", 0), 1).copy()
        alpha_m = (img[..., 3] > 0).astype(float)
    pid = save(L["name"], img, alpha_m)
    parent = L.get("parent")
    if L.get("pivot") == "bottom":
        ys, xs = np.nonzero(layers[L["name"]][..., 3] > 128); piv = [float(xs.mean()), float(ys.max())]
    elif isinstance(L.get("pivot"), list): piv = L["pivot"]
    else:
        piv = contact(layers[L["name"]][..., 3] > 128, layers[parent][..., 3] > 128, L.get("top"))
    b = {"name": L["name"], "piece": pid, "pivot": [round(v, 1) for v in piv], "z": L.get("z", 0)}
    if parent: b.update(parent=parent, at=b["pivot"])
    if L.get("rot"): b["rot"] = L["rot"]
    if L.get("hidden"): b["hidden"] = True
    if L.get("mirror_of"): b["scale"] = L.get("scale_mirror", 0.85)
    bones.append(b)

for n, sw in S.get("swaps", {}).items():
    f = keyed(sw["src"])
    within = np.zeros((H, W), bool)
    for q in sw["within"]: within |= part[q]
    diff = np.abs(f[..., :3] - ref[..., :3]).max(2) > sw.get("thr", 40)
    m = ndi.binary_dilation(ndi.binary_opening(diff & within, iterations=2), iterations=sw.get("grow", 10)) & within
    lab2, k = ndi.label(m)
    if k > 1:  # keep the big blobs only (stray single-pixel differences elsewhere on the head)
        sizes = ndi.sum(m, lab2, range(1, k + 1)); m = np.isin(lab2, 1 + np.nonzero(sizes > 0.15 * sizes.max())[0])
    alpha = np.clip(ndi.gaussian_filter(m.astype(float), sw.get("feather", 4)) * 1.6 - 0.3, 0, 1) * (f[..., 3] > 128)
    pid = save(n, f, alpha)
    pb = next(b for b in bones if b["name"] == sw["parent"])
    bones.append({"name": n, "piece": pid, "pivot": pb["pivot"], "parent": sw["parent"], "at": pb["pivot"], "z": pb["z"] + 0.5, "hidden": True})

json.dump({"sheet": S["ref"], "size": [W, H], "pieces": pieces}, open(os.path.join(out, "pieces.json"), "w"), indent=1)
json.dump({"bones": bones}, open(os.path.join(out, "rig.json"), "w"), indent=1)
# check.png: every layer side by side on grey
cells = [Image.fromarray(np.round(layers[p["name"]]).astype(np.uint8)).crop(tuple([p["bbox"][0], p["bbox"][1], p["bbox"][0] + p["bbox"][2], p["bbox"][1] + p["bbox"][3]])) for p in pieces]
cw = sum(c.width for c in cells) + 10 * len(cells); ch = max(c.height for c in cells)
sheet = Image.new("RGBA", (cw, ch), (70, 70, 70, 255)); x = 0
for c in cells: sheet.alpha_composite(c, (x, 0)); x += c.width + 10
sheet.convert("RGB").save(os.path.join(out, "check.png"))
for b in bones: print(f"  {b['name']:10s} {b['piece']} pivot {b['pivot']} parent {b.get('parent')}")
