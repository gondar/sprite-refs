#!/usr/bin/env python3
"""Jaś keeping the beat (UkuZiom Short, „Pójdźmy wszyscy do stajenki”, 110 bpm): the star-wave clip, locked, retimed so
every swing's extreme lands on a beat, packed as an 8-column WebP atlas + meta for film.js's beatCell (CFG.shortRun.beat).

  python3 skill/sprite-pipeline/scripts/lock.py LOCK --home refs/ukuziom/jas/jas-home-cut-768.png --at 247,216 \
      raw/20261117-195106-949a77.mp4=wave --pose-s 4.45 --cell 766,766 --pivot 382.5,706 --fig 491 --step 1 --webp 0 --reach 200
  python3 scripts/jas_beat_build.py LOCK OUT_DIR [--plate plate-town.webp] [--raw raw/<clip>.mp4] [--per-beat 0 --cols 12]
  (the Short's atlas since 2026-11-17: --per-beat 0 --cols 12, every source frame once)

Retime: the six staff extremes (star's x on the locked frames, parabola-refined) are anchors; out frame 4 + 9k is extreme k
(9 cells a beat = 16.5 fps at 110 bpm), out 0 = src 0 (home), out 54 = src 106 (home again, = out 0). Between anchors the
source frame is linear in time and taken whole (nearest frame, never blended: a blend ghosts the staff).

--per-beat 0 (2026-11-17, the animation review: 9 cells a beat played at 30 fps held cells 1 and 2 frames alternately, and
the nearest-frame retime doubled one cell and skipped two at another): every source frame once, in order, nothing
retimed — cell k = source frame k, the last frame (= the first, home) dropped, so the atlas is the clip's own 24 fps
motion (~17.7 cells a beat) and film.js maps film frames to cells. accents: each extreme's nearest whole frame. The meta
also carries each cell's drawn box (vis) and its star's centre (star, cell px), for the film's even stepping."""
import argparse, glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BPM = 110.0; SPB = 60.0 / BPM; PER_BEAT = 9; FPS = PER_BEAT / SPB   # 16.5
ap = argparse.ArgumentParser(); ap.add_argument("lock"); ap.add_argument("out")
ap.add_argument("--plate"); ap.add_argument("--raw"); ap.add_argument("--per-beat", type=int, default=9); ap.add_argument("--cols", type=int, default=8)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

