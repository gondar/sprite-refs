#!/bin/sh
# The Stajenka finale after the owner's ask of 2026-10-24: an EMPTY stable plate, and the cast as separate cut-outs that
# walk to it (Joseph leading Mary on the donkey first, then shepherds with sheep, carollers, townsfolk), the Holy
# Family group placed inside once they have arrived.
#   plate-stable-empty  Nano Banana Pro, 2K, 16:9 (the backdrops' layout: calm sky 30 %, boards 16 %)   $0.09
#   cast-sheet          Nano Banana Pro, 1:1, 12 figures on green, cut by cut_assets.py --grid 3x4     $0.09
#   total ≈ $0.18. Needs APIYI_API_KEY. Run from the repo root.
set -e
P=jobs/prompts/wintertown/nativity; A=skill/asset-sheet/scripts
python3 $A/gen_image.py --model gemini-3-pro-image --prompt-file $P/plate-stable-empty.txt --ref refs/wintertown/gen/plate-stable.webp \
  --aspect 16:9 --size 2K --stream 1 --out refs/wintertown/gen/plate-stable-empty.png --tag wintertown-stable-empty
python3 $A/gen_image.py --model gemini-3-pro-image --prompt-file $P/cast-sheet.txt --ref refs/wintertown/gen/plate-stable.webp \
  --aspect 1:1 --size 2K --stream 1 --out refs/wintertown/gen/sheet-nativity.png --tag wintertown-nativity-cast
python3 $A/cut_assets.py refs/wintertown/gen/sheet-nativity.png $P/cast-items.txt sheets/wintertown/nativity --grid 3x4
echo "LOOK at sheets/wintertown/nativity/check.png and refs/wintertown/gen/plate-stable-empty.png before wiring them in"
