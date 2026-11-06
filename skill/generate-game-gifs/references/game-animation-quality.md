# Is this GIF good enough for the game?

Four separate questions. Answer each; a "yes" to one says nothing about the next.

1. **File** — `inspect_gif.py` exit < 2: GIF signature, every frame decodes.
2. **Animation** — exit 0: several frames, no identical neighbours.
3. **Visual quality** — the contact sheet and the GIF itself, at full size AND at the size it will be shown.
4. **Production suitability** — fits the game's art, sizes, background, timing and performance.

## Metrics (`inspect_gif.py`) and what they mean

| metric | reading | measured on the 4 tested GIFs |
|---|---|---|
| `adjacent_mad` | mean abs RGB difference between neighbours (0–255). ~1–8 for gentle motion | 1.7–7.9 |
| `seam_ratio` | last→first difference ÷ the median step. ≈1 smooth; > 2.5 warns of a jump at the wrap | 0.94–1.39 |
| `max_step` vs median | > 3× (and > 8) warns of a pop or cut | ≤ 2.2× |
| `changed_px_fraction` | share of pixels moving > 24 levels per step. > 0.5 = redrawn, not animated | 1.4–8.9 % |
| `border_drift_max` | how much a 6 % frame edge changes. > 6 warns of camera/background motion | 0.4–1.2 on flat grounds, 6.2 on a painted room (dither) |
| `moving_centroids` | centre of the pixels that move, per frame | shows a wandering body (Sunburst walk ±50 px vs Flare ±30) |
| `export_frames.py` `bottomSpreadPx` | feet row spread after the cut | 1 px |

These flag problems; none of them can say the motion looks right. All four 2026-11-05 GIFs passed every
threshold here and were still rejected: the character was repainted every frame (boiling eyes, ears, paws;
legs fusing). Always look at full size, frame by frame.

## The eye checklist

- **Character consistency** inside the GIF: markings, eye shape, ears, proportions, posture.
- **Temporal coherence**: each change follows from the last; nothing appears or vanishes.
- **Loop**: play it several times; watch the wrap.
- **Background**: still where it should be still; no shadow that should not be there.
- **Stray marks**: motion lines, sparkles, duplicated limbs.
- **Small size**: view at the real display size (e.g. 34–60 CSS px). Detail that matters must survive.
- **Across generations**: compare with the other animations of the same character; expect drift.

## Format for the game

| format | alpha | control | size (8 × 512² frames → keyed 104–144 px) | use |
|---|---|---|---|---|
| GIF | 1-bit at best (none returned) | play only | 368–693 KB | review, chat, a quick look |
| PNG strip | full | exact (steps / canvas) | 650 KB–1.2 MB at 512² | lossless source |
| **WebP strip** | full | exact | 46–53 KB keyed at game size | what would ship, for frames that pass review |
| animated WebP | full | play only | 52–115 KB at 512² | decoration |
| animated AVIF | full | play only | 14–48 KB at 512² | decoration, newest browsers |

Pick a strip whenever the animation must stay in step with something (a beat, a move): `steps()` or a
canvas puts frame *k* exactly where the game wants it, and the manifest's `rects` and `durationsMs` are the
contract. Load it fail-open (switch on `onload`) and give `prefers-reduced-motion` a still frame.
