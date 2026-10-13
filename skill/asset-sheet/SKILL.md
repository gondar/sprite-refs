---
name: asset-sheet
description: Generate many static game assets at once — props, icons, items, collectibles, UI pictures — as ONE image with up to ~100 objects on a flat key colour, then cut it into named transparent files plus an atlas, with checks that every name matches its picture. Uses Nano Banana (Gemini image) through APIYI at about $0.00025–0.0015 per asset. Use this whenever someone needs a set of icons, props, stickers, item pictures, collectibles or sprites that do not move, "a bunch of assets", "art for all these items", or a replacement for emoji in a game — and before generating assets one image at a time. For characters that must MOVE (idle, walk, run, jump), use the `sprite-pipeline` skill instead.
---

# Asset sheet — many static assets from one image

The image-generation recipe (style · subject · composition · context), pushed to its limit: list every asset you
need, ask for all of them on ONE sheet in a grid, then cut, name and verify automatically. Measured on
2026-10-12/13 with a cosy campfire prop set (fox scout game) through APIYI.

**Static only.** Anything that animates belongs to `sprite-pipeline` (it has the video route, loops, pivots).
A single hero image or background is ordinary image generation, not this.

## How many per sheet (measured, Nano Banana `gemini-3.1-flash-image`, 1:1)

| Assets on one sheet | Output | Result | Cost per asset |
|---|---|---|---|
| 16 (4×4) | 1K | all 16, in order, clean | $0.0015 |
| 36 (6×6) | 1K | all 36 in order, but pale-pink background and DRAWN grid lines (keyed out fine) | $0.0007 |
| 64 (8×8) | 1K | all 64 in order, clean | $0.0004 |
| 64 (8×8) | 4K | all 64 in order, ~512 px each, slightly lighter magenta, 31 s | per tokens — check the log |
| 100 (10×10) | 1K | all 100 in order, ~100 px each | $0.00025 |
| 144 (12×12) | 1K | **broke**: duplicated 5 items, dropped others, names shifted from row 2 | — |
| 144 (12×12) | 2K | HTTP 502 at 30.7 s (no image; may still be billed) | — |

**Default 64 per sheet; 100 is the ceiling.** Past that the model repeats items to fill the grid. Need more
than 100? Split the list across sheets that share the same style line. Need bigger pictures than ~100–128 px?
Fewer per sheet or 4K (slow: keep it under ~30 s or the gateway may cut it).

## The prompt (copy the shape)

```
Game asset sheet: separate small objects for <game / theme>, painted in <style: e.g. a soft cartoon storybook
style (gentle shading, clean silhouettes, no hard black outlines)>, all lit from the top-left, all in the same
style and scale family.
Draw EXACTLY <N> separate objects, one per cell of an invisible <R> x <C> grid (<R> rows of <C>), placed in the
order of this list in reading order (row 1 left to right, then row 2 …), each object centred in its own cell,
filling about 70% of the cell, never touching or overlapping a neighbour, empty space between them:
- <item 1>
- <item 2>
…
Each object stands alone: no ground, no shadow, no scenery, no glow, no smoke. Draw NO text anywhere: no numbers,
no letters, no labels, no captions, no grid lines, no borders.
Background: perfectly flat solid magenta #FF00FF everywhere. No object may contain magenta or pink; use red,
orange, purple-blue instead.
```

Why each line is there:
- **Bullets, not numbers.** A numbered list put faint "19", "21", "61" next to objects; grey digits are not key
  colour, so they survive keying. Bullets fixed it.
- **"EXACTLY N", the grid size, reading order.** This is what lets the cutter name things from the list.
- **Concrete item names with a colour where it matters** ("maple leaf (orange)", "butterfly (blue)") keep the
  model from improvising and from drifting into the key colour.
- **No glow / smoke / steam.** Semi-transparent effects mix with the magenta: the firefly's glow came out pink.
  Need a glowing item? Put the glowing ones on their own sheet keyed on green, or draw the glow in the game.
- **Key colour:** magenta by default; green #00FF00 when the set has pink, purple or magenta things in it (the
  sheet must be one key colour — split a mixed set into two sheets).
- **A style reference image helps match an existing game** (pass it with `--ref`, as in sprite-pipeline);
  without one the model's house style is a clean cartoon icon look.

## Generate, cut, verify

From a clone of `gondar/sprite-refs` (the job log lives there):

```bash
S=.claude/skills/asset-sheet/scripts   # or skill/asset-sheet/scripts inside sprite-refs
python3 $S/gen_image.py --model gemini-3.1-flash-image --prompt-file prompts/props-64.txt \
        --aspect 1:1 --out refs/assets/props-64.png --tag props-64            # logged, ~15 s, ~$0.025
python3 $S/cut_assets.py refs/assets/props-64.png prompts/props-items.txt sheets/assets/props --grid 8x8
```

`cut_assets.py` keys the sheet (edge-only despill), finds each object, assigns it to the grid cell its centre
falls in and names it from the item list. It writes `<name>.webp` per asset (tight crop, longest side ≤ 256 px),
`atlas.png` + `atlas.json` (`{name: {x, y, w, h}}`) and `check.png` (every cut on a checkerboard with its name).

It refuses to let a misnamed set through quietly:
- **exit 2 — an empty cell:** the model skipped or merged an item, so every later name would be off by one.
- **exit 3 — possible duplicates:** two cuts look nearly identical (32 px thumbnails, mean difference < 0.055).
  That is how an over-full sheet fails — it repeats items, every cell holds something, and the count looks fine.
  Measured: real duplicates 0.035–0.050; the closest distinct pair on a clean sheet 0.059. Similar real objects
  (wooden spoon vs paddle) can trip it, so it is a warning to LOOK, not a verdict.
- **merged pieces are reported, not errors:** one object drawn in two parts (deer antlers, a whistle on a cord)
  is merged into one asset.
- **Always open `check.png` before using the set.** Names come from list order; only your eyes confirm that
  item 37 really is the matchbox.

## Before any paid call

- Tell the person the batch cost first. Nano Banana at 1K ≈ $0.025 a sheet (billed by tokens; 2K/4K cost more —
  check the APIYI log). Nano Banana Pro is $0.09 and was not needed for props.
- A call slower than ~30 s can come back HTTP 502 "upstream request failed" through the gateway and still be
  billed (seen on gpt-image and on a 2K Gemini sheet). Keep dense sheets at 1K; never auto-retry a 502 without
  checking the APIYI log first.
- `gen_image.py` logs a `submitting` line before the call and the result after, in `jobs/jobs.jsonl`.

## Into the game

Use the per-asset WebP files where the game references images one by one (the ukulele warm-up's themes do), or
the atlas where it draws from one texture. Keep the generated sheet and item list in `gondar/sprite-refs`; only
the cut files go into the game repo. Fail open: a missing file should fall back to the emoji or the old picture.

## Open questions

- Does Nano Banana Pro hold order past 100? Not tried.
- 2K at 100+ items — worth it if the call finishes under ~30 s; not yet measured.
- Mixed scales (a tent next to an acorn) are drawn at the same cell size; if real relative size matters, say it
  per item or group items of a similar size on one sheet.
