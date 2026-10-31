# Heron musician (Pory roku, ukulele warm-up C·G·a·F) — strum loop, idle bag, joy

Design: gpt-image-2 (medium, stream 2) from a crop of the owner's r2-b mockup → `refs/heron/design/heron-design-v1.png`,
keyed (green #22B24C), placed on 768² at 640 px tall (`refs/heron/heron-home-green.png`, cut `heron-cut.png` at 205,60).
Cell 412×476, figure 440 px, pivot (foot) 186,460, 12 fps. Shipped to MusicGames `ukulele-warmup/art/pory-roku/heron*`.

- **strum** (MiniMax, chained through a drawn pose): clip home → `heron-strumdown-green.png` (GPT edit, wing-tip below the
  sound hole, composited onto the design so only the hand box changed). H3 swung the wing UP over the strings first and
  then down past the hole; the loop is that down sweep, ping-pong: source frames 55 58 61 64 67 71 75 | 72 68 64 60 57
  (24 fps), `down` = 1 (wing over the sound hole). `in` = 14 frames home → top of the stroke (play reversed for out).
  The free-running strum clip (b0a501) was unusable: the ukulele turned and was redrawn every stroke.
- **idle** 8 gestures, one home: cutout (`rigs/heron/heron_cutout.py`) blink, breath, tilt, sway; MiniMax (lock.py)
  listen + lookup (clip A), ruffle (clip B, its blink-nod half dropped: the backdrop flashed lime 1.5–3.3 s), hat (clip C,
  no rest mid-clip so one gesture).
- **joy** MiniMax: wing flourish spread wide, then a deep bow, 49 frames.
- Blink: the Nano Banana closed-eye edit read as a grey blind disc, so the closed eye is painted (`heron-cut-eyeclosed.png`).

score.py: cutout static 3.15 colour 0.33 seam 0 motion 6.2 · A 9.2/6.1/0/18.0 · B 11.1/8.8/0/14.7 · C 11.8/8.6/0/27.3 ·
joy 23.4/22.5/0/39.1 (joy repaints the whole bird — by design, it is a big move).
Jobs: 59e3ea design, 6cd6b1 blink edit, 6f42c8 strum-down edit, clips b0a501 (strum, unused) 05d04a (A) 422153 (B)
af0b08 (C) ae8326 (joy) 614143 (strum chain); b0906a refunded (input_download_failed); four Gemini 502s.
