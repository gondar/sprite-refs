---
name: sprite-pipeline
description: Animate a 2D game character — idle, idle gestures, walk, run, jump, sit, turn, wave, nod, cheer — through APIYI. Starts by choosing the method (MiniMax-H3 video, a drawn cycle sheet, a cutout puppet, or no animation at all via asset-sheet), then gives the MiniMax-H3 recipe that works (first frame = last frame on a flat blue ground, a short motion-only prompt, two movements per 4 s clip, the static lock in lock.py) and the scripts that cut, align, score and pack the frames. For an idle, the idle-animation skill picks between MiniMax, cutout and both. Use this whenever a character, mascot or unit has to MOVE, an animation "feels repetitive", or a generated video has to become game frames — and before spending money on video. For many STATIC assets (props, icons, items) use the `asset-sheet` skill instead.
---

# Sprite pipeline — animation

Media, the job log, the mannequin library and the source of truth for this skill live in **`gondar/sprite-refs`**
(`skill/sprite-pipeline/`; also the public hosting H3 needs). Clone it and run every script from its root. Only the
finished strip/atlas goes into the game repo, as a fail-open WebP. Evidence for every rule: `references/findings.md`.

## 1. Choose the method first — every time

Ask **what has to move, how much, and how big the file may be**. For an IDLE (a character waiting on screen),
read the `idle-animation` skill first: it decides between MiniMax, cutout and a hybrid of both.

| Method | Use when | Cost / size | Not for |
|---|---|---|---|
| **No animation** — `asset-sheet` skill | it never moves (props, icons, items, poses shown one at a time) | ≈ $0.0003–0.0015 per asset | anything that should breathe |
| **Cutout** — `skill/cutout/SKILL.md` (the picture bent by weight maps + overlays from single-change image edits) | many SMALL variations on a fixed body: blink, glance, smile, tilt, sway, breath, glow, nods | ≈ $0.025 per new face edit, combinations free; static parts identical by construction | a limb travelling across the body (a hand to the beard ghosts), turning, big actions |
| **Drawn cycle** — one Nano Banana image, 8 frames on a 4 × 2 grid | a small looping story (dozing owl) where a hand-drawn feel is fine | ≈ $0.025 | smooth motion; it drifts in size (`pack.py --fix-scale`) |
| **MiniMax-H3 video** (§2) | REAL movement: a hand to the face, a head turn, a sigh with the eyes closing, nod, cheer, walk, jump | $0.12 per 4 s clip = about two movements; MBs | tiny downloads; dozens of variations (the cutout is cheaper per variation) |

## 2. MiniMax-H3 — the recipe that works (2026-10-16, the owner's "perfect")

The two things that ruin a clip are the MODE and the BACKGROUND, not the wording of the motion. Evidence:
`references/findings.md` (Mountain King, four rounds), `references/minimax-research.md` and the owner's own
research, distilled to what applies to the hosted API, in `references/h3-research-owner.md`.

**Mode: first frame = last frame = the same picture.** Not `reference_image`: that is a *subject* reference — the
model imitates the character, reframes, relights and darkens it (frame 0 differed from the picture by 9–10.6 MAE; in
first-frame mode by ~5). Pinning both ends also brings every clip home to the same frame, which is what lets clips
be cut into gestures that play in any order. `h3.py submit --first URL --last URL` (same URL twice).

**Background: flat blue #2F6BD8** (or green #22B24C when the character has blue). Never magenta: a saturated
magenta ground is out of distribution, the model "fixes" it from ~0.5 s on and relights the character with the new
colour — every magenta clip drifted (sky blue, teal with a grassy floor, pale green, black). On blue and on green the
corner colour held to ±3 levels for all 4 s. Prepare the picture once: key the design, clean its fringe, put it on the
flat colour at ~64 % of the height with room above for a raised arm, save it under a NEW name, host on jsDelivr.

**Prompt: ~130 words, only what moves.** Open with `[Static shot]`, one sentence that the camera is locked and the
lighting never changes, then the movements in order ("First … Then … Last …, resting in the starting pose between"),
"He ends exactly in his starting pose", "lips pressed together" (positive, not a list of forbidden mouth actions —
a "breath" still opened the mouth once), "his throne, legs, feet and the plain backdrop stay completely still", and
"Sound: a soft, low cave ambience only" (H3 always makes audio; a voice makes lip-sync). **Never name the background
colour** and never list colours it must not become — the old prompts named exactly the colours it drifted to. No
clock syntax ("0.0–1.0 s"): it is followed loosely. Worked prompts: `sprite-refs/jobs/prompts/mountain-king/v3-first-last-{A,B}.txt`.

