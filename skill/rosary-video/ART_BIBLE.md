# Paciorki światła — art bible

Owner decisions so far, collected over 7 iterations. Every scene is judged against this file. Owner quotes are in Polish.

## What the film is
- A ~3:40 music video for children before their First Communion. Track: "Triplet Sway", instrumental, 117.5 BPM, 12/8, one bar = 2.0434 s.
- **Main goal: remembering all 20 rosary mysteries.** Each mystery must be instantly recognisable, and the viewer must always know which part and which number it is.
- **Timing:**
  - Intro: 4 bars (~9 s).
  - 20 mysteries: 5 bars each (10.217 s).
  - Outro: ~6.6 s.
  - Cuts land on the bar's downbeat.
- **Thread:** a hazel dormouse (orzesznica) chases a small golden bead of light. The bead jumps through history and she follows, landing in each mystery and watching it. There is no physical portal; the light carries her.

## Look
- **Visual language:** Cartoon Saloon / Tomm Moore (Secret of Kells, Song of the Sea, Wolfwalkers).
  - Flat graphic shapes.
  - Celtic spirals in nature: trees, water, light, wind.
  - Visible pencil line.
  - Gouache texture.
- **Approved reference scenes:**
  - Gethsemane B1 (`i5/B1_full.jpg`).
  - Resurrection C1 (`i5/C1_full.jpg`).
  - The new low-key Annunciation R1 (`i5/R1_full.jpg`).
  - The new Visitation R2 and Baptism S1 are the target tone for Joyful and Luminous scenes.
- **Poverty and simplicity, never pathos.** "za mało biedy Maryi i prostoty", "zbyt ułożone", "uciekamy od patatyzmu".
  - Rough mud-brick, a dirt floor, a clay jar, a mat, an oil lamp, patched homespun clothes, bare feet.
  - Nothing ornamental, no jewellery, no decorative arches, no "church painting".
- **Candid, slightly asymmetric compositions,** as if we caught a moment. Tools and objects are left where they were used.
- **Holiness is shown only through light:**
  - A soft circle of light, spiral rays, an angel made of light.
  - Never gold-plate halos or heavy gold.
- **Not too bright, not candy, not storybook-cute.** "tło za jasne", "zbyt bajkowy chrzest".
  - Low key, a single warm light source, deep shadows.
  - The Joyful mysteries are dawn, not pastel noon.
- **Each part has its own time of day and palette:**

  | Part | Time of day | UI colour |
  |---|---|---|
  | Radosne | dawn, dim earthy | #cfe6c4 |
  | Światła | harsh noon, ochre and olive | #3dbfb0 |
  | Bolesne | night, indigo with one crimson accent | #c8475c |
  | Chwalebne | golden dawn on cool blue-grey | #f6c35b |

- **Sorrowful mysteries:** symbolic and calm, no blood, nothing scary.
- **No text inside the painted images.** Captions are drawn by the engine.

## People
- **Figures are intimate, human, mid-gesture,** a little tender or playful. The angel whispers into Mary's ear; Elizabeth laughs.
- **Mary is a poor village girl of about 14–15:** barefoot, patched dress, rough head cloth, working hands.
- **Figures must live.** "animacja Maryi i anioła jest zbyt statyczna".
  - Every figure gets a cutout idle bag: blink, glance, breath, small head tilt, lips.
  - Every figure also gets slow code motion (breath, lean).
  - Movements stay small and tender, nothing theatrical.

## The dormouse
- **Design:** golden-ginger, cream belly, big dark eyes, small round ears, big spiral fluffy tail; storybook-flat.
- **Approved animation:** the MiniMax actions in `i6/dm/` ("orzesznica sama super").
- **In the scene she must look like she belongs there:**
  - A contact shadow.
  - The scene's light and colour on her fur.
  - Scale about 14% of frame height.
  - Feet on real surfaces.
  - Never over a face or the key action.
- **"Światło ma zejść do niej".** The bead comes down to her and hovers near her head while she watches the mystery; its warm light falls on her.
- **Jumps must read as jumps,** not slides. Anticipation (crouch), take-off, an arc, landing with squash, settle; about 1.4–1.6 s. "widać, że się przesuwa zamiast skakać".
- **Fewer, more deliberate moves beat a busy route.** Land, sniff, notice, watch, react, leave.

## Background life
- Every background has small moving details: leaves or curtains swaying, flame flicker, dust in light shafts, water shimmer, sun or moon pulse, fireflies.
- All of them are subtle, and none may show seams or ghost edges.

## Transitions
- Approved, played in turn: Rozbłysk, Trójspirala, Złota nić, Róża, Kometa, Kropla.
- Rejected: Promienie (rays), Plecionka kręgów (circle weave).

## Caption
- **Placement:** visible for the whole mystery, from landing to exit, on a calm area at the side or bottom.
- **Content:**
  - "TAJEMNICE <PART> · n" with 5 dots.
  - The mystery name, large, in Uncial.
- **Readable on a phone.** It must not cover figures or the dormouse.

## Hard fails (any one means the scene is rejected)
1. The event is not recognisable within about 2 s for an 8-year-old.
2. Wrong part palette or time of day, or the scene is too bright or pastel.
3. Pathos, ornament, wealth, churchy gold, or posed symmetry.
4. Any figure frozen for more than about 3 s with no idle life.
5. The dormouse slides instead of walking or jumping, floats without a shadow, has the wrong colour against the scene, or covers a face or the key action.
6. The bead does not come to the dormouse.
7. Visible seams, ghost edges, doubled features, keying fringe, or flicker artefacts.
8. The caption is missing, unreadable, or covering important content.
9. Text, letters or a signature inside the painted image.
