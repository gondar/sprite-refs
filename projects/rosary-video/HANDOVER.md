# Paciorki światła: handover

A 3:40 music video about the 20 rosary mysteries, for children before First Communion.

- **Hero:** a hazel dormouse (orzesznica). She chases a golden seed of light through the mysteries.
- **Style:** Cartoon Saloon / Secret of Kells. Poor and simple, never churchy.
- **Owner:** marcin.bazydlo@gmail.com. He talks in Polish or English and judges by watching the film.

## Current state (version 5, 2026-10-18)

- **Film page:** https://claude.ai/artifact/3sNBPcuSs3Hf6wgGTQ3zEu. It holds only a video player with 20 beads that jump to each mystery.
  - The video is an asset in the artifact's asset store (20 MiB cap per asset).
  - The page source is `film/film_page.html`; it references the asset by its `/_blob/<id>` URL.
  - To update the video: upload the new MP4 with `Artifact publish asset:true`, put the new id into `SRC` in the page, republish, then delete the old asset.
- **Light video:** `film/paciorki_web_v5.mp4`, 19 MB, 2-pass at 560 kb/s. This is the copy the page plays.
- **Full quality:** about 88 MB, CRF 19. It was sent to the owner but is not in the repo. Re-render it with `process/make_film.sh`.
- **Review status:** every scene passed the scene-reviewer at some point. Several later changes were checked only by the lead on frames, not re-reviewed:
  - v5's new movements (drift, rise, drop);
  - C5 Mary as a figure of light;
  - the bead choreography fixes after the last choreography review.
- **Cost so far:** about $8.6 logged in `process/costs.jsonl`, plus earlier iterations that were not logged.

## Where things are (this folder)

| Path | What |
|---|---|
| `pub/index.html` | **The engine.** One HTML file that draws the whole film on a canvas; `renderTo(ctx, t)` is deterministic. It also contains the old review sections; the artifact no longer uses them. |
| `pub/i5/<id>.json`, `<id>_full.jpg`, `_plate.jpg`, `_fig_<name>.png` | Each scene: the full painting, the plate without people, and the figure layers (bbox and pivot as frame fractions). `<id>` is R1…R5, S1…S5, B1…B5, C1…C5. |
| `pub/i6/fx/<id>.json` | Per-scene behaviour: sway layers, flicker, shimmer, beam, particles, caption, grade, crown, dormouse **route**, plus `exit`, `drift`, `rise`, `drop` (see Engine). |
| `pub/i7/cut/<id>/cut.json` + WebP sheets | Cutout idle gestures per figure. R1's set lives at the top of `i7/cut/`. |
| `pub/i6/dm/dm.json` + sheets | Dormouse actions made with MiniMax-H3, 12 fps. The playful ones carry per-frame `nose`, `paw` and `gaze` contact points. |
| `pub/i7/jump/` | 7 drawn jump poses for the engine's jumps. |
| `pub/intro/`, `pub/outro/` | Rendered intro (hazel nest at night) and outro (dawn, rosary): 30 fps JPG frames plus JSON with seed and rosary positions. |
| `pub/utwor.mp3` | The track: "Triplet Sway", 117.5 BPM, 12/8, bar = 2.0434 s, first downbeat 0.859 s. |
| `process/ART_BIBLE.md` | **The law:** look, poverty, people, Mary's age, dormouse, caption, and the 9 hard fails. Read it first. |
| `process/PIPELINE.md`, `process/PRODUCER.md` | How to make or fix one scene, plus the engine gesture rules. |
| `process/briefs/`, `process/costs.jsonl` | Scene briefs and the log of paid calls. |
| `process/render_scene.js` | 12-frame review sheet for one mystery: `node process/render_scene.js <n> <id>`. |
| `process/render_frames.js`, `process/make_film.sh` | **Film render:** `bash process/make_film.sh out.mp4 30 3 19` (3 Chromium workers, about 6–8 min, then ffmpeg). |
| `tools/` | Review tools: `strip.js`, `trail.js`, `trace.js` + `metric.py` for bead choreography, `sched*.js` + `schedcheck.js` for gesture schedules, `shimseam.py`, `pop.py`, and others. They were written in a scratchpad where `pub/` sat at `../../pub`; fix the `ROOT` path at the top before running. |
| `src/` | Scripts behind the assets: cutout bags (`i7c/cut.py`, `fix6/lid.py`, `work/fix8/fixbag.py`), scene prompts (`scripts/i5/**.txt`), C5/B5 edits, and the new dormouse action tools (`i6n/tools`). |
| `../../skill/rosary-video/` | An older copy of the process docs and engine snapshots. |
| `../../.claude/agents/scene-reviewer.md` | The reviewer agent: Gate A (image), Gate B (layers and idle), Final, and full film. |
| `../../jobs/` | MiniMax prompts and job log. |
| `../../raw/` | The raw H3 clips. |

## Engine in brief (`pub/index.html`)

- **Timeline:**
  - Intro 0–9.03 s.
  - Mystery n starts at 9.033 + n·10.217 s (5 bars each).
  - Outro from 213.37 s to 220.03 s.
  - Each mystery opens with a light transition: bloom, triskele, thread, rose, comet or ripple, in turn.
