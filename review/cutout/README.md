# Mountain King — cutout-puppet idle (8 gestures), experiment vs the H3 video set

Built 2026-10-16. 8 gestures, 153 frames at 12 fps, cell 479×444, pivot (245.6, 442.8), atlas 34 cols × 5 rows
(`atlas.png` 6.5 MB, `atlas.webp` 1.55 MB at q70). First and last frame of every gesture = `rest.png` exactly.

## How it is built
- Rest pose = the reference picture itself (`refs/mountain-king/king-ref-headroom-v2.png`), placed in the cell by a
  similarity fit to frame 0 of the shipped `king-idle` strip (scale 0.3588, silhouette IoU 0.988 vs that frame).
- Rig `rigs/king/` (built by `skill/cutout/scripts/build_warp_rig.py rigs/king/spec.json rigs/king`):
  `base.png` (throne; inside the figure the "King removed" edit, seen only in slivers the head/torso uncover),
  `king.png` (figure, hard-cut from the reference), `ov_*.png` overlays (only the pixels an edit changed,
  registered + feathered), `w_head/w_torso/w_hand.png` weight maps, `rig.json`, `gestures.json` (keyframes).
- Instead of rigid pieces the figure is ONE layer bent by smooth weight maps (skinning: head, torso, hand).
  A seated, front-view troll has no clean joints (beard over neck, belly over hips, hands on the throne), so rigid
  pieces would open gaps / double outlines; a weighted bend cannot. Weight 0 (throne, legs, feet, hands) = the
  same pixels in every frame.
- Render: `python3 skill/cutout/scripts/render_gestures.py rigs/king review/cutout` (from the sprites root, ~75 s).

## Edits (gemini-3.1-flash-image, $0.0245 each, all logged in jobs/jobs.jsonl, tags K-cut-*)
| edit | result | used |
|---|---|---|
| throne (King removed) | redrew the whole throne taller/different | no |
| throne2 ("make him invisible, keep the low backrest") | kept hands/legs but painted the backrest behind head+torso | yes (base) |
| seg (flat parts map) | aligned to 1–2 px | yes (masks) |
| blink | clean closed eyes | yes |
| glance (eyes right) | clean | yes |
| down (eyes down) | clean, heavier lids | yes |
| smile | warm smile + happy squint | yes |
| beard (hand strokes beard) | good pose, armrest repainted | yes |
| drum (fingers lifted) | lifted the whole hand into a wave | no |
| drum2 (only fingers bend up) | small finger lift | yes |
10 successful calls = **$0.245**. Two more calls returned HTTP 502 (logged at $0; if billed anyway, +$0.049 →
worst case **$0.294**). All edits came back at 1024² aligned to the reference (registered scale 1.298–1.299, shift ≤2 px).

## Self-check (render_gestures.py writes check.json)
Max over frames of mean |RGBA diff| vs frame 0: bottom 28 % of figure = 0.000 in all 8 gestures; throne back
outside the head = 0.000 (glance, look, smile, beard, drum), 0.10 (tilt), 0.30 (breath), 0.50 (sway: the
shoulders cover/uncover the backrest edge; the throne pixels themselves never change). Seams: first/last frame vs
rest = 0.000 for all. (Armrests under the hands change in beard/drum on purpose: 0.65 / 0.90.)

## What worked
- Throne, legs, feet: bit-identical across all frames — the video route's main failure is gone.
- Face edits (blink, glance, down, smile) are clean overlays; flash was enough, pro not needed.
- Skinned head/torso: tilt, look-down, sway, breath have no holes, no double outlines.

## What did not / weak spots
- Beard: the arm swap is a crossfade (rest arm → raised arm) — one in-between frame each way shows a faint ghost
  arm. The stroke itself is a small warp of the hand (reads as a rub, not finger motion).
- Drum: a swap between two finger positions; the lift is small, reads as a twitch at game size.
- Glance/look are eye overlays + a small head shift (no 3D head turn).
- The "King removed" throne behind him is an edit, not the original; only thin slivers of it ever show.
- Sway is deliberately tiny (±1.3°); the hands stay pinned so the forearms bend slightly.
