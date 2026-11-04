"""Builds the single-file review page: the hybrid bag next to the cutout-only bag, buttons per gesture, frame strips,
peak-vs-raw frames and the rejected clips."""
import base64, io, json, os, re
from PIL import Image
SP = '/tmp/claude-0/-home-user/0228c9b6-969d-5255-8ea4-a930b937b60f/scratchpad'
MG = '/home/user/MusicGames/.claude/worktrees/agent-a0cb8bfd258c202c9/ukulele-warmup/'


def durl(path=None, im=None, fmt='WEBP', q=80, w=None):
    if path and path.endswith('.webp') and im is None and w is None:
        return 'data:image/webp;base64,' + base64.b64encode(open(path, 'rb').read()).decode()
    im = im or Image.open(path)
    if w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, quality=q); return f'data:image/{fmt.lower()};base64,' + base64.b64encode(b.getvalue()).decode()


js = open(MG + 'phone.js').read()
blk = js[js.index('var IDLE = {'):js.index('var IDLE_REST')]
# the manifest straight from the player (JS object literal -> JSON)
lit = blk[blk.index('proste:') + len('proste:'):blk.rindex('}')].strip()
lit = re.sub(r'^\s*//.*$', '', lit, flags=re.M)
lit = re.sub(r'([{,]\s*)([a-zA-Z_]+):', r'\1"\2":', lit)
M = json.loads(lit)
M['src'] = durl(MG + 'art/jungle/monkey-idle.webp')
for sh in M['sheets']: sh['src'] = durl(MG + sh['src'])
OLD = {"wave": 1, "blink": 3, "tail": 2, "happy": 2}            # PR #391's cutout-only bag
home = durl(MG + 'art/jungle/monkey.webp'); plate = durl(MG + 'art/jungle/bicia-proste.webp', w=700, q=78)
peaks = {g: durl(f'{SP}/revF/peak-{g}.png', w=900, q=82) for g in ('scratch', 'hop', 'cheer')}
peaks.update({g: durl(f'{SP}/revW/peak-{g}.png', w=1100, q=82) for g in ('flip', 'reach', 'play')})
rej = {k: durl(f'{SP}/{f}', w=1400, q=78) for k, f in [('B', 'sheetB.png'), ('Aclap', 'v2.png'), ('A', 'sheetA.png'), ('B2', 'sheetB2.png'), ('C', 'sheetC.png'), ('S1', 'sheetS1.png'), ('S2', 'sheetS2.png'), ('R', 'sheetR.png'), ('P', 'sheetP.png'), ('Bk', 'sheetBk.png'), ('UK', 'ukepk.png')]}
cost = 1.25