**Plan: TWO movements per 4 s clip.** Asked for four, H3 in this mode made two, with one near-rest at ~2 s. So 4
gestures = 2 clips ($0.24); 8 = 4 clips. Cut at the real rests (`--pose-s 2`), never on the clock. Submit the first
clip on blue AND green when the character is new ($0.24) and keep the colour that held.

**A gesture that must reach a specific pose: chain two clips through a DRAWN peak.** Hosted H3 pins only the first
and last frame, and identical ends damp the motion. So draw the peak (a single-change image edit of the picture —
the cutout's edits are exactly this), put it on the same ground in the same framing, and run two clips: home → peak
and peak → home (the second one reversed before `lock.py`, so both start at home). Cut each half with
`lock.py --open-end` (eases into home at the start only), keep the moving spans, and join them; the King's beard
stroke joined with a frame-to-frame change of 0.35 at the peak against a median of 1.1. H3 takes its time — the
moving span was ~3 s per half — so play it at 2× (every 4th source frame at 12 fps). $0.24 per gesture.

**Reference mode is out, even with MiniMax's own grammar.** `subject_definitions` / `retention_analysis` with
`fully_preserved` on the character, the backdrop and the picture (tested 2026-10-16, $0.12) still repainted the
scene from frame 0: backdrop dark navy instead of the picture's blue, frame 0 off the picture by 60 (first-frame mode:
~6). It is a subject reference by design; use it only when nothing has to be locked to the picture.

**Run** (from the sprite-refs root; `h3.py` logs to `jobs/jobs.jsonl` BEFORE the paid call — check it before
re-running anything, a resubmit is billed twice; tell the person the cost first):
```
python3 skill/sprite-pipeline/scripts/h3.py submit --tag <char>-<set> --prompt-file jobs/prompts/<char>/<set>.txt \
        --duration 4 --ratio adaptive --first <URL> --last <URL>
python3 skill/sprite-pipeline/scripts/h3.py poll <job_id> --every 15        # 2–7 min; downloads raw/<job_id>.mp4
ffmpeg -i raw/<job>.mp4 -vf "fps=4,scale=200:-1,tile=8x2" -frames:v 1 sheet.png   # LOOK before cutting
```
Measure before cutting: the corner colour per frame (must not move) and frame 0 against the picture (MAE ≈ 5).

**Cut with the static lock — `scripts/lock.py`**, never by keying whole frames. Only pixels that really move come
from the clip; every other pixel is the picture itself, so a throne, legs and body cannot shimmer or change colour:
```
lock.py OUT --home <clean cut-out>.png --at X,Y --keep <prop mask>.png --pose-s 2 \
        raw/A.mp4=sigh,squint raw/B.mp4=beard,sidelook [--cell 479,444 --pivot X,Y --fig H]
```
- motion is measured against the clip's OWN first frame (against the picture, repaint noise lit up 20k px at rest);
- colour of the moving area is matched to the same area of the clip's first frame, gains capped ±15 % (matching to the
  painted picture gave an orange cast; per-channel gains on a ring gave a purple one);
- outside the outline it keys on how much the ground colour DOMINATES, not on distance (the model casts soft shadows
  on the backdrop; a distance key kept them and the spill clamp turned them teal);
