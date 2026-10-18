# One scene, start to finish

This is the production line for each of the 20 mysteries. R1 (Zwiastowanie) is the pilot. Paths are relative to the artifact root, `scratchpad/pub/`. Scripts live in `scratchpad/scripts/` and `scratchpad/process/`.

| # | Step | Who | Output | Gate |
|---|---|---|---|---|
| 0 | **Brief:** event, 2–3 figures and their gesture, time of day and palette, poor setting props, the light source, where the dormouse can land and watch, and the caption spot | lead | `briefs/<id>.md` | the owner's priorities in ART_BIBLE |
| 1 | **Full image:** Nano Banana Pro 1K, style refs B1 + C1 + R1 (768 px), style block `scripts/i5/v2/style.txt` | image agent | `i5/<id>_full.jpg` | the image agent self-checks against the hard fails |
| 2 | **Layers:** a plate edit (people removed), then a figure mask from \|full − plate\|, then a watershed split | image agent | `i5/<id>_plate.jpg`, `i5/<id>_fig_*.png`, `i5/<id>.json` | composite vs full mean error < 3 |
| 3 | **Figure idle:** a cutout bag per figure (blink, glance, lips, tilt, breath), on the figure's own canvas | cutout agent | `i7/cut/<id>_*.webp`, `cut.json` | ends equal home; no ghosting on faces |
| 4 | **Background life:** sway layers, flicker, shimmer, beams, discs, particles; dormouse route, watch spot, caption spot | fx agent | `i6/fx/<id>.json`, `i6/fx/<id>_*.png` | check image |
| 5 | **Integration** in the engine (`index.html`): figure motion presets, route, light descending to the dormouse | lead | page | renders without errors |
| 6 | **Render:** 12 frames per mystery plus the layer view and a contact sheet | `process/render_scene.js` | `review/<id>/frames.jpg` | — |
| 7 | **Review:** the scene-reviewer agent scores against ART_BIBLE and returns PASS / FIX with concrete fixes | reviewer | `review/<id>/review.md` | PASS, or at most 2 fix loops |
| 8 | **Owner review** on the artifact | owner | decision | owner |

## Costs per scene (2026-10 measurements)
- Full image: ~$0.05–0.09.
- Plate edit: ~$0.05.
- Cutout face edits: ~$0.025 each, 4–6 per scene.
- MiniMax: not needed per scene, because the dormouse actions are shared.
- Total: about $0.4–0.7 per scene, plus retries. The APIYI gateway returns 502 about half the time; failed calls are not billed.

## Rules learned the hard way
- **Green-key edits fail** on these painterly scenes (Nano Banana keeps the line art). The difference mask \|full − plate\| works. The final plate uses full pixels everywhere except under the figures.
- **MiniMax:**
  - Use first frame = last frame, a flat blue ground, and a prompt that never names colours.
  - "garden ambience" or "flat lighting" in the prompt made it paint a garden.
  - Hosting from raw.githubusercontent works. jsDelivr `@branch` is rejected.
- **Figures that touch** (an embrace) can only take tiny rotations. Plan small gaps where the story allows.
- **Keep sway amplitudes small.** The edges reveal a smeared plate underneath.

## Rules from review round 1 (R1)
- **Routes start at landing.** Route times are seconds within the mystery. The dormouse lands at `TIN + 0.75 bar` (≈ 3.9 s). The first route point is that landing spot. The last point is ≤ `M − 1.55 s` (≈ 8.67 s); after that the engine plays the exit jump.
- **Only three ways to move.**
  - `jump` (A → next point), drawn from the 7 key poses: crouch, push, arc, land, settle; about 1.5 s.
  - `run` along the ground.
  - `climb`, only on a real vertical surface in the plate.
  - Every other action holds its place. Nothing slides.
- **Light carries her.** During the transition the light carries the dormouse to a point above her landing spot, never over a face. One dormouse and one bead on screen at all times.
- **The bead leaves first.** It leaves her ~0.8 s before her exit jump and flies ahead.
- **Caption timing:** it appears when the scene is revealed and disappears at the exit.
- **Transition masking:** the transition draws the new scene into its own buffer, then masks it. Never mask while drawing, because effects change the compositing mode.