html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kiwajka Hybrid Idle</title>
<style>
:root{--bg:#f7f1e6;--ink:#3b2a1a;--muted:#7a6650;--card:#fffaf0;--line:#e3d5bd;--accent:#c4501a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1d1813;--ink:#f1e6d4;--muted:#b8a58a;--card:#2a231b;--line:#3e3427;--accent:#f08a4b}}
:root[data-theme="dark"]{--bg:#1d1813;--ink:#f1e6d4;--muted:#b8a58a;--card:#2a231b;--line:#3e3427;--accent:#f08a4b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:32px 0 8px}
p{margin:6px 0;color:var(--muted)}.row{display:flex;flex-wrap:wrap;gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;flex:1 1 280px;min-width:0}
.card h3{margin:0 0 8px;font-size:15px}.stage{position:relative;height:300px;border-radius:10px;overflow:hidden;background:#f3b54a}
.stage.small{height:190px}
.stage .plate{position:absolute;inset:0;background:url(PLATE) 62% 100%/cover no-repeat}
.fig{position:absolute;left:6%;bottom:10px;height:200px;aspect-ratio:230/256;background:url(HOME) 0 0/100% 100% no-repeat}
.small .fig{height:150px;left:22px}.stage.small{max-width:400px}
.fig i{position:absolute;display:block;background-repeat:no-repeat}
.lab{font:600 13px system-ui;color:var(--muted);margin-top:6px;min-height:1.4em}.btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
button{font:600 14px system-ui;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:999px;padding:6px 14px;cursor:pointer}
button:hover{border-color:var(--accent)}button.sig{border-color:var(--accent)}
.strip{display:flex;gap:4px;overflow-x:auto;padding:4px 0}
.strip .cell{flex:none;width:92px;height:96px;border-radius:8px;background-color:#c9d4e6;background-repeat:no-repeat}
.pk img,.rj img{width:100%;border-radius:10px;display:block}
small{color:var(--muted)}.tag{display:inline-block;font:700 11px system-ui;padding:1px 7px;border-radius:999px;background:var(--accent);color:#fff;margin-left:6px;vertical-align:2px}
.tally{font:13px ui-monospace,monospace;color:var(--muted)}
</style></head><body><main>
<h1>Małpka Kiwajka, waiting — with real moves</h1>
<p>„Proste bicia” on a phone. Left: the new hybrid bag as the play screen plays it — the four cutout gestures plus six
MiniMax-H3 signature moves (scratch, hop, cheer, somersault, reach for the ukulele, strum), rarer, never two signature moves
running. The level screen (the monkey in the ring's middle) plays all but the somersault and the ukulele: there is no room
to her right. Right: the cutout-only bag that ships now.</p>
<div class="row">
 <div class="card"><h3>New: hybrid bag</h3><div class="stage"><div class="plate"></div><div class="fig" id="A"><i></i></div></div><div class="lab" id="Alab">rest</div>
  <div class="btns" id="Abtns"></div><div class="tally" id="Atally"></div></div>
 <div class="card"><h3>Before: cutout-only bag</h3><div class="stage"><div class="plate"></div><div class="fig" id="B"><i></i></div></div><div class="lab" id="Blab">rest</div>
  <div class="btns" id="Bbtns"></div><div class="tally" id="Btally"></div></div>
</div>
<h2>At game size</h2><p>The play screen's bottom row draws her about 150 px tall.</p>
<div class="row"><div class="card"><div class="stage small"><div class="plate"></div><div class="fig" id="C"><i></i></div></div><div class="lab" id="Clab">rest</div><div class="btns" id="Cbtns"></div></div></div>
<h2>Every gesture, frame by frame</h2><p>12 fps. Cell 0 is the old still picture; every gesture starts and ends on it. The signature moves come from
their own atlas (a taller cell, so the hop and the raised hands fit) whose cell 0 is the same picture.</p><div id="strips"></div>
<h2>Peak frames next to the raw clip</h2><p>Left: the shipped cell (on blue, 2×). Right: the MiniMax-H3 frame it was cut from, same crop and scale.
Feet and legs are the home picture's own pixels wherever they did not move (static lock).</p>
<div class="row pk"><div class="card"><h3>scratch</h3><img src="PK_scratch" alt="scratch peak"></div></div>
<div class="row pk"><div class="card"><h3>hop (apex)</h3><img src="PK_hop" alt="hop peak"></div></div>
<div class="row pk"><div class="card"><h3>cheer</h3><img src="PK_cheer" alt="cheer peak"></div></div>
<div class="row pk"><div class="card"><h3>somersault (upside down)</h3><img src="PK_flip" alt="somersault peak"></div></div>
<div class="row pk"><div class="card"><h3>reach (picking up the ukulele)</h3><img src="PK_reach" alt="reach peak"></div></div>
<div class="row pk"><div class="card"><h3>strum</h3><img src="PK_play" alt="strum peak"></div></div>
<h2>Clips: 9 submitted, 6 moves kept</h2>
<p>Round 2 (the owner's „fikołek, granie, sięganie po ukulele”) ran on a 1344×768 canvas with the monkey where she stood, so a
somersault or a reach to her right is not cropped. The ukulele moves are chained through one drawn picture (a Nano Banana edit of the
home picture, registered on the legs): home → holding the ukulele (clip R), strumming on that picture (clip P), and the reach
played backwards to put it down.</p>
<div class="row rj"><div class="card"><h3>The drawn ukulele peak (two edits; the left one used)</h3><img src="RJ_UK" alt="ukulele peak"></div></div>
<div class="row rj"><div class="card"><h3>S1 — somersault kept (6 s clip; the first 4.1 s used)</h3><img src="RJ_S1" alt="clip S1"><p>A forward roll to the right, a hop, a cartwheel back to her spot, arms up, home.</p></div></div>
<div class="row rj"><div class="card"><h3>S2 — rejected: the monkey turns into her mirror image</h3><img src="RJ_S2" alt="clip S2"><p>A cartwheel; mid-clip her tail swaps sides and she comes back mirrored — not her.</p></div></div>
<div class="row rj"><div class="card"><h3>R — reach kept (home → holding the ukulele)</h3><img src="RJ_R" alt="clip R"><p>The ukulele fades in on the ground over two frames, keyed purple: those two frames are skipped, so it appears at once.</p></div></div>
<div class="row rj"><div class="card"><h3>P — strum kept (the first 1.9 s, played forth and back)</h3><img src="RJ_P" alt="clip P"></div></div>
<div class="row rj"><div class="card"><h3>B (put down) — rejected: the ukulele stays on the ground to the last frame, then pops away</h3><img src="RJ_Bk" alt="clip B put down"><p>The reach played backwards puts it down instead.</p></div></div>
<h3 style="margin-top:20px">Round 1</h3>
<div class="row rj"><div class="card"><h3>B — rejected: the backdrop repainted</h3><img src="RJ_B" alt="clip B"><p>Hop + two-arm wave. From 0.3 s the flat blue became a painted savanna and the monkey grew — the sound line asked for a „savanna evening ambience”. Re-run as B2 with a neutral sound line.</p></div></div>
<div class="row rj"><div class="card"><h3>A — scratch kept; its clap rejected</h3><img src="RJ_A" alt="clip A"><img src="RJ_Aclap" alt="clip A clap cut" style="margin-top:8px"><p>The clap half turns the body and passes through a sly, half-lidded face — not her.</p></div></div>
<div class="row rj"><div class="card"><h3>B2 — hop kept (the two-arm wave left out: the cutout already waves)</h3><img src="RJ_B2" alt="clip B2"></div></div>
<div class="row rj"><div class="card"><h3>C — cheer kept (the clap left out: small at 150 px, 31 frames)</h3><img src="RJ_C" alt="clip C"></div></div>
<p><small>MiniMax-H3 first = last frame on flat blue #2F6BD8, cut with lock.py, rebased on monkey.webp. COST in API calls (9 clips $1.20 + 2 image edits $0.05; failed submits were not billed). Atlases: moves 2304×2100 (55 cells, KB KB), somersault 4096×1860 (48 cells, 364 KB), ukulele 3144×2170 (52 cells, 429 KB) — the last two load only on the play screen.</small></p>
</main>
<script>
const M = MANIFEST, OLD = OLDW;
// each atlas once, as a blob: URL (a 700 KB data: URL repeated in a hundred inline styles is not reliable)
const blobUrl = (d) => { const b = atob(d.split(",")[1]), u = new Uint8Array(b.length); for (let k = 0; k < b.length; k++) u[k] = b.charCodeAt(k); return URL.createObjectURL(new Blob([u], { type: "image/webp" })); };
M.src = blobUrl(M.src); M.sheets.forEach(s => s.src = blobUrl(s.src));
const sheetOf = (g) => g.sheet ? M.sheets[g.sheet - 1] : M;
function geom(i, S) {
  const b = S.box, rows = Math.ceil(S.count / S.cols);
  i.style.left = (-b[0] / b[2] * 100) + "%"; i.style.top = (-b[1] / b[3] * 100) + "%";
  i.style.width = (S.cell[0] / b[2] * 100) + "%"; i.style.height = (S.cell[1] / b[3] * 100) + "%";
  i.style.backgroundImage = `url(${S.src})`; i.style.backgroundSize = `${S.cols * 100}% ${rows * 100}%`;
}
const pos = (S, c) => { const rows = Math.ceil(S.count / S.cols); return `${(c % S.cols) / (S.cols - 1) * 100}% ${Math.floor(c / S.cols) / (rows - 1) * 100}%`; };
function player(id, gestures) {
  const i = document.querySelector(`#${id} i`), lab = document.getElementById(id + "lab"), tally = document.getElementById(id + "tally"), count = {};
  let st = { g: -1, t0: 0, until: performance.now() + 800, last: -1, lastSig: false, bag: [] }, sheet = -1;
  const show = (S, k, c) => { if (sheet !== k) { sheet = k; geom(i, S); } i.style.backgroundPosition = pos(S, c); };
  show(M, 0, 0); document.getElementById(id).style.backgroundImage = "none";   // as in the game: the atlas replaces the still picture
  function next() {
    for (let k = 0; k < 2; k++) {
      if (!st.bag.length) { gestures.forEach((g, n) => { for (let w = 0; w < g.weight; w++) st.bag.push(n); }); for (let a = st.bag.length - 1; a > 0; a--) { const b = Math.floor(Math.random() * (a + 1)); [st.bag[a], st.bag[b]] = [st.bag[b], st.bag[a]]; } }
      const j = st.bag.findIndex(n => n !== st.last && !(gestures[n].sig && st.lastSig));
      if (j >= 0) return st.bag.splice(j, 1)[0];
      st.bag = [];
    }
    return gestures.findIndex((g, n) => n !== st.last && !g.sig);
  }
  function tick() {
    const t = performance.now();
    if (st.g < 0 && t >= st.until) { st.g = next(); st.t0 = t; }
    if (st.g >= 0) {
      const g = gestures[st.g], f = Math.floor((t - st.t0) / 1000 * M.fps);
      if (f >= g.seq.length) { st.last = st.g; st.lastSig = !!g.sig; st.g = -1; st.until = t + 900 + Math.random() * 2300; show(M, 0, 0); lab.textContent = "rest";
        count[g.name] = (count[g.name] || 0) + 1; if (tally) tally.textContent = "played: " + Object.entries(count).map(([k, v]) => k + " " + v).join(" · "); }
      else { show(sheetOf(g), g.sheet || 0, g.seq[f]); lab.textContent = g.name + (g.sheet ? " (MiniMax)" : ""); }
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  const bt = document.getElementById(id + "btns");
  gestures.forEach((g, n) => { const b = document.createElement("button"); b.textContent = g.name; if (g.sheet) b.className = "sig"; b.onclick = () => { st.g = n; st.t0 = performance.now(); }; bt.appendChild(b); });
}
player("A", M.gestures);
player("B", M.gestures.filter(g => !g.sheet).map(g => ({ ...g, weight: OLD[g.name] })));
player("C", M.gestures);
const S = document.getElementById("strips");
M.gestures.forEach(g => {
  const sh = sheetOf(g), rows = Math.ceil(sh.count / sh.cols);
  const h = document.createElement("h3"); h.innerHTML = g.name + (g.sheet ? '<span class="tag">MiniMax-H3</span>' : '') + ` <small>weight ${g.weight}${g.sig ? ", signature" : ""} · ${g.seq.length} frames</small>`; h.style.cssText = "font-size:15px;margin:14px 0 2px";
  const d = document.createElement("div"); d.className = "strip";
  g.seq.forEach(c => { const e = document.createElement("div"); e.className = "cell"; e.style.backgroundImage = `url(${sh.src})`; e.style.backgroundSize = `${sh.cols * 100}% ${rows * 100}%`; e.style.backgroundPosition = pos(sh, c); e.style.aspectRatio = sh.cell[0] + "/" + sh.cell[1]; e.style.height = "auto"; d.appendChild(e); });
  S.append(h, d);
});
</script></body></html>"""
# plain text first, the data URLs last (a placeholder word can occur inside base64)
html = html.replace('COST', f'${cost:.2f}').replace('KB KB', str(os.path.getsize(MG + 'art/jungle/monkey-moves.webp') // 1024) + ' KB')
html = html.replace('OLDW', json.dumps(OLD)).replace('url(PLATE)', 'url(' + plate + ')').replace('url(HOME)', 'url(' + home + ')').replace('const M = MANIFEST', 'const M = ' + json.dumps(M))
for k, v in peaks.items(): html = html.replace('PK_' + k + '"', v + '"')
for k, v in rej.items(): html = html.replace('RJ_' + k + '"', v + '"')
out = SP + '/kiwajka-hybrid-review.html'; open(out, 'w').write(html); print(out, len(html) // 1024, 'KB')
