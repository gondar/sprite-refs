#!/usr/bin/env python3
"""Build ONE self-contained HTML review page for generated animations (offline, no cost).

usage: build_preview.py SPEC.json OUT.html [--embed | --no-skeleton]

SPEC.json:
{
  "title": "Cat GIF Lab",                 # the page's name
  "intro": "One paragraph of context.",
  "items": [{
     "name": "cat-walk", "title": "Walking cat", "purpose": "what it is for in the game",
     "gif": "outputs/cat.gif",            # the generated GIF (numbers are measured from it)
     "sheet": "outputs/sheets/cat.json",  # optional: build_spritesheet.py manifest -> frame scrubber
     "game_sheet": "outputs/sheets/cat-walk.json",   # optional: a keyed RGBA sheet, scrubbed on the same panel
     "provider": "APIYI", "model": "gpt-image-2.6-flare", "latency_s": 7.2, "cost": "$0.018 (estimate)",
     "verdict": "usable" | "usable with fixes" | "not usable" | "baseline",
     "notes": ["observation", ...]
  }],
  "compare": [{"label": "Before", "src": "path.webp", "caption": "..."}]   # optional still gallery
}
Paths are relative to SPEC.json. With --embed every file becomes a data: URI (one file you can send
anywhere); without it the page links the files relative to OUT.html (keep them side by side).
--no-skeleton links the files but leaves out <!doctype>/<html>/<body>, for a host that adds its own
(a claude.ai artifact published with its files beside it). An item {"heading": "…", "text": "…"} starts a section.
Each card shows: the GIF playing on a light / dark / checker ground, frames, size, per-frame timing, loop
flag, file size, a frame scrubber (play/pause, step, slider) drawn from the spritesheet, and the notes.
"""
import argparse, base64, html, json, mimetypes, os
from PIL import Image, ImageSequence

CSS = r"""
:root{--bg:#f3f1f6;--panel:#ffffff;--fg:#1d1a24;--muted:#5f5970;--line:#ddd8e6;--accent:#4f8f2f;--glow:#7dff7a;
--ok:#2f7d32;--warn:#a26a00;--bad:#b3261e;--f-display:"Fraunces",Georgia,serif;--f-body:"Atkinson Hyperlegible",system-ui,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15131b;--panel:#1f1c27;--fg:#ece8f4;--muted:#a69fb8;--line:#332e3f;--accent:#9be070;--ok:#79c67c;--warn:#e0b450;--bad:#f08a80;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#15131b;--panel:#1f1c27;--fg:#ece8f4;--muted:#a69fb8;--line:#332e3f;--accent:#9be070;--ok:#79c67c;--warn:#e0b450;--bad:#f08a80;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font:16px/1.55 var(--f-body)}
.wrap{max-width:1120px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}
h1{font:600 clamp(28px,4vw,40px)/1.1 var(--f-display);margin:0;text-wrap:balance}
h2{font:600 22px/1.2 var(--f-display);margin:0;text-wrap:balance}
.intro{max-width:68ch;color:var(--muted);margin:6px 0 0}
.grounds{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:14px;color:var(--muted)}
.grounds button,.ctl button{font:600 13px var(--f-body);padding:6px 12px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--fg);cursor:pointer}
.grounds button[aria-pressed="true"]{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:24px}
@media (max-width:760px){.card{grid-template-columns:minmax(0,1fr)}}
.stage{border-radius:10px;aspect-ratio:1;display:grid;place-items:center;overflow:hidden;max-width:100%}
.stage img{width:100%;height:100%;object-fit:contain;image-rendering:auto}
body[data-ground="light"] .stage,body[data-ground="light"] .scrub canvas{background:#f7f7f2}
body[data-ground="dark"] .stage,body[data-ground="dark"] .scrub canvas{background:#1b1820}
body[data-ground="checker"] .stage,body[data-ground="checker"] .scrub canvas{background:repeating-conic-gradient(#cfcfd6 0 25%,#f2f2f5 0 50%) 0 0/20px 20px}
.head{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:baseline}
.pill{font:600 12px var(--f-body);letter-spacing:.04em;text-transform:uppercase;padding:3px 9px;border-radius:999px;border:1px solid currentColor}
.v-usable{color:var(--ok)}.v-fixes{color:var(--warn)}.v-not{color:var(--bad)}.v-base{color:var(--muted)}
.purpose{color:var(--muted);margin:4px 0 0;max-width:68ch}
dl{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px 18px;margin:14px 0}
dt{font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
dd{margin:0;font:500 14px var(--f-mono);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.scrub{display:grid;gap:8px;margin-top:6px}
.scrub canvas{max-width:min(100%,300px);height:auto;border-radius:8px;border:1px solid var(--line)}
.ctl{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font:13px var(--f-mono)}
.ctl input[type=range]{flex:1;min-width:120px;accent-color:var(--accent)}
.tabs{display:flex;gap:6px;flex-wrap:wrap}
ul.notes{margin:10px 0 0;padding-left:20px;display:grid;gap:4px;max-width:72ch}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.gallery figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;display:grid;gap:8px}
.gallery .stage{aspect-ratio:auto;min-height:140px}
.gallery figcaption{font-size:14px;color:var(--muted)}
@media (prefers-reduced-motion:reduce){.stage img[data-anim]{visibility:hidden}}
"""

