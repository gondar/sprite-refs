# Lew śpi dziś w nocy — three ukulele musicians (lion, parrot, leopard)

## What was done
1. **Design** (Nano Banana Pro, `gemini-3-pro-image`, $0.09 each). Refs passed in: the portrait cropped from the mockup, the one cropped from the owner's reference, and the whole reference. All three are waist-up, three-quarter turned to screen RIGHT, with a dark bottle-green tux with gold piping, a white shirt, a black bow tie and a ukulele in playing position.
   - Two fixes, done as single-change edits on Nano Banana (`gemini-3.1-flash-image`, $0.0245 each):
     the **parrot** had palm-frond clumps behind his shoulders (carried over from the reference's leaves), so they were removed;
     the **leopard's** bow tie was dark green, so it was made black and given a warmer smile.
   - The lion needed no change.
   - Each design was keyed on blue dominance, with the fringe despilled and only the largest component kept. It was then placed on flat #2F6BD8 at 768×768, the figure 64 % of the height (492 px), centred, cut at the bottom edge (waist). Head tops are at the same height for all three.
   - Files: `sprite-refs/refs/lew/{lew,papuga,lampart}-home-blue.png` (first/last frame) and `-cut.png` (RGBA for lock.py). The designs are in `refs/lew/design/`.
2. **MiniMax-H3**, first = last = the same picture, 4 s, ratio adaptive. Prompts are in `sprite-refs/jobs/prompts/lew/play-*.txt` (~135 words, quoted below).
3. **Cut** with `lock.py --pose-s 4.4 --reach 60 --cell 360,360 --pivot 180,359 --fig 320 --step 2` (no `--keep`). The frame at 4.25 s, which equals home, was dropped, giving 51 frames at 12 fps per character. Packing is my own: 11×5 cells of 360×360 on a single 3960×1800 page, WebP q35 with alpha q50.

## Hosting problem
- **jsDelivr** URLs pinned with `@sha` are refused by H3 with a 400 ("must be a public HTTPS URL", the known `@` validator issue, not billed).
- **raw.githubusercontent.com/<sha>/…** was used instead. The first try of each clip failed with `input_download_failed` (H3 reached GitHub over IPv6) and was auto-refunded. The second try of each succeeded.

## Jobs / cost (from jobs/jobs.jsonl)
| char | design | edit | clip job (succeeded) |
|---|---|---|---|
| lew | 20261026-214948-ba7a38 | — | 20261026-215944-42e0f2 |
| papuga | 20261026-214948-975b0d | 20261026-215045-45b4e9 | 20261026-215931-c992d4 |
| lampart | 20261026-214948-c3a7ae | 20261026-215045-89ce1a | 20261026-220009-9133ad |

Refunded (input_download_failed): 20261026-215420-2c4672, -215422-feb6a2, -215424-c987a6, -215712-94c196, -215717-95d831, -215721-6be7f9.
The three 400s (20261026-215354/215357/215358) were not billed.

**Net spend: $0.679** = 3 × $0.09 + 2 × $0.0245 + 3 × $0.12. No clip was re-run for quality.

## Measurements
- **Clips:** 768×768, 24 fps, 107 frames (4.46 s).
- **Corner colour:** held to ±2–3 levels for the whole clip in all three.
- **Frame 0 vs the picture, MAE:** lew 8.1, papuga 6.2, lampart 7.6 (target ≈ 5). Part of this is the ground shifting from (47,107,216) to (42,99,207). The static lock replaces non-moving pixels with the picture.
- **score.py:**

  | char | static | colour | seam | motion |
  |---|---|---|---|---|
  | lew | 13.3 | 3.8 | 0.00 | 22.6 |
  | papuga | 17.0 | 9.0 | 0.00 | 29.6 |
  | lampart | 17.2 | 4.1 | 0.00 | 30.5 |
- **Loop wrap (frame 50 → 0):** mean |diff| 0.1–0.5 against a median frame step of 5. It comes home cleanly.

## Honest notes
- **H3 moved the whole upper body, not just the strumming hand.** In all three the body sways gently and the ukulele moves with it. The lion's mane is redrawn a little fuller mid-clip. So the static lock covers most of the figure (moving area ~120k px), and "static" in score.py is high (13–17).
  - This reads as a musician playing, not as shimmer: there are no seams or ghosting in a full-size check.
  - The bottom edge (the waist cut) also moves slightly.
- **Leopard:** around frames 38–45 the ukulele bridge and strings are a little smeared, and the strumming paw is large. It is barely visible at 180 px.
- **Parrot:** colour drift 9.0 (shading on the green tux shifts a little). It looks the same by eye. Owner, please glance at the parrot's frames 15–30 (the head bob).
- **Strum tempo is H3's own, not the game's.** One down-stroke every ~12.5 frames for the lion (~58/min at 12 fps), ~7.5 for the parrot (~96/min) and ~8.5 for the leopard (~85/min). To land a strum on a beat, retime: pick the `strum_low` frame nearest the beat, or scale playback fps.
  - `strum_low` was measured from the vertical centroid of the strumming paw/hand in each frame (local maxima, prominence > 12 px).
  - The parrot's frame 4 is at the very start, during the ease out of home.
- **Size:** 1.62 MB total (three strips 0.47–0.59 MB plus three homes ~24 KB each), slightly over the 1.5 MB target.
  - At q30 it would be 1.5 MB, but feathers and strings smear visibly, so I kept q35 at full height and 12 fps.
  - Next lever: 8 fps (lock with `--step 3`), about −30 %.

## Prompts
**lew** (`jobs/prompts/lew/play-lew.txt`):

```
[Static shot] The camera is locked and the lighting never changes. A dignified lion musician in a tuxedo plays his ukulele in a calm jazz club. His right hand strums gently down and up across the strings in a slow, steady rhythm the whole time, a small relaxed wrist movement right over the sound hole, while his left hand stays on the neck. First his head sways slowly to one side with the beat and his eyes close halfway, enjoying the music. Then his head sways gently back and his eyes open again in one slow, contented blink. He ends exactly in his starting pose, lips pressed together in a calm smile. The ukulele, his left hand, his tuxedo, his shoulders and the plain backdrop stay completely steady. Sound: a soft, quiet jazz-club room ambience only.
```

**papuga** (`jobs/prompts/lew/play-papuga.txt`):

```
[Static shot] The camera is locked and the lighting never changes. A dignified green parrot musician in a tuxedo plays his ukulele in a calm jazz club. His right hand strums gently down and up across the strings in a slow, steady rhythm the whole time, a small relaxed wrist movement right over the sound hole, while his left hand stays on the neck. First he bobs his head softly forward and back twice with the beat, his crest feathers bouncing a little. Then he closes his eyes in one slow, contented blink, enjoying the music. He ends exactly in his starting pose, beak pressed closed in a calm smile. The ukulele, his left hand, his tuxedo, his shoulders and the plain backdrop stay completely steady. Sound: a soft, quiet jazz-club room ambience only.
```

**lampart** (`jobs/prompts/lew/play-lampart.txt`):

```
[Static shot] The camera is locked and the lighting never changes. A dignified leopard musician in a tuxedo plays his ukulele in a calm jazz club. His right hand strums gently down and up across the strings in a slow, steady rhythm the whole time, a small relaxed wrist movement right over the sound hole, while his left hand stays on the neck. First his head tilts slowly to one side with the beat and his eyes close halfway, savouring the music. Then his head returns gently upright and his eyes open again in one slow, contented blink. He ends exactly in his starting pose, lips pressed together in a calm smile. The ukulele, his left hand, his tuxedo, his shoulders and the plain backdrop stay completely steady. Sound: a soft, quiet jazz-club room ambience only.
```

## Manifest (characters.json)
- **Per character:**
  - `home`, `cell` [360,360], `fps` 12, `frames` 51;
  - `pages` [{file, cols 11, rows 5, first 0}];
  - `play` [0,50], a loop where frame 0 is home and the frame after 50 is home again;
  - `strum_low` (frame indices);
  - `anchor` [180,360], the figure's bottom centre, which is the waist cut at the cell's bottom edge;
  - `figure_bbox_home`, `source_job`.
- **Cell layout:** frame i sits at ((i % 11) × 360, (i // 11) × 360) on its page.
