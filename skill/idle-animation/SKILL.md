---
name: idle-animation
description: Make a game character's IDLE feel alive instead of looping — a shuffled bag of short gestures that all start and end on one shared home frame, made with a cutout rig, MiniMax-H3 video, or a hybrid of both, chosen by context. Use whenever a character waits on screen (a conductor, a king on a throne, a mascot, a shopkeeper), when an idle "is irritating", "feels like the same animation", "is constant", or when someone asks for more idle variations. Covers the choice, the shared-home-frame contract, the bag player, the checks and the review before shipping. The making itself is in `sprite-pipeline` (MiniMax) and `skill/cutout` (cutout).
---

# Idle animation — variety on one home frame

An idle that loops one clip is noticed within seconds ("feels like it is the same one and constant"). What fixes it
is **variety**, not a better loop: several short gestures (0.8–2 s), every one starting and ending on **one shared
home frame**, played as a shuffled bag — never the same gesture twice running — with 0.4–2.2 s of stillness on the
home frame between them. Because every gesture meets the same frame, any order is seamless.

## 1. Choose the source — it depends on the character and the budget

| | **Cutout** (`sprite-refs/skill/cutout/SKILL.md`) | **MiniMax-H3** (`sprite-pipeline` §2) |
|---|---|---|
| What it is | the picture itself, bent by weight maps (head, torso, hand) + overlays cut from single-change image edits (blink, eyes left/right/down, smile …) | a 4 s video clip pinned at both ends to the picture, cut with the static lock (`lock.py`) |
| Good at | MANY small variations: blinks, glances, smiles, tilts, sway, breath, nods, glow pulses, combinations of them | REAL movement: a hand to the face, a head that turns, a sigh with the eyes closing, a shrug |
| Bad at | a limb travelling across the body (the beard touch ghosted), turning, anything big | quantity: ~two movements per $0.12 clip; MBs of frames |
| Static parts | identical by construction | identical through the lock (`--keep` the prop) |
| Cost | ≈ $0.025 per new face edit; every combination free | $0.12 per two free-running gestures; $0.24 for one gesture chained through a drawn peak pose (home → peak → home), which lands exactly where you drew it (+ a re-try budget) |

Pick by asking:
1. **What must move?** Only the face and small body sway → cutout. A hand, an arm, a head turn → MiniMax.
2. **How many variations, how often seen?** A character on screen for minutes needs 12–20 gestures → cutout carries
   the count. A character seen in short bursts gets by with 4–6 → MiniMax alone is fine.
3. **How big on screen?** Cutout motion is subtle by construction; below ~150 px it may not read — lean on MiniMax.
4. **What is attached?** A throne, desk or instrument that must never move is a separate static layer (cutout) or the
   `--keep` mask (MiniMax). Decide this before generating anything.
5. **Download budget?** Every atlas frame costs bytes (a 479×444 cell ≈ 10 KB in WebP). Count frames, not gestures.

**Both, for one gesture**: the cutout's single-change edits double as MiniMax peak poses. A move the cutout cannot
do cleanly (the King's hand to his beard ghosted as a crossfade) becomes two chained MiniMax clips through that
same edit — clean, and exactly the pose that was drawn (sprite-pipeline §2).

**Hybrid** — the usual answer for a main character: the cutout supplies the bulk (most of the bag), MiniMax supplies
two to four signature moves that only real video can do. Context decides the mix; neither alone is wrong.

## 2. The hybrid contract — one home frame for everything

- **ONE home frame, from ONE picture.** Both sources start from the same design picture, placed in the game's cell
  by the same transform (scale + bottom-centre pivot). Never take the home frame from an older clip or strip of a
  different render: two drawings crossfaded at every seam read as ghosting.
- **Prove the seam across sources**: frame 0 of every gesture, from either source, equals the home frame (mean
  |RGBA diff| < ~1; WebP noise between identical cells is ~4 on 0–255 — compare before compression when you can).
- **One manifest** listing every gesture with its source, frames and bag weight:
  `{"cell":[W,H],"pivot":[x,y],"fps":12,"gestures":[{"name":"blink2","src":"cutout","atlas":0,"at":0,"frames":14,"weight":3}, …]}`
  — one atlas per source is fine; the player resolves `atlas` + `at`.
- **Weights**: signature (MiniMax) moves rarer than small ones — e.g. weight 1 against 3 — and never two signature
  moves in a row. A big move every few seconds turns into a tic.

## 3. The player

A shuffled bag (Fisher–Yates, refilled when empty, skipping the gesture just played), a rest of 0.4–2.2 s on the home
frame between gestures, and a frame clock in milliseconds, never in rAF ticks. Beat-locked moves (a conductor's nod)
stay on the beat; the bag fills the gaps — the Mountain King nods on the downbeat and gestures between nods when it
fits before the next one. Worked example: MusicGames `fingerpick-warmup/index.html` (`SPR.idle`, `idleFrame`,
`nextGesture`, `kingListens`) and `tests/fingerpick-warmup.mjs` §5a (every gesture's ends equal the home frame, the
middles do not; a minute of the mixer plays every gesture and never repeats one back to back).

## 4. Checks before anyone sees it

1. `sprite-pipeline/scripts/score.py NAME=atlas.json …` for every source: throne/legs shimmer (≈0 for both methods),
   colour drift, seams, motion. Motion keeps you honest — a sprite that never moves wins the other three.
2. **Look at every gesture's peak frame at full size**, zoomed on the head and hands, next to its raw source (the clip
   frame, the edit). The score missed two crowns; a zoom found them at once.
3. A **review page** (the Mountain King's: claude.ai artifact "Mountain King Gestures") that plays the new idle next to
   what it replaces, as the game plays it, with a frame strip per gesture — the owner decides there, before any PR.
   Shipping art the owner has not seen moving cost a full redo on 2026-10-16.

## 5. Costs (2026-10)

Cutout: one rig ≈ $0.25 (8–10 edits), then ≈ $0.025 per new face. MiniMax: $0.12 per clip of two gestures, first clip
on two grounds when the character is new (+$0.12), one re-try per clip budgeted. A Mountain King hybrid of ~20
gestures: ≈ $0.65–0.90 in API calls.
