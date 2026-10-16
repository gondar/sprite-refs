---
name: cutout
description: Make many small idle variations of a character on a FIXED body from its one finished picture — blink, double blink, glance left/right, look up/down, smile, raised brow, frown, sleepy lids, head tilt, nods, sway, breath, shrug, sigh, crown/eye glow pulse and combinations of them — by bending the picture with weight maps (head, torso) and laying overlays cut from single-change Nano Banana edits on top. Static props (a throne, a desk, an instrument) and the legs stay identical pixels in every frame by construction, every gesture starts and ends on the exact rest frame, and a new gesture costs nothing but keyframes (a new face ≈ $0.025). Use it when an idle needs quantity and subtlety, or a video route re-renders the props. Do NOT use it for a limb travelling across the body (the Mountain King's hand-to-beard ghosted and was dropped), a head or body turning, or big actions — those go to MiniMax-H3 via the `sprite-pipeline` skill; the `idle-animation` skill decides the mix of the two.
---

# Cutout — one picture, bent and overlaid

Source of truth: **`gondar/sprite-refs` → `skill/cutout/`** (scripts, this file). Run everything from the sprite-refs
root. Rigs live in `rigs/<char>/`, edits in `refs/cutout/<char>/`, paid calls in `jobs/jobs.jsonl`. Evidence:
`skill/sprite-pipeline/references/findings.md` (Rounds 5–6, C1/C2 owl) and the Mountain King below. Choosing cutout vs
MiniMax vs both: `idle-animation` skill. MiniMax recipe and `score.py`: `sprite-pipeline` skill.

## Why a warp, not rigid pieces
A seated front-view character has no clean joints: the beard covers the neck, the belly the hips, the hands rest on
the throne. Rigid pieces open gaps or show a second outline at every seam ("double back", C2). So the figure is ONE
layer bent by smooth weight maps (skinning, as in Spine/Live2D): seams cannot open, and every pixel with weight 0
(throne, legs, feet, hands) samples itself exactly. Rigid pieces (C2: `decompose.py`, `cutout.js`) are still right
for a character with real joints and parts that move far — a wing that flaps, an arm that waves beside the body, a
tail — where a warp would smear a large motion.

## 1. Edits — one change per edit (Nano Banana flash, `gemini-3.1-flash-image`, ≈ $0.0245, 15 s)
Every edit takes the design picture (flat key colour, magenta here) as `--ref` and asks for ONE change:
```
SPRITE_ROOT=$PWD python3 skill/sprite-pipeline/scripts/gen_image.py --model gemini-3.1-flash-image \
  --ref refs/<char>/<picture>.png --prompt-file refs/cutout/<char>/prompts/blink.txt \
  --out refs/cutout/<char>/blink.png --aspect 1:1 --tag <char>-cut-blink
```
Check `jobs/jobs.jsonl` before any re-run (it logs BEFORE the call; an HTTP 502 may still be billed).
The pattern that worked, verbatim (King, `refs/cutout/king/prompts/`):
> Edit this image: the King closes both eyes calmly (stone eyelids down, the amber glow hidden, just two closed curved
> eyelid lines). Change nothing else at all: the same troll, the same throne, the same pose, the same position and
> size on the canvas, the same lighting, colours and painted style. The background stays perfectly flat magenta #FF00FF.

Same tail for: eyes to the right / LEFT side of the picture ("His head does not turn"), eyes down, eyes UP (brows
raised a little), half-closed sleepy lids, ONE raised brow ("the brow above the eye on the RIGHT side of the picture"),
grumpy furrow, a warm closed-mouth smile ("The mouth stays closed"), fingers lifted ("ONLY the four fingers bend
upward a little at the knuckles … the palm, wrist and thumb stay"). Say sides as "of the picture", never his left.
- **Hidden areas** (what the head/torso uncover): "make the stone troll king invisible and keep the throne EXACTLY as
  it is drawn here — the same outline, the same height … The backrest is LOW and rounded: its top edge stays exactly
  where it is now … paint what was hidden behind him". The first try, "remove the King, keep only the empty throne",
  REDREW the throne taller and different — useless. The fix kept even his hands and legs; fine, only slivers show.
- **Parts map**: "Recolour this exact image as a flat-colour segmentation map … head with face, ears, beard and crown =
  #FF0000, torso = #0000FF, arm on the LEFT of the picture = #FFFF00, RIGHT = #00FFFF, legs and feet = #00FF00, the
  throne = #FFFFFF, background = #000000". Aligned to 1–2 px.
- Flash was enough for all 15 King edits (face edits clean on the first try 9/9); pro ($0.09) only if a face edit
  fails twice. A "do a small change" prompt beats "lift the hand": the first drum edit lifted the whole hand.

## 2. Register, then build the rig
Edits come back at 1024² and shifted ≤ 2 px. Fit each onto the picture (scale, rotation, shift; L1 on the figure, or
on its lower part for edits that change the upper body), and the picture onto the game's existing home frame:
```
python3 skill/cutout/scripts/register.py refs/<char>/<picture>.png --out refs/cutout/<char>/register.json \
        refs/cutout/<char>/{blink,glance,left,up,down,smile}.png refs/cutout/<char>/{throne2,drum2}.png=lower
python3 skill/cutout/scripts/register.py refs/<char>/<picture>.png --home sheets/<char>/<idle>.json:0 \
        --cell 479,444 --pivot 245.6,442.8 --out rigs/<char>/home_fit.json        # King: IoU 0.99
python3 skill/cutout/scripts/build_warp_rig.py rigs/<char>/spec.json rigs/<char>
```
`spec.json` (copy `rigs/king/spec.json`): `ref`, `seg` (parts-map path, its registration, colours), `edits`
(register.json), `under` (the hidden-area edit), `home`, `deformers` (torso: pivot at the hips, `y_full`/`y_zero`
ramp, `arm_falloff` so the hands stay at 0; head: pivot at the chin, grown mask so thin crown spikes stay rigid,
`beard_keep`), `overlays` (per edit: `within` parts, `box`, `thr`, `grow`, `feather`), `glow` (gain, colour test,
boxes around crystals and eyes). It writes `rigs/<char>/`: `base.png` (props + hidden-area fill), `king.png` (the
figure, hard-cut from the picture so rest == picture), `ov_*.png` (only pixels the edit changed, feathered, with
`xy`), `w_head.png`/`w_torso.png` (weights), `rig.json`, `check.png` — look at `check.png` (weights at the hands ≈ 0).

## 3. Gestures = keyframes (`rigs/<char>/gestures.json`) — adding one is free
```
{"name": "curious", "dur": 1.5, "tracks": {"ov.brow": [[0,0],[0.1,0],[0.4,1],[1.05,1],[1.35,0],[1.5,0]],
                                         "head.rot": [[0,0],[0.45,2.5],[1.0,2.5],[1.5,0]]}}
```
Channels: `head|torso.rot` (deg, + clockwise), `.dx .dy` (px of the picture), `.sx .sy`, `ov.<overlay>` alpha;
smoothstep between keys. Rules: 0.8–2 s at 12 fps; every channel at rest on the first and last key (the renderer
also writes the rest frame itself there); subtle and slow (head ≤ 4.5°, torso ≤ 1.3°, shifts ≤ 10 px of a 1331 px
picture); eye/face overlays in 1–2 frames are fine (small, same place); **never crossfade a large part between two
distant positions** — the King's arm-to-beard swap showed a ghost arm and was removed. Combine freely: sigh = breath
+ blink + head drop; drowsy = sleepy lids → blink → head sinks → startle; smiletilt = smile + tilt.

## 4. Render, split, check
```
python3 skill/cutout/scripts/render_gestures.py rigs/<char> review/cutout     # atlas.{png,webp,json}, review.png,
                                                                              # check.json, rest.png, frames/
python3 skill/sprite-pipeline/scripts/pages.py review/cutout/atlas.json review/cutout/pages <char>-cutout   # to ship
python3 skill/sprite-pipeline/scripts/score.py cutout=review/cutout/atlas.json
```
`atlas.json`: `{cell, pivot, fps, cols (=16383 // cell w), rows, gestures:[{name, at, frames, src:"cutout"}]}`.
**Ship with `pages.py`, not `split_atlas.py`**: the full-cell atlas (King: 16286×5328 px, 87 Mpx) and even the
split's single moving-region atlas (~29 Mpx) are over what a phone decodes (iOS Safari refuses > ~16.7 Mpx; headless
Chromium refused the 87 Mpx one). `pages.py` writes one base + pages ≤ 4096 px a side, each cell in a gutter of its
own repeated edge pixels (no hairline when the page is scaled), and checks the rebuild is exact. The game draws the
base, then the cell on a crop layer (MusicGames `fingerpick-warmup/index.html`, `pagedFrame`). Checks: `check.json` — max over frames of mean |RGBA diff| vs frame 0 on the bottom 28 % of the figure (must be 0)
and on the throne back outside the head (< 0.5; the residue is the shoulders covering its edge), seams first/last
vs rest (must be 0). Then LOOK at every gesture's extreme frame at full size, zoomed on head and hands — that is how
the bent crown spikes (blurred head weight) were found. Review page for the owner before anything ships.

## Worked example — Mountain King (2026-10-16)
Round 1: 10 flash edits $0.245 (+ two HTTP 502, $0–0.049), 8 gestures; the beard gesture ghosted. Round 2: 5 face
edits $0.1225, beard dropped, 13 new gestures from the same rig → 20 gestures, 386 frames, cell 479×444.
Throne/legs diff 0.000 in all, seams 0.000, score.py `static 0.05 colour 4.55 (glow, on purpose) seam 0.00 motion 1.83`.
Size: atlas.webp 4.24 MB; split 2.93 MB + 5 KB base (changing rectangle = 33 % of the cell). Owner: "others are brill".

## Known weak spots
- No real 3D: glances are eyes + a small head shift; nothing turns. Hands crossing the body → MiniMax.
- The hidden-area fill is an edit, not the original; keep motion small so only slivers show.
- Finger taps are a swap of two finger positions — reads as a twitch at small sizes.
- Frames are full cells: 20 gestures ≈ 4 MB WebP. Split, fewer frames, or play the rig at runtime (layers + weights +
  gestures.json are all the data a WebGL mesh player needs).
