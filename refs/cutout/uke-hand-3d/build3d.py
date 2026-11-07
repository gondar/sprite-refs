#!/usr/bin/env python3
"""The UkuZiom Short's left hand on the ukulele neck, second version: driven by a 3D model.

The 3D scene (scene/scene.html, a rigged WebXR hand, MIT, posed by scene/poses.js) renders the rest pose and the six
pressed poses with one camera (guides/<state>-{shaded,id,depth,normal,clay}.png, 2200x1238 = the 1100x619 canvas x2;
the final 1100x528 picture is that canvas from row 91 down). base.png is ONE painting of the rest render (Nano Banana
Pro). Each pressed state:

  collage STATE   base painting everywhere, except inside M = the moving finger in the rest render OR in the state
                  render (grown a little): there the state's 3D render, colour-matched to the painting
                  -> collage/<state>.jpg, the input of one Nano Banana flash edit ("repaint this finger")
  build OUTDIR    every state = the base painting outside M, the edit inside M (feathered), so all pixels away from
                  the moving finger are the base's; magenta keyed out; scaled and cropped to 1100x528 WebP.
                  edits.json names the edit used per state; "stretch" lengthens an edit's finger (factor about the
                  canvas top) where the edit drew it shorter than the 3D pose, so the nail sits on its string

Guides (re-render): serve the folder ABOVE scene/'s parent with scene/serve.py, put three@0.170.0 under npm3d/
(scene.html's import map), then  OPT="$(cat scene/opt-final.txt)" node scene/run.cjs scene/poses.js guides
(run.cjs and poses.js expect the files at /h3d/ and /npm3d/ on http://127.0.0.1:8765; see their headers).
The hand: @webxr-input-profiles/assets generic-hand/left.glb (MIT, scene/hand-LICENSE.md), fingers slimmed by 14 %,
scale .88; the neck: frets and strings at hand.json's pixels, an oblique parallel view (scene.html: a, b, sy).
Rest = a fixed natural curl, wrist solved so the tips hover over the A string; a press = that finger re-solved by grid
IK (tip on the string, fingertip pointing down, no collision with the neck), the wrist and other fingers fixed.

usage: python3 build3d.py collage e1 | python3 build3d.py build OUTDIR"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1376, 768                  # working size (= Nano Banana 16:9 1K); the guides' 1100x619 canvas maps onto it
OUT_W, CANVAS_H, PADTOP, OUT_H = 1100, 619, 91, 528
FINGER = {"e1": "index", "c1": "index", "e2": "middle", "c2": "middle", "e3": "ring", "c3": "ring"}
IDCOL = {"index": (255, 0, 0), "middle": (0, 255, 0), "ring": (0, 0, 255), "pinky": (255, 255, 0), "thumb": (0, 255, 255)}
EDITS = json.load(open(os.path.join(HERE, "edits.json"))) if os.path.exists(os.path.join(HERE, "edits.json")) else {}


def rgb(path, size=(W, H)):
    return np.asarray(Image.open(path).convert("RGB").resize(size, Image.LANCZOS)).astype(np.float32)


def idmask(state, finger):
    a = np.asarray(Image.open(os.path.join(HERE, "guides", f"{state}-id.png")).convert("RGB").resize((W, H), Image.NEAREST)).astype(int)
    c = IDCOL[finger]
    return (np.abs(a - c).sum(2) < 60)


def hand(state):
    a = np.asarray(Image.open(os.path.join(HERE, "guides", f"{state}-id.png")).convert("RGB").resize((W, H), Image.NEAREST)).astype(int)
    return a.max(2) > 200      # any hand colour (the neck is dark grey, background black)


def region(state, grow=7):
    f = FINGER[state]
    m = idmask("rest", f) | idmask(state, f)
    return ndimage.binary_dilation(m, iterations=grow)


def match(src, ref, msrc, mref):
    """per-channel mean/std transfer of src's pixels (msrc) to ref's statistics (mref)"""
    out = src.copy()
    for c in range(3):
        s, r = src[..., c][msrc], ref[..., c][mref]
        if len(s) < 50 or len(r) < 50: continue
        out[..., c][msrc] = (s - s.mean()) / (s.std() + 1e-6) * r.std() + r.mean()
    return np.clip(out, 0, 255)


def collage(state):
    base = rgb(os.path.join(HERE, "base.png"))
    ren = rgb(os.path.join(HERE, "guides", f"{state}-shaded.png"))
    M = region(state)
    skin_r = hand(state) & M
    skin_b = hand("rest")
    neck_r = ~hand(state) & M & ~(np.abs(ren - [255, 0, 255]).sum(2) < 60)
    neck_b = ~hand("rest") & ~(np.abs(base - [255, 0, 255]).sum(2) < 90)
    ren2 = match(ren, base, skin_r, skin_b)
    ren2 = np.where(neck_r[..., None], match(ren, base, neck_r, neck_b), ren2)
    soft = ndimage.gaussian_filter(M.astype(np.float32), 1.5)[..., None]
    col = base * (1 - soft) + ren2 * soft
    os.makedirs(os.path.join(HERE, "collage"), exist_ok=True)
    Image.fromarray(col.astype(np.uint8)).save(os.path.join(HERE, "collage", f"{state}.jpg"), quality=93)
    Image.fromarray((M * 255).astype(np.uint8)).save(os.path.join(HERE, "collage", f"{state}-mask.png"))


def key(img):
    """alpha from the magenta key: distance from #FF00FF, soft edge; de-spill the magenta"""
    d = np.sqrt(((img - [255, 0, 255]) ** 2).sum(2))
    a = np.clip((d - 70) / 70, 0, 1)
    sp = np.minimum(img[..., 0], img[..., 2]) - img[..., 1]
    fix = img.copy()
    edge = ndimage.binary_dilation(a < .5, iterations=5)          # a band along the cut-out's outline
    m = (sp > 0) & ((a < 1) | edge)
    k = np.where(edge, 1.0, 1 - a)[m]
    fix[..., 0][m] -= sp[m] * k
    fix[..., 2][m] -= sp[m] * k
    return np.clip(fix, 0, 255), a