- **Scene drawing:**
  - The camera slowly zooms the plate.
  - Figures are drawn with strip bending. The strips go into an offscreen buffer, so soft alpha shows no seams.
  - Cutout gestures run on a deterministic schedule. Every gesture ending in `blink` plays twice in 2.6–8.4 s; other gestures shift, they are never deleted.
  - fx are drawn on top, then the grade and the caption.
- **Dormouse** (`dmState`, `playsFor`, `dmContact`, `drawDormouse`):
  - She is in the scene from t = 0 on her `route`.
  - She makes one in-scene jump and lands facing the jump direction.
  - After landing she plays (`PLAYS[n%4]`): bat_reach, sniff_up, look_up_follow or happy_hop.
  - `crouch_takeoff` runs from tE−1, then the exit leap at tE = 8.67 along `exitB`/`exitPt`.
- **Bead** (`mkOrb` inside `mystery`):
  - It enters from the side opposite the previous scene's exit (`exitDirOf`: R, L or U, chosen from her position or `fx.exit`).
  - It circles her nose, hovers in front of her face, and flies ahead to the landing point before a jump.
  - During play it sits at her paw, nose or gaze contact point.
  - It leaves along her exit arc about 0.35 s ahead of her.
  - A centred cosine window of ±0.25 s smooths it, with a lift over her head when it changes sides. Measured with `trace.js` + `metric.py`: no bead jumps over 25 px/frame².
- **Bolder movement from existing layers:**
  - `fx.drift`: per figure, `{from:[dx,dy], to, t0, t1, a0, rot0}` in frame fractions. Used for R1 angel, S1 dove, S4 Moses and Elijah, C1 stone, C4 Mary.
  - `fx.rise`: C2 Jesus, cut out of the plate, rises out of frame.
  - `fx.drop`: C3 flames, cut out of the figures, descend onto heads.
  - `fx.crown.drop`: the C5 crown descends.
- **Intro and outro:**
  - `SEQ` plays the frame sequences.
  - R1's bead starts at `intro.seedLast`.
  - The outro lights the rosary beads in prayer order after `seedSettled`.

## How to work (what made it go well)

1. **Owner feedback → a producer agent per scene.** Give it `process/PRODUCER.md` plus the exact change, a budget, "never edit index.html", "never touch other scenes" and "report evidence paths". The lead owns `index.html`.
2. **Then the scene-reviewer agent.** Use Final, or a narrow gate. At most 2–3 fix rounds. Real hard fails only.
3. **Always look yourself.** Use zoomed crops and `tools/strip.js` (dense thumbnails at absolute times, optional crop). Most bugs were visible only in strips at 0.1–0.15 s steps.
4. **Re-render the film, upload the light MP4 to the artifact, and send the full file** to the owner with SendUserFile.

## Gotchas learned the hard way

- **Image API:** Nano Banana via `api.apiyi.com`; the proxy injects the key.
  - About half the calls return 502. Retry with 40 s waits; failed calls are not billed.
  - `gemini-3-pro-image-preview` is about $0.09; `gemini-3.1-flash-image-preview` is $0.0245.
  - Pass refs at 768 px or less.
- **MiniMax-H3:** see the `sprite-pipeline` skill (first frame = last frame, flat blue ground). Raw GitHub hosting on the branch can be unreachable for about 20 minutes; failed tasks are refunded.
- **Headless Chromium:**
  - `canvas.toBlob` takes about 1.7 s per frame; use `toDataURL`.
  - Navigate with `waitUntil:'domcontentloaded'`, because the Google Fonts stylesheet can hang `load`.
  - Serve HTML with `charset=utf-8` (the page now has `<meta charset>`).
- **Blinks:** must be hard cuts, open or closed only. Cross-faded frames show a ghost iris, which is hard fail 7. `src/work/fix8/fixbag.py` hard-cuts a bag.
- **Image models cannot count beads:** the outro rosary is drawn in code onto the frames (5 decades, pendant, cross).
- **Containers restart:** keep everything important in this repo, not in /tmp.

## Open items / ideas

- **Mary's age** (owner decision pending): she is the R1 girl in the Joyful mysteries and in her 50s in B5. Ask whether S2 (Kana) and C3 (Pentecost) should also show her older. C4 is a young dormition with eyes closed; C5 is a figure of light, about 50.
- **v5 not reviewed:** run a scene-reviewer full-film pass on it, covering the drift, rise and drop movements and C5.
- **Room for more motion** from existing layers if the owner asks for even bolder movement:
  - B4: Jesus and Simon could advance slightly; needs care, no legs move.
  - S3: the boat.
  - R4: Simeon lifting the child.
- **Known minor issues:**
  - The outro rosary is small in frame.
  - The intro dormouse holds mid-air for about 2 s under the R1 transition.
  - In S5 the exit hop passes behind the backs of the front apostles.
  - In C4 the old man's closed far eye is a shaded lid.
- **Artifact:** private to the owner; sharing is done from the page's Share menu.
