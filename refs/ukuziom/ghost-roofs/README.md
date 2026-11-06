# Neonowe miasto on a phone: rooftops with cats and ghosts (2026-11-06)

The owner's request: fill the empty band under the ring of G ↔ a (theme `ghost`, phone play screen) with
rooftops and cats and ghosts. `owner-mockup.png` is the owner's picture of the target; `owner-board-1/2.png`
the inspiration boards; `mockup-bottom.png` the mockup's bottom crop, passed as the style reference.

- `roofs.png` — the rooftop foreground, gpt-image-1.5, `--background transparent`, 1536×1024 (job
  `ghost-roofs-plate-2`, $0.23; the first try 502'd). Prompt: `prompts/ghost-roofs/roofs.txt`.
- `cast-sheet.png` — 16 cats and ghosts on magenta, Nano Banana 2K (job `ghost-roofs-cast`, $0.025).
  Prompt and names: `prompts/ghost-roofs/cast.txt`, `cast-items.txt`. Cut at native size into
  `sheets/assets/ghost-roofs-full/` (cut_assets.py --max-side 2048: 16/16, no duplicates).

Shipped in gondar/MusicGames `ukulele-warmup/art/ghost/roofs/`: every cast picture scaled ×0.5 (one scale for
all, so their sizes compare), and roofs.png cropped to y ≥ 300 and scaled to 1200×566.