- **`--keep` is a mask of the PROP only** (throne, stand — from the cutout's parts map or painted once): there, pixels
  the clip erases come back from the picture. Applied to the whole outline, it pasted the home crown back where the
  head had just moved away — the King wore two crowns. Elsewhere, the space a moving part leaves is empty.
- **A character with blue in it** (a parrot's wing tips): blue keys the tips away and green keys the body. Use a
  flat RED ground (#D23B2B; held ±3 levels for 4 s, 2026-10-31) and widen the key for it: `--dom 100,35 --spill 100,55`.
  The defaults (60,40 and 25,0) are tuned on blue and turn a yellow chest pale on red (R−G ≈ 40 crosses both);
  red's own ground sits ~155 above the other channels. Worked example: Papuga Konfetka, `refs/ukuziom/`.

**Check, then show** — `scripts/score.py` on the atlas (throne shimmer, colour drift, seams, motion), then
LOOK at each gesture's peak frame at full size, zoomed on the head, next to the raw clip's frame: the score did not see
two crowns. Then a review page for the owner, side by side with what it replaces, before anything goes into a game.

**Pack for phones**: `scripts/pages.py` (one base + pages of the moving region, ≤ 4096 px a side, edge gutters) — a
full-cell atlas of a few hundred frames does not decode on a phone; `scripts/rebase.py` when frames from two sources
must meet on one home frame (idle-animation skill).

**Do not**: `reference_image` mode for a pose that must come home; magenta; a prompt that names colours; a home frame
taken from a different clip or an older strip (two drawings crossfaded = ghosting); `gestures.py` on a first-frame
clip (it keys whole frames — it is for clips with no clean picture behind them, e.g. walk cycles cut by `segments.py`).

**Play** the atlas as a shuffled bag — never the same gesture twice running, 0.4–2.2 s of rest on the home frame
between — and keep beat-locked moves (a nod on the beat) on the beat. Worked example: the Mountain King in
MusicGames `fingerpick-warmup/index.html` (`SPR.idle`, `idleFrame`, `kingListens`) and its test §5a, which checks
every gesture's ends against the home frame with the middles as the positive control.

## Mannequin library (`refs/mannequins/`, 4 s each, audio stripped)

| File | Actions |
|---|---|
| `idle-breath-4s.mp4` | calm breathing idle (side view) |
| `idle-wave-hop-settle-4s.mp4` | idle 0–0.8 · wave 0.8–2.6 · hop 2.8–3.8 · settle |
| `std4-idle-walk-run-jump-4s.mp4` | idle · walk · run · jump, 1 s each |
| `std6-…-sit-stand-4s.mp4`, `std8-…-turn-turnback-4s.mp4` | 6 and 8 actions — at 0.5–0.67 s a pose is a sketch; prefer 1 s |
| `seated-front-idle-nod-cheer-settle-4s.mp4` | seated FRONT view, heavy adult build: idle · nod · fists up · settle (Mountain King) |

## Other routes and scripts

- **Design** once on GPT by default: `gpt-image-2 --quality medium --stream 2` (≈ $0.06, ~35 s; never without
  `--stream` — a non-streamed call over 30 s 502s and is still billed), with a style reference cut from the target
  game. **Fall back to Nano Banana Pro** (`gemini-3-pro-image`, $0.09) when GPT does not get it right: two GPT tries
  with a fixed prompt still miss, or it must match a painted reference (Gemini matched one better; GPT drew shaggy
  fur), or the design needs a size GPT lacks (it only does 1024² / 1536 × 1024 / 1024 × 1536). Say when you switch.
  Every later image on Nano Banana (`gemini-3.1-flash-image`, ≈ $0.025) with that design as identity reference
  (`scripts/gen_image.py`). Show the design to the person before animating it.
- **Drawn cycle**: "the SAME character drawn 8 times on a clean 4 × 2 grid, same size, feet on one baseline … no
  text, no numbers, no grid lines", frames numbered with what each does, "frame 8 flows back into frame 1".
  `key.py` → `cut_sheet.py --grid 4x2` → `pack.py --fix-scale`.
- `key.py` (magenta/green/`--key border`), `video_frames.py` (extract + best loop), `pack.py` (align: `feet` for
  idles/walks, `head` for turns, `fixed` for anything that leaves the ground; ONE `--src-scale` for all strips of a
  character), `onion.py` (idle IoU > 0.9), `compare_gif.py`, `build_viewer.py` (review page). Judge at game size.
- GPT image models: the default for the design (above), always with `--stream 2` — a non-streamed `gpt-image-2`
  over 30 s dies with 502 and is billed. `gpt-image-2` refuses `--background transparent` (`gpt-image-1.5` takes it).

## Prices and timings (2026-10)

Nano Banana ≈ $0.025 (15 s) · Pro $0.09 (25 s) · H3 4 s $0.12 (text 1.5 min; reference + video 3–7 min; reference
only up to 25 min). Check `https://api.apiyi.com/api/pricing` — they move. Hosts that must be reachable:
`api.apiyi.com`, `cdn.jsdelivr.net`, H3's output storage `*.myqcloud.com`.
