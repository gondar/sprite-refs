---
name: generate-game-gifs
description: Generate short animated GIFs for 2D games with an image model's NATIVE GIF output (gpt-image-2.6-flare / -sunburst through APIYI's OpenAI-compatible images endpoint), then validate them and turn them into game-ready frames, keyed RGBA spritesheets, manifests and a review page. Also works offline on any existing GIF — inspect it, extract frames, key a flat background, build a sheet — with no network and no cost. Use when someone asks for an animated GIF, a looping idle (sleeping, purring, blinking, tail swish), a small walk cycle, "make this character move" with a budget of cents, a spritesheet from a GIF, or "is this GIF good enough for my game". For a character that needs real limb motion with a fixed design across many clips, prefer a reference-driven pipeline (first/last-frame video, cutout rig); this skill's text-to-GIF cannot keep one character identical between separate generations.
---

# Generate game GIFs

Native GIF generation turns one text prompt into a real multi-frame GIF in **7–17 s for about $0.018**
(512×512, quality low, 6–8 frames, measured 2026-11-05). It is good at small, in-place, looping motion of a
character that does not have to match an existing one exactly. Everything after generation is offline:
validating, keying, cropping, packing, previewing.

All scripts are in `scripts/`, Python 3 + Pillow + NumPy, no other dependencies:

| script | network | what |
|---|---|---|
| `generate_gif.py` | **paid call** | one request, no retry, logs before and after, saves errors apart from media |
| `inspect_gif.py` | none | file / animation / numbers / metrics verdicts, contact sheet, exit code |
| `export_frames.py` | none | frames → PNG with timing; key a flat ground, despill, drop stray marks, match a hue, one shared crop, resize |
| `build_spritesheet.py` | none | frames → strip/grid PNG or WebP + manifest with measured rects and durations |
| `build_preview.py` | none | one HTML review page: GIFs on light/dark/checker, frame scrubber, numbers, notes |
| `selftest.py` | blocked | checks the skill itself with sockets disabled: `python3 scripts/selftest.py [some.gif]` |

Looping: the API returns a looping GIF (`loop=0`); a one-shot reaction is a manifest flag
(`build_spritesheet.py --no-loop`) and the game plays it once.

## 1 · Decide whether this is the right tool

- **Yes**: an idle loop (breathing, blink, ear twitch, tail), a reaction (perk up, paw wave, small bounce),
  a simple in-place walk, ambient props (flame, flag) — at sprite sizes up to ~256 px.
- **No**: the character must be the SAME one already in the game, pixel for pixel, or across many
  animations; precise timing on a beat inside the animation; large travel across the frame; text.
  Separate generations of the same prompt give a different cat (eye hue 82° vs 134°, fur tone, fluff).
  Use a reference-based route for that, and use this skill only for its offline half.
- The images **edit** endpoint does not return GIFs, so there is no "animate this picture" here.

## 2 · Providers and credentials

| provider | status | how |
|---|---|---|
| `apiyi` (default) | **tested, works** | `https://api.apiyi.com/v1/images/generations`, key in `APIYI_API_KEY` |
| `openai` | untested | `https://api.openai.com/v1/images/generations`, key in `OPENAI_API_KEY`; only when asked for by name — never a fallback |
| native Codex / ChatGPT image tool | not available in the environment this was built in | if your session exposes an image-generation tool, it is a separate route; do not assume one exists |

The key is read from the environment and never printed or logged. Behind an egress proxy that injects it,
set `APIYI_KEY_FROM_PROXY=1` (the header then carries a dummy the proxy replaces). A missing key exits 2
with "Nothing was sent". **Never commit a key**; manifests and logs contain none.

## 3 · Cost safeguards (read before any call)

- Billing is per token: $5/M text in, $30/M image out on APIYI (read the live price:
  `curl -s https://docs.apiyi.com/model-registry.json`). Measured: **555 output tokens per 512×512 low GIF
  whether 6 or 8 frames**, ~150–220 input tokens → ≈ $0.018 per call, Flare and Sunburst alike.
- Agree a cap on calls with the person before the first one, and log every call (`--log`). Use
  `--dry-run` to show the exact body without sending it.
- **Never retry** a timeout, a 5xx or a transport error: the upstream job may have run and been billed.
  The script stops and says so. Check the provider's request log (needs a personal access token, `nap_…`,
  at `https://api.apiyi.com/api/log/self`; an `sk-` key cannot read it) before asking again.
- Offline steps never touch the network — reuse an existing GIF to test anything that is not generation.

## 4 · Generate

