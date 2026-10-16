# Mountain King — cutout-puppet idle, round 2 (20 gestures)

20 gestures, 386 frames at 12 fps, cell 479×444, pivot (245.6, 442.8), atlas 34 cols × 12 rows.
`atlas.webp` = **4.24 MB** (`atlas.png` for the review page). Because that is over 3 MB there is also a split version
in `split/`: `base.png/.webp` (everything that never changes, 5 KB) + `atlas.{png,webp,json}` holding only the
rectangle that ever changes, `crop` = [83, 105, 292, 241] (33 % of the cell), **2.93 MB** webp. Draw the base at the
cell origin, then the cell at (crop.x, crop.y). Rebuilding every frame from the split is exact (max error 0).
First and last frame of every gesture = `rest.png`, bit for bit.

## Round 2 changes
- **beard: removed.** I chose to drop it rather than redo it. Any hand-to-beard move means a large part changing
  position, and the slide-on-the-armrest version would show the throne edit's own hand painted under the King's
  hand. Its overlay (`ov_beard`) and hand deformer are gone from the rig.
- The 7 kept gestures render the same pixels as round 1 (all 133 frames checked: max difference 0).
- New: 5 flash face edits (eyes left, eyes up, sleepy half-lids, one raised brow, grumpy furrow), all clean on the
  first try, plus a free `glow` overlay (the crystals and eye glow pixels brightened ×1.35, picked by colour inside
  boxes around the crown, shoulder crystals and eyes).

## Gestures (seconds = (frames − 1) / 12)
| name | s | what |
|---|---|---|
| breath | 1.5 | chest swells (torso scale), head rides up |
| glance | 1.42 | eyes right + small head turn |
| look | 1.5 | eyes down + head dips |
| smile | 1.58 | warm smile, slow blink inside it |
| drum | 1.42 | fingers of the right-side hand lift and tap three times |
| tilt | 1.5 | curious head tilt 4.5° |
| sway | 1.58 | upper body sways ±1.3°, hands stay put |
| blink2 | 1.0 | double blink |
| sleepy | 1.83 | lids sink to half, head drops a little, eyes reopen |
| dart | 0.92 | eyes dart right and back (head still) |
| glance_left | 1.42 | mirror of glance (eyes-left edit) |
| nod | 1.42 | two tiny "hmm" nods |
| lookup | 1.58 | eyes up, head lifts a little |
| shrug | 1.33 | shoulders rise and settle |
| sigh | 2.0 | deep inhale, eyes close, exhale with the head dropping |
| smiletilt | 1.83 | smile + tilt |
| glow | 1.58 | crown crystals and eye glow brighten and fade |
| drowsy | 2.0 | head sinks, lids droop, eyes close, then a small startle awake |
| curious | 1.5 | one brow up + slight tilt |
| grumpy | 1.58 | brows furrow, head lowers a little |

## Cost (gemini-3.1-flash-image, $0.0245 per edit, all in jobs/jobs.jsonl)
- Round 1, tags K-cut-*: 10 edits = $0.245. Two more calls returned HTTP 502; they are logged at $0, and if they
  were billed anyway that adds up to $0.049.
- Round 2, tags K-cut2-*: 5 edits = $0.1225.
- Total: $0.3675, worst case $0.4165.

## Checks (`check.json`, written by render_gestures.py)
- Bottom 28 % of the figure: 0.000 in every gesture.
- Throne back outside the head: ≤ 0.50 (sway 0.50, shrug 0.42, sigh 0.36, breath 0.30, others ≤ 0.10). The non-zero
  values come from the shoulders covering and uncovering the backrest edge; the throne pixels themselves never change.
- Seams (first and last frame vs rest): 0.000 for all 20.
- `review/score.py`: static 0.05, colour 4.55 (most of it from the glow gesture, which brightens on purpose),
  seam 0.00, motion 1.83.

## Weak spots
- Eye changes (glance, dart, lookup) are 1–2 frame crossfades of the pupils inside the socket. The move is small,
  so there is no visible ghost.
- drum is a swap between two finger positions; it may read as a twitch at game size.
- The throne back that the head and torso uncover comes from an edit, not the original painting; only slivers of a
  few pixels ever show.
- The atlas is large (4.2 MB, or 2.9 MB split). Lower webp quality or keeping every other frame would shrink it.

## Rebuild
`python3 skill/cutout/scripts/build_warp_rig.py rigs/king/spec.json rigs/king`, then
`python3 skill/cutout/scripts/render_gestures.py rigs/king review/cutout` (~3 min), then
`python3 skill/cutout/scripts/split_atlas.py review/cutout/atlas.json review/cutout/split`.
The gestures are keyframes in `rigs/king/gestures.json`, so a new gesture costs nothing but a few lines there.
