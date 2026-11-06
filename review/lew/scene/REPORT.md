# Scene layers — The Lion Sleeps Tonight

All images: gemini-3.1-flash-image via APIYI (gen_image.py, --size 2K --stream 1), job log `/tmp/claude-0/-home-user/b0558c5d-ed4e-5e44-a3ad-976c343aec93/scratchpad/lew/work/jobs/jobs.jsonl`.
Prompts: `/tmp/claude-0/-home-user/b0558c5d-ed4e-5e44-a3ad-976c343aec93/scratchpad/lew/work/prompts/`. Raw outputs: `/tmp/claude-0/-home-user/b0558c5d-ed4e-5e44-a3ad-976c343aec93/scratchpad/lew/work/raw/`. Build scripts: `/tmp/claude-0/-home-user/b0558c5d-ed4e-5e44-a3ad-976c343aec93/scratchpad/lew/tools/` (build_sky.py, key_frame.py, build_fg.py, finalize.py).

## Jobs and cost
| job | tag | result | cost |
|---|---|---|---|
| 20261026-214945-739467 | sky1 (first composition, sun centred — superseded) | ok | 0.0245 |
| 20261026-215039-1e45ce | frame1 | HTTP 502 at 31 s | 0 logged (may be billed 0.0245) |
| 20261026-215123-e93161 | frame1-retry (b.apiyi.com, small JPEG refs) | ok → frame | 0.0245 |
| 20261026-215229-b0a342 | sky1b (horizon higher) | ok → sky-1 | 0.0245 |
| 20261026-215423-19fba7 | sky2 dusk | ok → sky-2 | 0.0245 |
| 20261026-215423-fb7379 / -533328 | sky3 / sky4 (run in parallel) | HTTP 502 | 0 logged (may be billed 2×0.0245) |
| 20261026-215509-60adcb | sky3-retry night | ok → sky-3 | 0.0245 |
| 20261026-215527-989a4a | sky4-retry dawn | ok → sky-4 | 0.0245 |
| 20261026-215716-51e85a | fg1 foliage on magenta | ok → foreground | 0.0245 |
| 20261026-215901-7aed6a | orn1 ornament sheet on magenta | ok → orn-* | 0.0245 |

**Logged cost $0.196; worst case incl. the three 502s $0.27.** Lesson: parallel 2K Gemini calls hit the ~30 s gateway cut; sequential calls with a downscaled ref took 16–18 s.

## How it was built
- **Frame**: generated with arch windows in flat #FF00FF (the model added gold mullions — kept, they look Art Deco). Keyed with key.py (lo 30 / hi 110), downscaled premultiplied to 1920×1080, plus an extra despill inside the window boxes (B ≤ 0.75·G, R ≤ 1.45·G+10) because the mullions had a pink cast. Edges checked at 4× over white and black: a faint warm-brown hairline remains on white, invisible over the sky.
- **Skies**: the frame's windows are small (each ~13% × 26% of the stage) and sit left/right of the marquee, so a single full-stage painting only ever showed empty sky through them. build_sky.py therefore places a *framed view* of the painting into each window (left: sun/moon over the left peak; right: right peak with palms; ~800 px source crop scaled to the window + 60 px feathered margin) over a blurred full painting as hidden filler. Same crop for all four times of day → identical composition. Skies 2–4 were generated from sky-1 as --ref ("repaint the same composition, change only the time of day"); the model held the layout very well (the dawn sun sits slightly lower/right).
- **Foreground**: generated foliage was much too big (reached x 40% and covered the arches from the top). The top fronds were dropped, the two bottom clusters split and shrunk to 55% toward their corners, then any residue in the free zone (x 15–85%, y < 88%) feathered out over 40 px. Result: zero alpha in the free zone.
- **Ornaments**: one 2048² sheet, 5 items, keyed and cropped by region, B channel clamped ≤ 0.8·G against magenta spill. Longest side capped at 900 px.

## Files (sizes)
sky-1..4.webp 1920×1080, 37–49 KB each · frame.webp 1920×1080 alpha 158 KB · foreground.webp 1920×1080 alpha 92 KB ·
orn-fan 900×469 (66 KB), orn-ring 739×743 (85 KB), orn-divider 900×76 (10 KB), orn-corner 708×689 (25 KB), orn-crest 694×694 (74 KB).
Previews: compose-1280.png, compose-1440x780.png, skies.png. Coordinates: scene.json.

## Known problems / notes
1. **The frame's top band is deeper than the mockup's**: the windows and the marquee panel reach y ≈ 30%, so a tab panel starting at y 22% hides the lower third of both windows and the lower part of the marquee panel. The sun/moon still shows (it sits at y 12–21%). If the panel can start at ~29–30%, the arches show whole; otherwise keep the title text in y 11–21%.
2. Windows are smaller than in the mockup (13% wide vs ~25%); the views are miniature but read well.
3. The sky files are only "right" inside the two windows — do not show them elsewhere.
4. The centre wall is plain dark green with a thin gold outline (by design, covered by the panel). Stage floor is fairly plain wood with footlight glow.
5. Gold in the frame/ornaments is warm, slightly coppery after despill.
