# Proste bicia: the jungle plate (2026-11-04)

Owner: „Małpka i sawanna? Myślę, że małpka to i tło trzeba by w dżunglę zmienić.” The „Tarcza” backdrop of the
strumming course „Proste bicia” (MusicGames `ukulele-warmup/art/jungle/bicia-proste.webp`) goes from the savanna to a
rainforest, same 1024 × 1536 framing.

- `jungle-1.txt` — the prompt (the `prompts/ukuziom/bicia-tla/` shape, world swapped to the jungle, no horizon line).
- `ref-savanna-plate.png`, `ref-monkey.png` — the references (the old plate for style and layout, Kiwajka on white).
- `jungle-1.png` — gpt-image-2, quality medium, stream 2, 2:3, through APIYI (`asset-sheet/scripts/gen_image.py`).
  One try, $0.0638 (job `20261104-065810-845cf2`, tag `ukuziom-bicia-proste-jungle`).
- `jungle-1-graded.png` — the shipped grade: the middle band (a Gaussian centred at 34 % of the height, σ ≈ 17 %,
  weaker at the side edges) multiplied by (0.86, 0.86, 0.80), so the pale paper strips of the ring sit on a deeper
  gold-green (contrast vs the strip paper 1.10 → 1.31–1.43).
- `bicia-proste.webp` — what ships: WebP q72 method 6, 108 506 bytes.
