# Mountain King — speed-up reactions (2026-11-13)

Three MiniMax-H3 clips made for the YouTube Short „Ta melodia przyspiesza. Nadążysz?” (gondar/Movies
`projects/w-grocie-krola-gor`), then put into the game (MusicGames `fingerpick-warmup`, sheet `react`).

| Name | Clip | Prompt | In the game |
|---|---|---|---|
| calm | `raw/20261113-074326-faac2f.mp4` (8 s) | `jobs/prompts/mountain-king/short-nadazysz-1-calm.txt` | a signature move in the idle bag |
| faster | `raw/20261113-074329-dc93a9.mp4` (7 s) | `…-2-faster.txt` | once, when the speed-up reaches stage 2 (2× speed) |
| fastest | `raw/20261113-074331-1bbe87.mp4` (6 s) | `…-3-fastest.txt` | at the take's top tempo, in place of the cheer (2× speed) |

First frame = last frame = `refs/mountain-king/king-first-blue-v3.png` (jsDelivr), $0.63 for the three.

Made with (from the repo root):
```
lock.py review/king-react raw/…faac2f.mp4=calm raw/…dc93a9.mp4=faster raw/…1bbe87.mp4=fastest \
  --home refs/mountain-king/king-cut-v3.png --at 158,215 --keep refs/mountain-king/king-throne-mask-v3.png \
  --pose-s 8 --step 2 --reach 260 --cell 479,444 --pivot 239.5,441.5 --fig 329.5
rebase.py review/king-react/atlas.json review/king-react/home.json review/king-react/rebased.json
pages.py review/king-react/rebased.json review/king-react/pages king-react --webp 80
```
`--pivot 239.5,441.5 --fig 329.5` were fitted so that the home frame lands on the game's cutout home (MAE 3.4 before
rebase, 0.35 after); `home.png` is the game's `art/king-cutout-base.webp`. `--reach 260`: the fists go far past the
outline. WebP 80, not 70: the browser's outline noise at the ends was over the game test's limit at 70.
The atlas PNGs are not committed (rebuild them with the commands above).

For the Short itself the clips were cut with `lock.py --frames --step 1` (full-size frames at 24 fps).
