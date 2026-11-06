# Prompting a game animation GIF

**Round 2 (2026-11-06) is what works**: the edits route with the character's art as `--ref`, no
`complexity` field, `background: transparent`. With those, the prompts in `assets/example-prompts.json`
("working") gave coherent GIFs: the same face, markings and costume in every frame. The structure below
still applies; the "rejected" notes further down are from round 1 (complexity low, no reference).

Extra lines that helped in round 2: name the character as it appears in the reference sheet; "exactly four
legs, clearly separated"; "runs on the spot … never travels across the picture"; "the body, head and eyes keep
exactly the same shape, size and position in every frame; only the eyelids, that ear and the tail tip move".

Learned from four calls (2026-11-05). Few, so treat these as a starting recipe, not law.

## The structure that worked

1. **Who, how framed**: "A small cute black cat sits upright, seen from the front at a slight three-quarter
   angle" / "seen exactly from the side, facing LEFT".
2. **Ground**: for anything you will cut out, "on a perfectly flat solid medium-blue background (#2F6BD8)
   with no floor, no shadow and no scenery". Choose a key colour far from the character (blue for a black
   cat with green eyes; green for a blue character; never magenta near pink).
3. **Style in one sentence** taken from the game's existing art ("Spooky-cute 2D game sticker style: soft
   painterly shading, black fur with a faint violet rim light, big round glowing lime-green eyes").
4. **The motion as two or three named beats**: "it blinks once slowly, its left ear gives one quick
   twitch, and the tip of its tail curls and uncurls". Small, specific, in-place.
5. **Lock everything else**: "stays in exactly the same place and size", "the camera is completely
   stationary", for a walk "walks on the spot … never moves across the picture".
6. **Loop**: "Seamless loop that ends on the same pose it starts with" / "the last step leads straight back
   into the first".
7. **Exclusions**: "No text, borders, motion lines, multiple cats, multiple views, or spritesheet layout."

## What the model did with it

**Overall: rejected.** All four GIFs repaint the character every frame (features change size and shape,
legs fuse and split). The points below are what the prompt did control; they did not make the result usable.

- Loops closed well every time (seam ratio 0.94–1.39).
- In-place framing held: the background border moved < 1.3/255 on keyed grounds, feet stayed on one row.
- It sometimes adds a cartoon **motion line** anyway (frame 4 of the idle) → remove in post
  (`--largest-component`).
- A flat ground came back flat, but it **lights the character's rim in the ground colour** and draws a
  soft contact shadow despite "no shadow" → `--despill`, and accept a faint dark edge under the feet.
- Named colours drift between calls: "lime-green eyes" gave hue 82° once and 134° the next → fix in post
  (`--shift-hue`) or accept that each animation is a slightly different character.
- Walk cycles: legs fuse into one shape and split again; the visible leg count changes. Not usable.
- Timing words ("slowly", "quick") map loosely onto frames; set the real pace in the game, from the
  manifest, not from the prompt.

## Patterns worth reusing

| animation | frames × ms | beats to name |
|---|---|---|
| sleeping / breathing | 6 × 180 | torso expands and contracts, head rises slightly, tail tip twitch |
| sitting idle | 8 × 160 | slow blink, one ear twitch, tail tip curl |
| purring | 8 × 150–180 | eyes slowly closing, tiny body vibration, soft tail sway |
| happy reaction | 8 × 120–150 | ears perk up, one paw raised, small bounce, back to neutral (not a loop: say "ends in the start pose") |
| in-place walk | 8 × 110 | legs step in a natural gait, slight body bob, small tail sway, "never moves across the picture" |
| tail wag (dog) | 6 × 120 | tail wags left-right twice, body still |

For an instrument or anything with a right answer (a chord shape, a fingering), keep it out of the GIF or
draw it in code: the model will not keep a fret or a finger exact across frames.