JS = r"""
/* Images are loaded through fetch() and shown from a blob: URL. An artifact host's CSP blocks <img src> on
   its own published files but allows fetch() of them; data: URIs and a page opened from disk (where fetch of
   file:// fails) fall back to the plain URL. */
function asset(u){
  if(!u||/^(data|blob):/.test(u))return Promise.resolve(u);
  return fetch(u).then(function(r){if(!r.ok)throw new Error(r.status);return r.blob()}).then(function(b){return URL.createObjectURL(b)}).catch(function(){return u});
}
[].slice.call(document.querySelectorAll('img[data-src]')).forEach(function(im){asset(im.dataset.src).then(function(u){im.src=u})});
(function(){
  var b=document.body,btns=[].slice.call(document.querySelectorAll('.grounds button'));
  function ground(g){b.dataset.ground=g;btns.forEach(function(x){x.setAttribute('aria-pressed',String(x.dataset.g===g))});try{localStorage.setItem('gifpreview.ground',g)}catch(e){}}
  btns.forEach(function(x){x.onclick=function(){ground(x.dataset.g)}});
  var saved=null;try{saved=localStorage.getItem('gifpreview.ground')}catch(e){}
  ground(saved||'checker');
  var reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  [].slice.call(document.querySelectorAll('.scrub')).forEach(function(s){
    var sheets=JSON.parse(s.dataset.sheets),cv=s.querySelector('canvas'),cx=cv.getContext('2d'),r=s.querySelector('input'),lab=s.querySelector('.fr'),
        play=s.querySelector('.play'),tabs=[].slice.call(s.querySelectorAll('.tabs button')),cur=0,i=0,t=null,img=new Image();
    function draw(){var m=sheets[cur],q=m.rects[i];cx.clearRect(0,0,cv.width,cv.height);if(img.complete&&img.naturalWidth)cx.drawImage(img,q[0],q[1],q[2],q[3],0,0,cv.width,cv.height);
      r.value=i;lab.textContent='frame '+i+' / '+(m.frames-1)+' · '+(m.durationsMs[i]||'?')+' ms';}
    function load(k){cur=k;var m=sheets[k];cv.width=m.frameWidth;cv.height=m.frameHeight;r.max=m.frames-1;i=Math.min(i,m.frames-1);img=new Image();img.onload=draw;asset(m.src).then(function(u){if(cur===k)img.src=u});
      tabs.forEach(function(x,j){x.setAttribute('aria-pressed',String(j===k))});}
    function stop(){clearTimeout(t);t=null;play.textContent='Play'}
    function tick(){i=(i+1)%sheets[cur].frames;draw();t=setTimeout(tick,sheets[cur].durationsMs[i]||100)}
    play.onclick=function(){if(t)stop();else{play.textContent='Pause';tick()}};
    s.querySelector('.prev').onclick=function(){stop();i=(i-1+sheets[cur].frames)%sheets[cur].frames;draw()};
    s.querySelector('.next').onclick=function(){stop();i=(i+1)%sheets[cur].frames;draw()};
    r.oninput=function(){stop();i=+r.value;draw()};
    tabs.forEach(function(x,j){x.onclick=function(){stop();load(j)}});
    load(0);if(!reduced){play.textContent='Pause';tick()}
  });
})();
"""


def src_of(path, out_dir, embed):
    if embed:
        mt = mimetypes.guess_type(path)[0] or "application/octet-stream"
        return "data:%s;base64,%s" % (mt, base64.b64encode(open(path, "rb").read()).decode())
    return os.path.relpath(path, out_dir).replace(os.sep, "/")


def measure(gif):
    im = Image.open(gif)
    durs = [f.info.get("duration") for f in ImageSequence.Iterator(im)]
    return {"frames": len(durs), "size": "%d×%d" % im.size, "durs": durs, "loop": im.info.get("loop"), "bytes": os.path.getsize(gif)}