def build(out):
    base = rgb(os.path.join(HERE, "base.png"))
    os.makedirs(out, exist_ok=True)
    info = {}
    for st in ["rest"] + list(FINGER):
        if st == "rest": img = base
        else:
            ed = rgb(os.path.join(HERE, EDITS[st]))
            f = EDITS.get("stretch", {}).get(st)
            if f:   # the edit drew the finger a little short: lay a copy stretched down about the canvas top over it,
                    # only its finger (skin, nail and outline), so the strings and frets keep their places
                hh = int(round(H * f))
                es = np.asarray(Image.fromarray(ed.astype(np.uint8)).resize((W, hh), Image.LANCZOS)).astype(np.float32)[:H]
                r, g, b = es[..., 0], es[..., 1], es[..., 2]
                sk = (r > 150) & (g > 90) & (r - b > 30) & ~((r > 200) & (b > 200) & (g < 120))
                sk = ndimage.binary_opening(sk, iterations=2) & region(st, grow=10)
                lab, n = ndimage.label(sk)
                if n: sk = lab == (np.argmax(ndimage.sum(sk, lab, range(1, n + 1))) + 1)
                sk = ndimage.binary_fill_holes(ndimage.binary_dilation(sk, iterations=3))
                so = ndimage.gaussian_filter(sk.astype(np.float32), 1.0)[..., None]
                ed = ed * (1 - so) + es * so
            g = EDITS.get("grow", 10); M = region(st, grow=g.get(st, 10) if isinstance(g, dict) else g)
            soft = ndimage.gaussian_filter(M.astype(np.float32), 2.0)[..., None]
            img = base * (1 - soft) + ed * soft
        im, a = key(img)
        rgba = np.dstack([im, a * 255]).astype(np.uint8)
        P = Image.fromarray(rgba, "RGBA").resize((OUT_W, CANVAS_H), Image.LANCZOS).crop((0, PADTOP, OUT_W, CANVAS_H))
        # fade the neck's cut end on the right, as before
        arr = np.asarray(P).astype(np.float32); x = np.arange(OUT_W)
        arr[..., 3] *= np.clip((OUT_W - 4 - x) / 70, 0, 1)[None, :]
        P = Image.fromarray(arr.astype(np.uint8), "RGBA")
        name = "open" if st == "rest" else st
        P.save(os.path.join(out, f"hand-{name}.webp"), quality=90, method=6)
        P.save(os.path.join(out, f"hand-{name}.png"))
    return info


if __name__ == "__main__":
    if sys.argv[1] == "collage":
        for s in sys.argv[2:]: collage(s)
    elif sys.argv[1] == "build":
        build(sys.argv[2])
