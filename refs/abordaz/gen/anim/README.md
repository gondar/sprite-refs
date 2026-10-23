# Abordaż — animation sheets and extra seas (2026-10-23)

Nano Banana Pro (`gemini-3-pro-image`, 2K, through APIYI; $0.09 a call; 12 billed calls ≈ $1.08, plus one gull call
rejected for an unsupported 2:1 aspect and not billed; the fencing sheet was re-rolled once because the cutlass changed hands). Prompts:
`jobs/prompts/abordaz/{szabla-sing,szabla-fence,szabla-fence2,grzmot-idle,gull-flap}.txt` and `jobs/prompts/abordaz/seas/*.txt`.
Stored as WebP q92 (the API's PNGs were 47 MB).

| sheet | ref(s) | used |
|---|---|---|
| `szabla-sing` (2×2) | `refs/abordaz/szabla-src.png` | all 4 → `szabla-sing.webp` |
| `szabla-fence` (2×2) | `szabla-src.png` | NOT used: the cutlass changed hands in frames 2–3; frames 1 and 4 became `ref-fence1/4` |
| `szabla-fence2` (3×2) | `ref-fence1`, `ref-fence4` | all 6 → `szabla-fence.webp` |
| `grzmot-idle` (2×2) | `ref-grzmot` (the shipped grzmot.webp on magenta) | all 4 → `grzmot-idle.webp` |
| `gull-flap` (4×2) | `ref-gull-up/mid/down` | all 8, reordered → `gull-flap.webp` |
| `../seas/*` | `refs/abordaz/gen/plate-sea.png` | → `sea-<name>.webp` |

Build: `python3 scripts/abordaz_anim.py /home/user/MusicGames` (keys, aligns on the anchor, equal cells, writes art.json).
