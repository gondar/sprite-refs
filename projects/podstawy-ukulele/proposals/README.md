# Mnemonic proposals (for the owner to pick; NOT used by the page)

PL „Grube Czarownice Edukują Alpaki” and EN “Good Cats Eat Apples”, redrawn in the style of the kirigami kid
(`../kid-hold.webp`, `../../kirigami/child-uke.webp`): layered matte cardstock and felt, the same ivory / cranberry /
honey palette, the same rounded proportions, dot eyes and small smiles, the same warm light from the upper left.
Comparison sheet: `mnemonic-proposals.png` in the build scratchpad (sprite-refs).

Each version: `scene-pl.webp` and `scene-en.webp` (1024×768, 4:3, opaque, made to sit under the strings: 390 px wide on a
phone = 292 px tall) and `layers/` (transparent cut-outs of the same characters, keyed off flat blue #2F6BD8, for animation;
draft size, ≤ 430 px; regenerate the chosen ones at full size on #2F6BD8 for MiniMax).

| version | PL scene | EN scene | layers | MiniMax animation (first frame = last frame, on #2F6BD8) |
|---|---|---|---|---|
| **V1 classroom & blackboard** | a plump witch teacher points her pointer at a blackboard with G C E A; two alpacas at a school desk | the same classroom: a honey cat teacher points at G C E A, two cats at the desk munch red apples | witch-pointing, alpacas-desk, blackboard (letters on it), cat-teacher, cats-desk-apples, apple | the witch taps the pointer on the board 4 times (G, C, E, A) while the alpacas nod; EN: the cat teacher taps, the pupils take a bite |
| **V2 the ukulele band** | the plump witch sits on a stump strumming a uke (neck to the viewer's right), two alpacas stand beside her each with a uke | the same hill: a cat strums on the stump under an apple tree, two cats eat apples | witch-uke, stump, alpaca-uke-1, alpaca-uke-2, cat-uke, cat-apple | the witch strums down-up and bobs, the alpacas sway and strum along; EN: the cat strums, the other two take a bite each |
| **V3 forest-school diorama** | a shadow-box forest at golden light, the plump witch on a broom reads from a book, three alpacas listen by a cottage | the same diorama with apples hanging on threads instead of stars: a cat bites an apple, two cats with a basket | witch-broom, alpaca-hoof, alpaca, cat-apple | the witch bobs on the broom and turns a page; the front alpaca raises its hoof and puts it down; EN: the cat lifts the apple and bites |

Models: Nano Banana Pro (`gemini-3-pro-image`) through APIYI; scenes with the kid as the style reference, EN scenes with
their PL partner as the reference, layers with both scenes as references; the witches were then made plump („Grube”) with
one edit each. The blackboard letters are painted (a zig-zag G C E A); for a pluck-synced animation the page can cover
them and draw its own.