# --- frames from lock.py's atlas
M = json.load(open(os.path.join(a.lock, "atlas.json"))); CW, CH = M["cell"]; PX, PY = M["pivot"]; cols = M["cols"]
AT = Image.open(os.path.join(a.lock, "atlas.png")).convert("RGBA"); N = M["gestures"][0]["frames"]
src = [AT.crop(((i % cols) * CW, (i // cols) * CH, (i % cols + 1) * CW, (i // cols + 1) * CH)) for i in range(N)]

# --- accents: the star's x (alpha over the top of the cell), its extremes refined on a parabola
sx = []
for f in src:
    al = np.asarray(f)[..., 3] > 128; ys, xs = np.nonzero(al[:330]); sx.append(xs.mean())
sx = np.array(sx); ext = []
for i in range(1, N - 1):
    if (sx[i] >= sx[i - 1] and sx[i] > sx[i + 1]) or (sx[i] <= sx[i - 1] and sx[i] < sx[i + 1]):
        y0, y1, y2 = sx[i - 1:i + 2]; den = y0 - 2 * y1 + y2
        ext.append((i + (0.5 * (y0 - y2) / den if den else 0), "R" if y1 > sx[0] else "L", y1 - sx[0]))
ext = [e for e in ext if abs(e[2]) > 20]
assert len(ext) == 6, ext
B = len(ext); PER_BEAT = a.per_beat
if PER_BEAT:
    FPS = PER_BEAT / SPB; n = B * PER_BEAT; acc = [4 + PER_BEAT * k for k in range(B)]
    anc_o = [0] + acc + [n]; anc_s = [0] + [e[0] for e in ext] + [N - 1]
    pick = [int(round(np.interp(o, anc_o, anc_s))) for o in range(n)]
else:   # every source frame once; the last one is the first (home) again
    n = N - 1; FPS = 24.0; pick = list(range(n))
    # each extreme's whole frame: of the two around the refined vertex, the one further out (the staff's turn)
    acc = [max((int(np.floor(e[0])), int(np.ceil(e[0]))), key=lambda i: (sx[i] - sx[0]) * (1 if e[1] == "R" else -1)) for e in ext]
print("extremes (src):", [(round(e[0], 2), e[1], round(e[2], 1)) for e in ext])
print("gaps:", np.round(np.diff([e[0] for e in ext]), 2), "wrap", round(N - 1 - ext[-1][0] + ext[0][0], 2))
print("picked src frames:", pick)
cells = [src[i] for i in pick]

# --- crop to what the loop covers, despill the edge
box = None
for c in cells:
    b = c.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
x0, y0, x1, y1 = box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4; cw, ch = x1 - x0, y1 - y0
def despill(im):   # where alpha < 250, green capped at max(red, blue) (the Short's green rim, 2026-11-16)
    p = np.asarray(im).copy(); al = p[..., 3]; e = (al > 0) & (al < 250)
    p[..., 1] = np.where(e, np.minimum(p[..., 1], np.maximum(p[..., 0], p[..., 2])), p[..., 1]); return Image.fromarray(p, "RGBA")
def despeck(im):   # the key leaves faint specks (alpha <= ~32) in the reach zone round the star: keep the figure's own
    from scipy import ndimage as ndi   # island and any island with real opacity, clear the rest
    # islands judged on alpha > 16 (they touch the figure only through alpha 1-8 haze); the figure's soft edge is kept as
    # a 3 px band round what survives
    p = np.asarray(im).copy(); lab, k = ndi.label(p[..., 3] > 16, structure=np.ones((3, 3)))
    if k > 1:
        idx = np.arange(1, k + 1); sz = ndi.sum(np.ones(lab.shape), lab, idx); mx = ndi.maximum(p[..., 3], lab, idx)
        keep = np.zeros(k + 1, bool); keep[1:] = (mx > 64); keep[1 + int(np.argmax(sz))] = True
        band = ndi.binary_dilation(keep[lab] & (lab > 0), iterations=3)
        p[~band] = 0
    return Image.fromarray(p, "RGBA")
cells = [despeck(despill(c.crop((x0, y0, x1, y1)))) for c in cells]
COLS = a.cols; rows = (n + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * cw, rows * ch), (0, 0, 0, 0))
for j, c in enumerate(cells): sheet.paste(c, ((j % COLS) * cw, (j // COLS) * ch))
sheet.save(os.path.join(a.out, "jas-beat.webp"), "WEBP", quality=82, method=6, alpha_quality=90)
sheet.save(os.path.join(a.out, "_atlas-lossless.png"))
piv = [round(PX - x0, 1), round(PY - y0, 1)]
def star_xy(cs):   # the star's centre in each cell (its yellow core over the top 330 px), cell px
    out = []
    for c in cs:
        p = np.asarray(c); m = (p[..., 3] > 128) & (p[..., 0] > 235) & (p[..., 1] > 200) & (p[..., 2] < 170); m[330:] = False
        ys, xs = np.nonzero(m); out.append([round(float(xs.mean()), 1), round(float(ys.mean()), 1)])
    return out
meta = {"n": n, "fps": round(FPS, 3), "cols": COLS, "cell": [cw, ch], "pivot": piv, "fig": M.get("fig", 491),
        "beats": acc, "accents": acc, "period": B, "bpm": BPM,
        "sides": [e[1] for e in ext],
        "src": "gondar/sprite-refs raw/20261117-195106-949a77.mp4 (MiniMax-H3, first = last frame = jas-home-green.png, lock.py, " + ("retimed" if PER_BEAT else "every frame, not retimed") + " by scripts/jas_beat_build.py)",
        "vis": [list(map(int, c.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())) for c in cells],
        "star": star_xy(cells), "per_beat": PER_BEAT or round(n / B, 2),
        "note": "frame 0 is the home frame; beats[k] (= accents[k]) is the staff at its k-th extreme (sides[k]: L/R as seen), to be "
                "played on beat k of every period; " + ("between two accents the cells run evenly (film.js beatCell). %d cells a beat = fps at 110 bpm." % PER_BEAT if PER_BEAT else
                "every cell is one whole source frame (24 fps), in order: film.js steps a cell a film frame, its skips and holds on the slowest cells (star: each cell's star centre)")}
json.dump(meta, open(os.path.join(a.out, "jas-beat.json"), "w"), indent=1)

# --- checks: body height (hat to sole, columns the staff and star never reach), seams, edge spill
def body_h(im):
    al = np.asarray(im)[..., 3] > 128; c0 = int(round(PX - x0 - 93)); r = np.nonzero(al[:, c0:c0 + 60].any(1))[0]; return r.max() - r.min() + 1
def full_h(im):
    al = np.asarray(im)[..., 3] > 128; r = np.nonzero(al.any(1))[0]; return r.max() - r.min() + 1
hb = np.array([body_h(c) for c in cells]); hf = np.array([full_h(c) for c in cells])
pm = lambda im: (lambda f: np.dstack([f[..., :3] * f[..., 3:4] / 255, f[..., 3:4]]))(np.asarray(im, dtype=float))
st = [pm(c) for c in cells]; dd = [np.abs(st[(j + 1) % n] - st[j]).mean() for j in range(n)]
home = np.asarray(src[0], dtype=float)[y0:y1, x0:x1]
p = np.asarray(sheet); edge = (p[..., 3] > 0) & (p[..., 3] < 250)
green = (p[..., 1].astype(int) > p[..., 0].astype(int) + 8) & (p[..., 1].astype(int) > p[..., 2].astype(int) + 8) & edge
chk = {"body_height_home": int(hb[0]), "body_height_max_dev_pct": round(100 * float(np.abs(hb - hb[0]).max()) / hb[0], 2),
       "full_height_home": int(hf[0]), "full_height_range": [int(hf.min()), int(hf.max())],
       "frame0_vs_home_mean_abs": round(float(np.abs(np.asarray(cells[0], dtype=float) - np.asarray(despill(src[0].crop((x0, y0, x1, y1))), dtype=float)).mean()), 3),
       "frame_to_frame_median": round(float(np.median(dd)), 2), "frame_to_frame_max": round(float(max(dd)), 2),
       "loop_seam_last_to_first": round(float(dd[-1]), 2), "edge_green_px_pct": round(100 * green.sum() / max(1, edge.sum()), 2),
       "atlas_px": list(sheet.size), "atlas_kb": round(os.path.getsize(os.path.join(a.out, "jas-beat.webp")) / 1024)}
print(json.dumps(chk, indent=1)); json.dump({"checks": chk, "pick": pick, "extremes": [[round(e[0], 2), e[1], round(float(e[2]), 1)] for e in ext]},
                                          open(os.path.join(a.out, "_checks.json"), "w"), indent=1)
# score.py's format (one gesture: the whole loop)
json.dump({"cell": [cw, ch], "cols": COLS, "gestures": [{"name": "beat", "at": 0, "frames": n}]}, open(os.path.join(a.out, "_atlas-lossless.json"), "w"))

# --- contact sheet: every cell on night blue, number, accent marked
try: FT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
except Exception: FT = ImageFont.load_default()
s = 0.5; tw, th = int(cw * s), int(ch * s); cs = Image.new("RGB", (COLS * tw, rows * (th + 30)), (22, 26, 52)); d = ImageDraw.Draw(cs)
for j, c in enumerate(cells):
    x, y = (j % COLS) * tw, (j // COLS) * (th + 30)
    if j in acc: d.rectangle([x + 2, y + 2, x + tw - 3, y + th + 27], outline=(255, 200, 60), width=3)
    bg = Image.new("RGBA", (tw, th), (22, 26, 52, 255)); bg.alpha_composite(c.resize((tw, th), Image.LANCZOS)); cs.paste(bg.convert("RGB"), (x, y))
    lab = f"{j}" + (f"  beat {acc.index(j) + 1} {ext[acc.index(j)][1]}" if j in acc else (" home" if j == 0 else ""))
    d.text((x + 8, y + th + 3), lab, fill=(255, 220, 120) if j in acc else (200, 205, 230), font=FT)
cs.save(os.path.join(a.out, "jas-beat-contact.png"))

# --- preview over the night town: 1080x1920 (the Short), Jaś 650 px tall, film.js's own beatCell, 8 fps + 30 fps
def beat_cell(t, beats, accents, n):
    A = len(accents); k = -1
    for i, b in enumerate(beats):
        if b <= t + 1e-9: k = i
        else: break
    dt = beats[1] - beats[0]
    if k < 0:
        m = int(np.ceil((beats[0] - t) / dt - 1e-9)); k = -m; b0 = beats[0] - m * dt; b1 = b0 + dt
    else:
        b0 = beats[k]; b1 = beats[k + 1] if k + 1 < len(beats) else b0 + dt
    j = k % A; aa = accents[j]; z = accents[j + 1] if j + 1 < A else accents[0] + n
    if z <= aa: z += n
    f = max(0.0, min(1.0, (t - b0) / (b1 - b0))); return (aa + int(np.floor((z - aa) * f + 1e-6))) % n
if a.plate:
    W, H = 1080, 1920; pl = Image.open(a.plate).convert("RGB"); sc = H / pl.size[1]
    pl = pl.resize((int(pl.size[0] * sc), H), Image.LANCZOS); cx = int(pl.size[0] * 0.40); pl = pl.crop((cx - W // 2, 0, cx + W // 2, H))
    k = 650.0 / M.get("fig", 491); big = [c.resize((int(cw * k), int(ch * k)), Image.LANCZOS) for c in cells]
    fx, fy = W // 2 - piv[0] * k, 1780 - piv[1] * k
    T0 = 0.6; DUR = T0 + SPB * B * 3; beats = [T0 + i * SPB for i in range(int((DUR - T0) / SPB) + 2)]
    for fps, tag in ((8, "8fps"), (30, "30fps")):
        fd = os.path.join(a.out, "_pv" + tag); os.makedirs(fd, exist_ok=True)
        for q in range(int(DUR * fps)):
            t = q / fps; im = pl.copy().convert("RGBA"); im.alpha_composite(big[beat_cell(t, beats, acc, n)], (int(round(fx)), int(round(fy))))
            dd2 = ImageDraw.Draw(im); near = min(abs(t - b) for b in beats)
            on = near < 0.5 / fps + 1e-6 and any(t >= b - 0.5 / fps for b in beats)
            for i in range(4):   # the bar's four beats as dots; the one sounding lights
                bi = int(np.floor((t - T0) / SPB + 0.5 / (fps * SPB))) if t >= T0 - 0.5 / fps else -1
                lit = bi >= 0 and bi % 4 == i and on
                dd2.ellipse([W // 2 - 105 + i * 60, 1840, W // 2 - 75 + i * 60, 1870], fill=(255, 210, 80) if lit else (60, 64, 90))
            im.convert("RGB").save(os.path.join(fd, f"{q:04d}.png"))
        sr = 44100; wav = np.zeros(int(DUR * sr) + sr // 10)
        for i, b in enumerate(beats):
            if b < DUR:
                s0 = int(b * sr); L = int(0.04 * sr); tt = np.arange(L) / sr
                wav[s0:s0 + L] += np.sin(2 * np.pi * (1500 if i % 4 == 0 else 1000) * tt) * np.exp(-tt / 0.008) * 0.6
        import wave
        with wave.open(os.path.join(a.out, "_click.wav"), "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((wav * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(fd, "%04d.png"), "-i", os.path.join(a.out, "_click.wav"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest",
                        os.path.join(a.out, f"jas-beat-preview-{tag}.mp4")], check=True)
        if fps == 8:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "8", "-i", os.path.join(fd, "%04d.png"), "-vf",
                            "scale=540:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer",
                            "-loop", "0", os.path.join(a.out, "jas-beat-preview-8fps.gif")], check=True)
if a.raw:
    import shutil; base = os.path.splitext(os.path.basename(a.raw))[0]; shutil.copy(a.raw, os.path.join(a.out, base + ".mp4"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.raw, "-vf", "select=eq(n\\,0)", "-frames:v", "1", os.path.join(a.out, base + "-first.png")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.2", "-i", a.raw, "-update", "1", "-q:v", "1", os.path.join(a.out, base + "-last.png")], check=True)
