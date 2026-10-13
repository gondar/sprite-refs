#!/usr/bin/env python3
"""Bundle cut-out rigs into one self-contained HTML page (pieces embedded as webp).

usage: build_page.py OUT.html RIG.json [RIG.json …] [--scale 0.5] [--template page.html] [--extra name=path …]
Each rig names its pieces folder (from pieces.py); per bone: `erase` [[x,y,r]…] clears joint tabs that would
show, `mask: "ellipse"` feathers a rectangular face patch into an oval. The template gets
/*RIGS*/ (JSON with data-URL pieces), /*PLAYER*/ (cutout.js) and /*EXTRA*/ (named data URLs) replaced."""
import argparse, base64, io, json, os, numpy as np
from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("rigs", nargs="+")
ap.add_argument("--scale", type=float, default=0.5)
ap.add_argument("--template", default=os.path.join(here, "..", "player", "page.html"))
ap.add_argument("--extra", action="append", default=[])
ap.add_argument("--content", help="JS file defining window.__build(app, kit) — the page text and layout")
a = ap.parse_args()


def durl(im, q=88):
    b = io.BytesIO(); im.save(b, "WEBP", quality=q, method=6)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())


rigs, report = [], []
for rp in a.rigs:
    rig = json.load(open(rp))
    rig.pop("verdict_md", None)
    meta = {p["id"]: p for p in json.load(open(os.path.join(rig["pieces"], "pieces.json")))["pieces"]}
    total = 0
    for b in rig["bones"]:
        p = meta[b["piece"]]; x0, y0, w, h = p["bbox"]
        arr = np.array(Image.open(os.path.join(rig["pieces"], b["piece"] + ".png")).convert("RGBA")).astype(float)
        yy, xx = np.mgrid[0:h, 0:w]
        for ex, ey, r in b.get("erase", []):
            d = np.hypot(xx + x0 - ex, yy + y0 - ey)
            arr[..., 3] *= np.clip((d - r) / 3, 0, 1)
        if b.get("mask") == "ellipse":
            d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
            arr[..., 3] *= np.clip((1 - d) / 0.25, 0, 1)
        im = Image.fromarray(arr.astype(np.uint8))
        im = im.resize((max(1, round(w * a.scale)), max(1, round(h * a.scale))), Image.LANCZOS)
        b["src"], n = durl(im); total += n
        b["bbox"] = [x0, y0, w, h]
    rig["bytes"] = total
    report.append(f"{rig['name']}: {len(rig['bones'])} pieces, {total/1024:.0f} KB at scale {a.scale}")
    rigs.append(rig)
extra = {}
for e in a.extra:
    k, p = e.split("=", 1)
    extra[k] = "data:" + ({".webp": "image/webp", ".png": "image/png", ".gif": "image/gif"}[os.path.splitext(p)[1]]) + ";base64," + base64.b64encode(open(p, "rb").read()).decode()
html = open(a.template).read()
html = html.replace("/*RIGS*/", json.dumps(rigs)).replace("/*EXTRA*/", json.dumps(extra))
html = html.replace("/*PLAYER*/", open(os.path.join(here, "..", "player", "cutout.js")).read())
if a.content: html = html.replace("/*CONTENT*/", open(a.content).read())
open(a.out, "w").write(html)
print("\n".join(report)); print(f"wrote {a.out} ({os.path.getsize(a.out)/1024:.0f} KB)")
