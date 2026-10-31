# UkuZiom exercise mascots — the moving conductors (2026-10-31)

Lwiątko Leon (exercise 2, C ↔ G), Zenek Kosmita (4, a ↔ F) and Papuga Konfetka (5, C → G → a → F), from the
8-mascot asset sheet (`refs/assets/ukuziom-cards/mascots-8.png`), animated with MiniMax-H3 in first = last frame
mode, one 4 s clip each. Shipped as `ukulele-warmup/art/{jungle/leon,space/zenek,festival/konfetka}-play.webp` in
MusicGames (13 × 4 grid of 280 × 240 cells, 12 fps), played by `MCOND` in `ukulele-warmup/index.html`.

- Home pictures: `refs/ukuziom/*-home-{blue,red}.png` (768², figure 492 px, feet at y 660), cut-outs `*-cut.png`.
- Prompts: `jobs/prompts/ukuziom/*-play.txt`. Clips: `raw/20261031-1619{19,21,23,25}-*.mp4`.
- Cost: 4 clips × $0.12 = $0.48 (Konfetka on blue and on red). Jsdelivr `@sha` URLs were refused (400, not billed);
  raw.githubusercontent `<sha>` went through first time.
- Every ground held: corner drift ≤ 3.3 levels over 4 s, red included; frame 0 vs the picture MAE 5.4–7.5.
- Konfetka: on blue her wing tips are keyed away (`konfetka-blue-cut.png`); on red with lock.py's default key her
  chest goes pale and wing blur leaves ghosts (`konfetka-red-default-key.png`); `--dom 100,35 --spill 100,55` is
  clean (`konfetka-red-final.png`).
- lock.py: `--pose-s 4.4 --cell 280,240 --pivot 140,238 --fig 200 --step 2`, `--reach 60` (Leon, Zenek) / 160 (Konfetka).