```bash
APIYI_KEY_FROM_PROXY=1 python3 scripts/generate_gif.py \
  --prompt-file prompts/cat-idle.txt --out out/cat-idle.gif --log out/jobs.jsonl \
  --model gpt-image-2.6-flare --frames 8 --duration-ms 160 --size 512x512 --quality low --complexity low
```

Defaults are the tested ones: Flare, 6 frames, 180 ms, 512×512, low, low, `n=1`, 600 s timeout.
`--complexity none` leaves the field out (APIYI accepted it; another gateway may not).
The response is decoded only after a 2xx with `data[0].b64_json`; a non-GIF payload is kept as
`OUT.notgif.<ext>` and never renamed to `.gif`. Exit codes: 0 ok · 2 usage/credentials · 3 HTTP/transport · 4 no GIF.

**Flare vs Sunburst** (same walk prompt): Flare kept the flat painted sticker look and a centred body;
Sunburst gave a longer stride but a glossy 3D look, more body drift and a stray pink paw pad, 1.8× slower,
same price. Start with Flare; try Sunburst when the motion itself is the problem.

Prompt patterns that worked are in `references/prompting-guide.md` and `assets/example-prompts.json`. The
short version: one character, "stays in exactly the same place and size", "camera completely stationary",
a flat solid background named by hex for anything you will cut out, the motion as two or three small
named beats, "seamless loop that ends on the same pose it starts with", and a "No text, borders, motion
lines, multiple views, spritesheet layout" tail.

## 5 · Validate — never report success from HTTP 200

```bash
python3 scripts/inspect_gif.py out/cat-idle.gif --json out/cat-idle.inspect.json --sheet out/cat-idle.contact.png
```

It answers four different questions: is the **file** a GIF Pillow decodes; is it **animated** (several
frames, adjacent frames differ); the **numbers** (frames, size, per-frame ms, loop flag, disposal,
transparency); and **metrics**: adjacent-frame difference, the last→first **seam ratio** (≈1 smooth,
>2.5 a visible jump), **border drift** (background/camera moving), share of pixels changing per step
(>50 % = a redraw, not motion). Then LOOK at the contact sheet and the GIF: metrics cannot see a morphing
face, a stray mark, or a gait that reads wrong. Details and thresholds: `references/game-animation-quality.md`.

## 6 · Make it game-ready

GIF has no real alpha (1-bit palette transparency at best; the tested outputs had none). Ask for a flat
ground and key it:

```bash
python3 scripts/export_frames.py out/cat-walk.gif out/cat-walk.frames \
  --key border --despill blue --largest-component --crop union --aspect 148/100 --height 104 \
  [--shift-hue 134 82]          # match an accent colour to another generation
python3 scripts/build_spritesheet.py out/cat-walk.frames out/cat-walk.webp --name cat-walk
```

- `--crop union` = ONE box for every frame, so frames stay aligned (never crop frames one by one).
- `--aspect` pads the box to an existing sprite box's proportions, feet kept on the bottom edge.
- `--despill` removes the background colour the model lit the rim with; `--largest-component` drops
  stray marks (a "motion line" appeared despite the prompt saying no); both are reported in `frames.json`.
- The manifest (`cat-walk.json`) holds measured `frames`, `frameWidth`, `frameHeight`, `durationsMs`,
  `loop`, `rects`, `bytes` — read numbers from it, never retype them.
- Prefer a **WebP strip** over the GIF in a game: full alpha, precise control of timing from code, and
  ~7× smaller (a 368 KB GIF became a 53 KB keyed strip). Animated WebP/AVIF are fine for decoration you do
  not need to control; a strip + `steps()` or a canvas is what you can sync to a beat.

CSS for a strip of N frames: `background-size: N*100% 100%` and animate `background-position-x` from `0%`
to `calc(100% * N / (N-1))` with `steps(N)`. Load the strip with `new Image()` and only switch to it on
`onload`, so a missing file leaves the old picture (fail open). Respect `prefers-reduced-motion`.

## 7 · Review page

```bash
python3 scripts/build_preview.py spec.json preview/index.html            # links files
python3 scripts/build_preview.py spec.json review.html --embed           # one self-contained file
```
The spec format is in the script's docstring. Show the person the animation moving before it ships.

## References

- `references/gif-api.md` — the request/response, parameters, limits, error classes, what was verified.
- `references/prompting-guide.md` — prompt structure, what helped, what the model ignored.
- `references/game-animation-quality.md` — the checklist, metric meanings and thresholds, format choice.
- `assets/example-prompts.json` — the prompts behind the four tested GIFs, with their results.
