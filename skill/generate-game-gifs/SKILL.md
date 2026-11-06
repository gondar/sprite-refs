---
name: generate-game-gifs
description: Generate short animated GIFs for 2D games with gpt-image-2.6's native GIF output through APIYI — idle loops, jumps, runs, walks, reactions — from YOUR character art as a reference, with a transparent background, then validate them at full size and turn them into game frames, spritesheets, manifests and a review page. Works offline on any existing GIF too (inspect, extract frames, key a flat ground, build a sheet) with no network and no cost. Use when someone wants a character animated as a GIF or sprite strip, "make this cat jump / run / blink", an animation that matches their existing art, a spritesheet from a GIF, or "is this GIF good enough for my game". About $0.04–0.11 per 8-frame GIF.
---

# Generate game GIFs

gpt-image-2.6 draws an animated GIF as **one sheet of frames** that the service slices. Through APIYI's
**edits** endpoint it takes your art as a reference, keeps that character and style, and returns a
transparent looping GIF in ~20–25 s. Tested 2026-11-05/06 (`experiments/gif-generation/REPORT.md` in
gondar/MusicGames): round 1 was rejected, round 2 found why and matched a ChatGPT-made GIF.

## 1 · The recipe (defaults of `generate_gif.py`)

```bash
APIYI_KEY_FROM_PROXY=1 python3 scripts/generate_gif.py \
  --route edits --ref art/my-character.png --prompt-file prompts/jump.txt --out out/jump.gif \
  --log out/jobs.jsonl          # defaults: flare, 8 frames, 100 ms, 960x960, medium, transparent, no complexity
```

| setting | use | why (measured) |
|---|---|---|
| `--route edits --ref ART` | yes, whenever the character exists | identity and style of your art; text only draws a different character |
| `complexity` | **never send it** | `complexity: low` ignored "green eyes" (amber), flattened the jump, smeared the drawing. It was in every rejected GIF of round 1; the same request without it was clean |
| `background` | `transparent` | palette transparency on every frame; no keying needed |
| `quality` | `medium` | as clean as `high` at full size, ~18 % fewer tokens; `low` still coherent, softer |
| frames × `size` | must fit a 3840 px sheet | 8 frames → ≤ 960×960 · 12 → ≤ 768×768 · too big = instant HTTP 400 "No supported sheet fits" |
| `model` | `gpt-image-2.6-flare` | Sunburst at high took > 30 s and APIYI cut it with a 502 at 30.6 s, twice (on api. and b.apiyi.com) |
| `--route responses` | no | the gateway rejects GIF parameters on the Responses image tool (`Unknown parameter: tools[0].frame_count`) |

Prices (APIYI list: $5/M text in, $8/M image in, $30/M image out): 8 frames 960 px medium ≈ 2,230 output
tokens ≈ **$0.08** with a reference; high ≈ 2,700 (≈ $0.095); low ≈ 1,260 (≈ $0.05); 12 frames at 768 medium
≈ 3,240 (≈ $0.11). A reference sheet of 1536×1024 added 1,536 image-input tokens (≈ $0.012).

## 2 · Prompt

Write it like the prompt that worked (full text: `assets/example-prompts.json`, `references/prompting-guide.md`):
name the character as it appears in the reference ("the grey cat, KOT 1 – SZARY"), demand the same style in
concrete words (thick dark outline, the same face, markings, scarf), describe the motion as a short sequence of
poses or 2–3 small named beats, say "stays in exactly the same place and size" (or "runs on the spot … never
travels across the picture"), "exactly four legs, clearly separated", "seamless loop", "N equal-size frames",
"clean transparent background only — no scene, no shadow, no text, no borders".

## 3 · Providers and credentials

`apiyi` (default, tested): key in `APIYI_API_KEY`, or `APIYI_KEY_FROM_PROXY=1` behind a key-injecting proxy.
`openai` (untested): `OPENAI_API_KEY`, only when asked for by name — never a fallback. A missing key exits 2,
"Nothing was sent". Keys are never printed, logged or written to manifests.

## 4 · Cost safeguards

- Agree a budget and a call cap first; every call is logged before and after (`--log`); `--dry-run` shows
  the exact request and sends nothing.
- **Never retry** a timeout or a 5xx: the job may have been billed. Exact charges need APIYI's personal
  access token (`nap_…`, `GET /api/log/self`); an `sk-` key cannot read them — say "estimated" until then.
- Offline steps never touch the network. Test scripts on an existing GIF, not a new generation.

## 5 · Validate — at FULL size, frame by frame

```bash
python3 scripts/inspect_gif.py out/jump.gif --json out/jump.inspect.json --sheet out/jump.contact.png
```
Numbers (frames, size, ms, loop, transparency) and metrics (adjacent difference, seam ratio, border drift)
catch broken files and jumps at the wrap. **They do not catch a character repainted every frame** — round 1
passed every threshold and was rejected. Look at the frames side by side at full resolution (not a small
contact sheet, not only at game size): eyes, ears, paws, legs, markings, scarf. Then let the person who
owns the art decide; show it moving (`build_preview.py`) before anything ships.

## 6 · Make it game-ready

```bash
python3 scripts/export_frames.py out/jump.gif out/jump.frames --crop union --pad 6 --height 256
python3 scripts/build_spritesheet.py out/jump.frames out/jump.webp --name jump --cols 4
```
`--crop union` = one box for all frames (they stay aligned). For an opaque GIF on a flat colour add
`--key border` (+ `--despill`, `--largest-component`, `--shift-hue`). The manifest records measured
`frames`, `frameWidth/Height`, `durationsMs`, `loop`, `rects`. GIF alpha is 1-bit: edges are hard, so view
it on the game's real background. A WebP strip + CSS `steps(N)` (or a canvas) is what a game can time:
`background-size: N*100% 100%`, animate `background-position-x` 0% → `calc(100% * N / (N-1))`, switch to
the strip only on `onload` (fail open), still under `prefers-reduced-motion`.

## 7 · Scripts

| script | network | what |
|---|---|---|
| `generate_gif.py` | **paid call** | one request (images / edits / responses route), no retry, logged |
| `inspect_gif.py` | none | file / animation / numbers / metrics verdicts, contact sheet |
| `export_frames.py` | none | frames → PNG with timing; crop, key, despill, stray-mark removal, hue match, resize |
| `build_spritesheet.py` | none | strip/grid PNG or WebP + manifest |
| `build_preview.py` | none | review page: GIFs on light/dark/checker, scrubber, numbers, notes, sections |
| `selftest.py` | blocked | the skill's own checks with sockets disabled |

References: `references/gif-api.md` (the API as tested, errors), `references/prompting-guide.md`,
`references/game-animation-quality.md`, `assets/example-prompts.json`.
