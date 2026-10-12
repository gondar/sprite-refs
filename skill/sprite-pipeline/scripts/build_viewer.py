#!/usr/bin/env python3
"""Bake packed strips into the single-file review viewer (offline: every strip is an embedded WebP data URI).

usage: build_viewer.py OUT.html NAME=STRIP.png[|note] ...
       build_viewer.py OUT.html --manifest experiments.json
The manifest is a list of experiments {id, title, route, model, cost, yields, setup, result, verdict,
verdict_kind (win|fail), takes:[{name, strip, note}]}; the page groups takes under their experiment and shows
the price, the cost per usable animation and the setup next to the playing take.
Each STRIP.png needs its STRIP.json beside it (pack.py writes both). Strips are re-encoded as WebP (q 88,
alpha kept) to keep the page small. The template is ../viewer/viewer.html; it also accepts dropped files."""
import base64, io, json, os, sys
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, "..", "viewer", "viewer.html")).read()
takes = []
items = []
if len(sys.argv) > 3 and sys.argv[2] == "--manifest":
    for e in json.load(open(sys.argv[3])):
        exp = {k: v for k, v in e.items() if k != "takes"}
        for t in e["takes"]: items.append((t["name"], t["strip"], t.get("note", ""), exp))
else:
    for arg in sys.argv[2:]:
        name, rest = arg.split("=", 1); path, note = (rest.split("|", 1) + [""])[:2]; items.append((name, path, note, None))
for name, path, note, exp in items:
    meta = json.load(open(path[:-4] + ".json"))
    buf = io.BytesIO(); Image.open(path).save(buf, "WEBP", quality=88, method=6)
    src0 = (meta.pop("sources", None) or [""])[0]
    lj = os.path.join(os.path.dirname(os.path.dirname(src0)), "loop.json")  # video takes: frames/<job>/loop/f_00.png
    if os.path.exists(lj): meta["seam"] = json.load(open(lj))["loop"]["seam_score"]
    takes.append({"name": name, "note": note, "exp": exp, "meta": meta, "src": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()})
html = tpl.replace("/*TAKES*/[]", json.dumps(takes))
open(sys.argv[1], "w").write(html)
print(sys.argv[1], round(len(html) / 1024), "KB,", len(takes), "takes")
