# Scene producer — instructions for one mystery

You produce one mystery scene end-to-end for "Paciorki światła". Read `process/ART_BIBLE.md` and `process/PIPELINE.md` first. They are the law; this file is the how-to.

- **Scratchpad** = `/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad` (S below). All paths are relative to `S/pub/` unless they start with `S/`.
- **Pilot scene to imitate:** R1 (Zwiastowanie).
  - Look at `i5/R1_full.jpg`, `i5/R1.json`, `i6/fx/R1.json`, `i7/cut/cut.json` and `S/review/R1/review_round3.md`.
- **Approved style refs:** `i5/B1_full.jpg`, `i5/C1_full.jpg`, `i5/R1_full.jpg`.
  - Downscale them to 768 px before passing them; refs at 1024 px cause 502 errors.
- **Image API:** Nano Banana via `api.apiyi.com`.
  - The proxy injects the key. Never use the direct Google API.
  - Model: `gemini-3-pro-image-preview` at 1K for full scenes and plate edits; `gemini-3.1-flash-image-preview` for face edits.
  - About half the calls return 502. Retry with 40 s waits, at most 4 tries.
  - Scripts: `S/scripts/gen3.py` (several refs), `S/scripts/gen2.py`, `S/scripts/i5/retry.sh`.
  - Load the Skill `image-generation:image-generation` first.
- **Budget:** about $0.70 per scene including retries. Log every paid call to `S/process/costs.jsonl` as `{"id":..,"what":..,"model":..,"usd":..}`.

## Phase A — brief and full image
1. **Brief:** write `S/process/briefs/<id>.md` (max 15 lines):
   - the event;
   - 2–3 figures and one tender, mid-gesture action each (no pathos);
   - the time of day and palette of the part (ART_BIBLE table);
   - the poor setting props;
   - the single light source;
   - where the dormouse sits at the start, where it jumps once, and where it watches;
   - the caption spot;
   - the unique memory symbol of this mystery.
2. **Style block:** use `S/scripts/i5/v2/style.txt` (the low-key poverty style that produced R1, R2 and S1). For the Glorious mysteries use the C1 look (golden dawn on cool blue-grey).
3. **Generate `i5/<id>_full.jpg`** (16:9, 1376 px).
   - Keep small gaps between figures where possible.
   - Keep an open floor, ground or ledge where the dormouse can sit at the start and later land after one jump.
   - No animals except those the event needs. No text.
4. **Self-check against the hard fails** in ART_BIBLE. Regenerate at most twice.
5. **STOP after Phase A** and report the file. A scene-reviewer runs **Gate A** on it before you continue.

## Phase B — layers, figure idle, living background, route
6. **Layers** (pipeline steps 2–3 of R1; reuse `S/scripts/i5/mask2.py` and `split2.py`, or the S1/B1 scripts):
   - a plate edit that removes the people;
   - a figure mask from |full − plate|;
   - a watershed split into one PNG per figure;
   - a final plate that uses full pixels everywhere except under the figures.
   - Write `i5/<id>_plate.jpg`, `i5/<id>_fig_<name>.png` and `i5/<id>.json`:
     `{"id","full","plate","figs":[{"name","file","bbox":[x,y,w,h],"pivot":[px,py],"motion"}],"land":[x,y],"light":[x,y],"fx":{}}`
     All values are frame fractions; the pivot is a fraction of the figure's own box.
   - Make a check image `S/review/<id>/layers_check.jpg`. Composite vs full must have a mean error < 3.
7. **Figure idle (cutout):**
   - Follow the Skills `idle-animation` and `cutout`. Reuse the R1 renderer: `i7/cut/src/render.py`, `ov.py`, `gestures.json`; also `S/i7w/`.
   - 4–7 small gestures per figure: blink, glance, breath, head tilt, lips or whisper, smile — whatever fits the figure.
   - Every gesture starts and ends on the exact home frame. Static parts stay identical pixels. No ghosting on faces; read zoomed peak frames yourself.
   - Output: `i7/cut/<id>/<figure>_<gesture>.webp`, `i7/cut/<id>/<figure>_home.png` and `i7/cut/<id>/cut.json`, in the same format as `i7/cut/cut.json` but with paths `i7/cut/<id>/...`.
   - Each frame must be the same size as the figure PNG's canvas.
   - Keep WebP quality around 80 and sheets ≤ 4096 px.
