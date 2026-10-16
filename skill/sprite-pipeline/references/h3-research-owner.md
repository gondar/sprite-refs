# MiniMax-H3 for animation — the owner's research, distilled (2026-10-16)

The owner's long report on H3 for temporally consistent sprite animation, cut down to what applies to OUR route (the
hosted H3 API through APIYI: `model, content, resolution, duration, ratio` only). Claims are the report's and were not
re-verified from here (its sources were not reachable); the ones we tested are marked.

## Applies to the hosted route

- **Treat H3 as a motion synthesiser, not a sprite generator.** Conditioning (pictures, keyframes, motion video) does
  the consistency work; the prompt only says what moves; deterministic tools do the rest (key/matte, register, select
  phases, pack). Same conclusion as our v3 round.
- **Prompt invariants as positive states** ("the camera stays locked off; framing, scale and lighting never change"),
  never as a "no …" list: the released H3 is guidance-distilled, there is no negative-prompt branch. Matches the v3
  prompt that worked.
- **First/last-frame interpolation wants a single continuous shot** and a description of the path between the
  endpoints — no cuts, no camera moves.
- **Identical first and last frames can damp the motion** (the model "solves" the loop by barely moving). Fits our
  v3 observation: four movements asked, two delivered. Remedy: a third, intermediate pose. Hosted H3 pins only the
  two ends, so we chain clips through a drawn peak (TESTED 2026-10-16, see findings).
- **Reference mode has its own grammar**: `subject_definitions` (`<Subject N>` = a character, a backdrop, a prop, a
  pose…), `summary`, `retention_analysis` with `fully_preserved` / `weak_reference` per subject, `detailed_description`
  with `[Shot 1]`, and the sound fields. One role per reference: "appearance from `<Picture 1>`, motion from
  `<Video 1>`". Our failed reference-mode clips never used it (TESTED 2026-10-16, see findings).
- **Plain background, alpha in post** — H3 has no transparency output. Our `lock.py` goes further than the report's
  generic video matting: with the exact source picture in hand, every non-moving pixel is copied from it.
- **Select phases, never convert all ~96 frames**: pick the frames of one clean cycle; do not interpolate to 48/60 fps
  and cut from that (interpolation invents poses).
- **One action, one viewpoint per clip**; one clip per direction for multi-direction sprites.
- **Evaluate per dimension** (identity, background, flicker, motion, root/scale stability, loop seam) and rank
  candidates instead of rescuing one — `scripts/score.py` covers the ones that matter for a seated idle.

## Needs a LOCAL H3 install — out of scope here

Open weights run through ComfyUI/Diffusers give: a fixed seed (reproducible renders, seed sweeps), 20–25 denoising
steps (the hosted service picks its own), `MiniMaxH3AddGuide` keyframes pinned at ANY frame (three-anchor loops in one
clip), latent noise masks (redraw one region, keep the rest), a Fun ControlNet for pose/depth/edge guidance videos,
and mixing first-frame and reference conditioning (the hosted API forbids it). The report puts the transformer alone
at ~62 GB in bf16, plus a similar text encoder — a dedicated GPU box, not this environment. Worth revisiting only if
the hosted route stops being good enough.

## Dropped as not relevant to our sprites

Pixel-art grid/palette advice (our art is painted), FFmpeg stabilisation and deflicker (the camera holds and the
backdrop no longer drifts in first-frame mode on blue), Robust Video Matting / SAM 2 (we lock against the known
picture), 2K regeneration (sprites are drawn at ~330 px), 8-direction walk planning, Aseprite packing.
