---
name: sprite-pipeline
description: Animate a 2D game character — idle, idle gestures, walk, run, jump, sit, turn, wave, nod, cheer — through APIYI. Starts by choosing the method (MiniMax-H3 video, a drawn cycle sheet, a cutout puppet, or no animation at all via asset-sheet), then gives the exact MiniMax-H3 recipe (one pose per second, four per 4 s clip, home pose between) and the scripts that key, cut, align and pack the frames. Use this whenever a character, mascot or unit has to MOVE, an animation "feels repetitive", or a generated video has to become game frames — and before spending money on video. For many STATIC assets (props, icons, items) use the `asset-sheet` skill instead.
---

# Sprite pipeline — animation

Media, the job log, the mannequin library and the source of truth for this skill live in **`gondar/sprite-refs`**
(`skill/sprite-pipeline/`; also the public hosting H3 needs). Clone it and run every script from its root. Only the
finished strip/atlas goes into the game repo, as a fail-open WebP. Evidence for every rule: `references/findings.md`.

## 1. Choose the method first — every time

Ask **what has to move, how much, and how big the file may be**:

| Method | Use when | Cost / size | Not for |
|---|---|---|---|
| **No animation** — `asset-sheet` skill | it never moves (props, icons, items, poses shown one at a time) | ≈ $0.0003–0.0015 per asset | anything that should breathe |
| **Cutout puppet** — `sprite-refs/skill/cutout` (parts map + Nano Banana edits of the reference, `decompose.py`, `cutout.js`) | rigid parts on pivots: bob, sway, blink, wing flap, head tilt, many procedural actions on one small rig | ≈ $0.15–0.25 once; **40–50 KB** for all actions | facial expressions, turning, limbs crossing the face, anything soft. No SKILL.md yet: rigging is by eye |
| **Drawn cycle** — one Nano Banana image, 8 frames on a 4 × 2 grid | a small looping story (dozing owl) where a hand-drawn feel is fine | ≈ $0.025 | smooth motion; it drifts in size (`pack.py --fix-scale`) |
| **MiniMax-H3 video** (§2) | real, organic motion of body AND face in the painted look: idle gestures, nod, cheer, walk, jump | $0.12 per 4 s clip; **MBs** (164 frames ≈ 2 MB WebP) | tiny downloads; a character whose silhouette leaves the reference a lot (the camera reframes) |

A complaint like "it is the same animation, constantly" is a **variety** problem, not a fidelity one: several short
gestures on one shared home frame, mixed at random (§2, `gestures.py`), beat one longer loop.

## 2. MiniMax-H3 — the recipe

**Plan.** ONE pose per second, FOUR poses per 4 s clip, the **home pose at every whole second** (0, 1, 2, 3, 4 s).
8 poses = **2 clips = $0.24**. Not one clip per pose (9 clips, $1.08 — 2026-10-16), not 2 s per pose, not one 8 s clip
(H3 stretches its motion and barely moves). Budget one re-try clip ($0.12): one clip in two or three comes back broken.

**Reference image** (`<Picture 1>`): the character design on flat magenta (#FF00FF; green if the character has
pink/purple), with headroom for raised arms, padded with **the image's own border colour**. Host on jsDelivr without a
version (`https://cdn.jsdelivr.net/gh/gondar/sprite-refs/<path>`); never overwrite a hosted file — new version, new name.

**Motion reference** (`<Video 1>`): for BODY motion (walk, hop, nod, cheer) add a grey mannequin clip from
`refs/mannequins/` — it holds the timing, the framing and the background. FACE gestures (smile, squint, glance) have
no mannequin: reference image only, and expect more drift. No mannequin fits → make one ($0.12, text-to-video, 1:1,
"a plain smooth grey artist's mannequin … flat solid bright green #00FF00 … no floor", per-second timing), strip its
audio, add it to the table below.