8. **Living background:** follow the format of `i6/fx/R1.json`.
   - 3–6 elements: sway layers (`i6/fx/<id>_<name>.png`), flicker, shimmer, beam, disc, particles.
   - Write `i6/fx/<id>_plate_clean.jpg` (inpainted under the sway layers).
   - Use small amplitudes (amp ≤ 0.02, speed 0.2–0.6).
9. **Route** (`i6/fx/<id>.json` → `route`). The NEW rules (owner, iteration 8):
   - **She starts in the scene.** The dormouse is already there at t = 0. She is revealed together with the scene by the light transition; she is not carried in.
   - **The bead finds her.** The golden bead flies continuously from the previous scene and comes down to her head.
   - **Route times:**
     - Times are seconds inside the mystery, from 0 to 8.6.
     - The first point at t = 0 is a calm action: `groom_wonder`, `idle_look` or `stop_sniff`.
     - Include **exactly one** `jump` (A → next point, ~1.5 s) to the watching spot, after about 3.5 s.
     - Optionally one short `run` along the ground.
     - `climb` is allowed only on a real vertical surface.
     - Other actions hold their place.
     - The last point is ≤ 8.6. The engine plays the exit jump (off frame to the upper right) from 8.67.
   - **Placement:**
     - Feet on real surfaces.
     - Never over a face or the key action.
     - Scale is 14% of the frame height.
     - `facing` must point at the mystery while watching.
   - Also set `watch` and `caption` (`pos`: top-left, top-right, bottom-left or bottom-right; on a calm area).
10. **Render:** `cd S && NODE_PATH=$(npm root -g) node process/render_scene.js <n> <id>`. Look at `S/review/<id>/frames.jpg` and `layers.jpg` yourself and fix obvious problems.
11. **STOP after Phase B** and report. A scene-reviewer runs **Gate B / Final**. You will receive its fixes; apply them and re-render. There are at most 2 fix rounds.

**Mystery index n:** R1..R5 = 0..4, S1..S5 = 5..9, B1..B5 = 10..14, C1..C5 = 15..19.

Never edit `pub/index.html`; the lead integrates the engine. Never touch other scenes' files.

## Rules from the first final reviews (B1, C1)
- **Watching means open eyes.** Watch the mystery with `idle_look` facing it. Use `groom_wonder` (eyes closed while grooming) for at most ~1.2 s.
- **Following the bead.** Around 8.0 s she turns toward the bead as it leaves (facing right), then the exit jump plays.
- **Glows** in the engine must not brighten the scene beyond the source image: keep disc and glow radii small and never double a glow that is already painted.
- **Sway amp ≤ 0.02, strictly.**
- **Blink overlays must cover the whole open eye.** That means the iris, the white and the original lid line. Check every blink peak at ×4 zoom: a dark oval, a pale ring or a second lid arc is a hard fail (7).
- **Optional engine controls** in `i6/fx/<id>.json`:
  - `"dormouse":{"tint":{"col":"#rrggbb","a":0..0.5}}` when the dormouse looks too bright for the scene.
  - `"grade":{"mul":"#rrggbb","alpha":0.2–0.4,"top":0–0.3}` to bring an over-bright source image down to the part's palette.
  - `"crown":{"x","y","r"}`, drawn by the engine (C5).
- **Engine reads only some fields.** It reads `caption.pos` and `caption.w`; `caption.x`/`caption.y` and `dormouse.height` are ignored (the height is fixed at 14% of the frame).

## Engine rules for gestures (round 3)
- Every gesture whose name ends in `blink` (e.g. `blink`, `jblink`) is guaranteed to play **twice** in 2.6–8.4 s. Other gestures are moved after the blink, never deleted. Gaps longer than 2.2 s in the window are filled with a short gesture.
- `blink2` plays only at random, but it must still be clean: hard cuts between open and closed eyes, with no cross-fade frames.
- Check: `node review/_tools/schedcheck.js` (it uses `sched4.js`, which mirrors the engine).