def kb(n):
    return "%.0f KB" % (n / 1024) if n < 1024 * 1024 else "%.2f MB" % (n / 1024 / 1024)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec"); ap.add_argument("out"); ap.add_argument("--embed", action="store_true")
    ap.add_argument("--no-skeleton", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec)); base = os.path.dirname(os.path.abspath(a.spec)); out_dir = os.path.dirname(os.path.abspath(a.out))
    P = lambda p: os.path.join(base, p)
    e = html.escape
    cards = []
    for it in spec["items"]:
        if "heading" in it:
            cards.append('<section><h2>%s</h2>%s</section>' % (e(it["heading"]), '<p class="intro">%s</p>' % e(it["text"]) if it.get("text") else ""))
            continue
        m = measure(P(it["gif"]))
        durs = sorted(set(m["durs"]))
        sheets = []
        for key, label in (("sheet", "Full frame"), ("game_sheet", "Game cut-out")):
            if it.get(key):
                man = json.load(open(P(it[key])))
                img = os.path.join(os.path.dirname(P(it[key])), man["image"])
                sheets.append({"label": label, "src": src_of(img, out_dir, a.embed), "frames": man["frames"], "frameWidth": man["frameWidth"],
                               "frameHeight": man["frameHeight"], "rects": man["rects"], "durationsMs": man["durationsMs"], "bytes": man["bytes"],
                               "dims": "%d×%d px a frame, %d×%d grid" % (man["frameWidth"], man["frameHeight"], man["cols"], man["rows"])})
        v = it.get("verdict", "")
        vc = {"usable": "v-usable", "usable with fixes": "v-fixes", "not usable": "v-not"}.get(v, "v-base")
        rows = [("Provider", it.get("provider", "?")), ("Model", it.get("model", "?")), ("Frames", m["frames"]),
                ("Size", m["size"]), ("Frame time", " / ".join("%s ms" % d for d in durs)),
                ("Loop", "forever" if m["loop"] == 0 else ("plays once" if m["loop"] is None else "%s extra" % m["loop"])),
                ("GIF file", kb(m["bytes"])), ("Latency", "%s s" % it["latency_s"] if it.get("latency_s") is not None else "?"),
                ("Cost", it.get("cost", "unknown"))]
        rows += [("%s sheet" % s["label"], "%s · %s" % (kb(s["bytes"]), s["dims"])) for s in sheets]
        dl = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (e(str(k)), e(str(v2))) for k, v2 in rows)
        scrub = ""
        if sheets:
            tabs = "".join('<button type="button">%s</button>' % e(s["label"]) for s in sheets) if len(sheets) > 1 else ""
            scrub = ('<div class="scrub" data-sheets="%s"><canvas width="10" height="10" aria-label="Frame viewer"></canvas>'
                     '<div class="ctl"><button type="button" class="prev" aria-label="Previous frame">◀</button><button type="button" class="play">Play</button>'
                     '<button type="button" class="next" aria-label="Next frame">▶</button><input type="range" min="0" max="1" value="0" aria-label="Frame" id="r-%s"><span class="fr"></span></div>'
                     '<div class="tabs">%s</div></div>') % (e(json.dumps(sheets)), e(it["name"]), tabs)
        notes = "".join("<li>%s</li>" % e(n) for n in it.get("notes", []))
        cards.append('<section class="card" id="%s"><div class="stage"><img data-anim data-src="%s" alt="%s, animated"></div><div style="min-width:0">'
                     '<div class="head"><h2>%s</h2>%s</div><p class="purpose">%s</p><dl>%s</dl>%s<ul class="notes">%s</ul></div></section>'
                     % (e(it["name"]), src_of(P(it["gif"]), out_dir, a.embed), e(it.get("title", it["name"])), e(it.get("title", it["name"])),
                        '<span class="pill %s">%s</span>' % (vc, e(v)) if v else "", e(it.get("purpose", "")), dl, scrub, notes))
    gal = ""
    if spec.get("compare"):
        figs = "".join('<figure><div class="stage"><img data-src="%s" alt="%s"></div><figcaption><b>%s</b> %s</figcaption></figure>'
                       % (src_of(P(c["src"]), out_dir, a.embed), e(c["label"]), e(c["label"]), e(c.get("caption", ""))) for c in spec["compare"])
        gal = '<section><h2>%s</h2><div class="gallery" style="margin-top:12px">%s</div></section>' % (e(spec.get("compare_title", "Compare")), figs)
    page = ('<title>%s</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Fraunces:opsz,wght@9..144,600&family=JetBrains+Mono:wght@500&display=swap">\n'
            '<style>%s</style>\n<div class="wrap"><header><h1>%s</h1><p class="intro">%s</p></header>'
            '<div class="grounds" role="group" aria-label="Background"><span>Background:</span><button type="button" data-g="light">Light</button><button type="button" data-g="dark">Dark</button><button type="button" data-g="checker">Checker</button></div>'
            '%s%s</div>\n<script>%s</script>\n') % (e(spec["title"]), CSS, e(spec["title"]), e(spec.get("intro", "")), "".join(cards), gal, JS)
    if not a.embed and not a.no_skeleton:   # a stand-alone file opened from disk needs the document skeleton the artifact host adds
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' + page.replace("<div class=\"wrap\">", "</head><body><div class=\"wrap\">", 1) + "</body></html>"
    else:
        page = '<meta charset="utf-8">\n' + page
    os.makedirs(out_dir, exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(page)
    print("%s  %s  (%d cards)" % (a.out, kb(os.path.getsize(a.out)), sum(1 for c in cards if c.startswith('<section class="card"'))))


if __name__ == "__main__":
    main()