**Prompt** — fill this in; every line is there because its absence broke a clip:
```
<Picture 1> is <who>, a 2D game character <pose: sitting on …/standing>.
This clip is FOUR SHORT <subtle idle gestures | actions> for a game, ONE PER SECOND, each one starting and
ending in EXACTLY the pose of <Picture 1>:
0.0–1.0 s, <POSE IN CAPITALS>: <what moves, small>.   … (four lines)
[with a mannequin: "performing exactly the same actions with the same timing as the grey figure in <Video 1>"]
The pose of <Picture 1> is the home pose: he is in it at 0.0, 1.0, 2.0, 3.0 and 4.0 s.
<BODY PLAN IN CAPITALS + the forbidden alternative: "BIPEDAL … never on all fours" / "stays SEATED … never stands">
MOUTH CLOSED IN EVERY FRAME: he never speaks, sings or opens his mouth.        (H3 adds audio and lip-syncs)
<Front|side> view, the whole figure always inside the frame. Never travels, never turns.
Camera: locked static camera, no zoom, no pan, the character centered and the same size throughout.
Style: keep the exact painted look, colours and details of <Picture 1>.
Background: the SAME flat solid magenta #FF00FF as <Picture 1> in every frame: never changes colour, never fades,
never turns purple or lavender. No floor, no ground, no shadow, no props, no particles, no text.
```
Never compare a motion to an object ("as on a treadmill" drew a treadmill). Do not use first+last-frame mode for
keyed sprites (it repaints the background).

**Run** (from the sprite-refs root; both scripts log to `jobs/jobs.jsonl` BEFORE the paid call — check the log
before re-running anything, a resubmit is billed twice):
```
python3 skill/sprite-pipeline/scripts/h3.py submit --tag <char>-<set> --prompt-file jobs/prompts/<char>/<set>.txt \
        --duration 4 --ratio adaptive --ref-image <URL> [--ref-video <mannequin URL>]
python3 skill/sprite-pipeline/scripts/h3.py poll <job_id> --every 15        # 2–7 min; downloads raw/<job_id>.mp4
ffmpeg -i raw/<job>.mp4 -vf "fps=4,scale=200:-1,tile=8x2" -frames:v 1 sheet.png   # LOOK before cutting
```
Tell the person the cost before submitting (H3 is $0.03 × seconds, pre-charged, refunded if the task fails).

**Judge the contact sheet**: (1) background drift — magenta held ~1.5–2 s in every reference-only clip, then went
lavender/teal/green/black; lavender and teal key, **black next to dark stone does not**; (2) reframing — H3 may zoom
in (a hand near the face pulled it in twice) or out on its own; (3) the mouth. Re-try only the broken clip.

**Cut**:
- Gestures on one home frame (idle variety, nods, reactions): **`scripts/gestures.py`** — keys every frame on its
  own border, registers it to the home frame by the part that never moves (`--static 0.72` = the bottom 28 %: legs,
  feet, throne) or by the upper body when the clip is framed too close, clips steam/glow/vignette, finds each cut at
  the dip of the distance-to-home curve near every whole second, crossfades 2 frames into the home frame, packs a
  row-major atlas + JSON + review sheet + a random-mix GIF. Pass `--home <existing strip>.json:0` so the gestures
  meet the character's other animations:
  `gestures.py OUT raw/A.mp4=sigh,glance,look,smile raw/B.mp4=beard,drum,tilt,sway --home sheets/<c>/idle.json:0`
- Actions and cycles (walk, run, jump): `segments.py` (mark cycles `:loop` — it finds a whole stride) then `pack.py`.
- Read the printed curve, not the prompt's clock; a cut flagged "does not come home" needs a look or a re-try.

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

- **Design** once on Nano Banana Pro (`gemini-3-pro-image`, $0.09) with a style reference cut from the target game;
  every later image on Nano Banana (`gemini-3.1-flash-image`, ≈ $0.025) with that design as identity reference
  (`scripts/gen_image.py`). Show the design to the person before animating it.
- **Drawn cycle**: "the SAME character drawn 8 times on a clean 4 × 2 grid, same size, feet on one baseline … no
  text, no numbers, no grid lines", frames numbered with what each does, "frame 8 flows back into frame 1".
  `key.py` → `cut_sheet.py --grid 4x2` → `pack.py --fix-scale`.
- `key.py` (magenta/green/`--key border`), `video_frames.py` (extract + best loop), `pack.py` (align: `feet` for
  idles/walks, `head` for turns, `fixed` for anything that leaves the ground; ONE `--src-scale` for all strips of a
  character), `onion.py` (idle IoU > 0.9), `compare_gif.py`, `build_viewer.py` (review page). Judge at game size.
- GPT image models: only if the style needs them — a non-streamed `gpt-image-2` over 30 s dies with 502 and is
  billed (`--stream 2`).

## Prices and timings (2026-10)

Nano Banana ≈ $0.025 (15 s) · Pro $0.09 (25 s) · H3 4 s $0.12 (text 1.5 min; reference + video 3–7 min; reference
only up to 25 min). Check `https://api.apiyi.com/api/pricing` — they move. Hosts that must be reachable:
`api.apiyi.com`, `cdn.jsdelivr.net`, H3's output storage `*.myqcloud.com`.
