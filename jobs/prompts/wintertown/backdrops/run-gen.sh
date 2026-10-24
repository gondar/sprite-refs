#!/bin/sh
# The 7 full-screen backdrops for Stajenka after the owner's decisions of 2026-10-24 (the place fills the window,
# the tab floats on frosted glass over its top 30 %, a shallow strip of boards covers its bottom 16 %).
# Nano Banana Pro, 2K, 16:9: ~$0.09 each, ~$0.63 for all 7. Needs APIYI_API_KEY. Run from the repo root.
# The game reads a plate's floor row from FLOOR in stajenka.html: set FLOOR["plate-<id>"] = .84 for each new plate,
# and measure its LIGHTS, chimneys and mover paths again (scripts/wintertown_build.py) — they are fractions of the plate.
P=$(dirname "$0"); REF=${REF:-refs/wintertown/gen/plate-lake.webp}
for s in ${@:-town forest port mountains station lake stable}; do
  python3 skill/asset-sheet/scripts/gen_image.py --model gemini-3-pro-image --prompt-file "$P/bg-$s.txt" \
    --ref "$REF" --aspect 16:9 --size 2K --stream 1 --out "refs/wintertown/gen/bg2-$s.png" --tag "wintertown-bg2-$s" &
done; wait
# the port's lit lamp room, laid over the unlit lighthouse of bg-port with the beam drawn in code (one light in the
# port's sky, as the owner asked): Nano Banana, 1:1, ~$0.025, key with skill/asset-sheet/scripts/key.py
[ -z "$1" ] || [ "$1" = port ] && python3 skill/asset-sheet/scripts/gen_image.py --model gemini-3.1-flash-image \
  --prompt-file "$P/port-lamp.txt" --ref "refs/wintertown/gen/plate-port.webp" --aspect 1:1 --out "refs/wintertown/gen/port-lamp.png" --tag wintertown-port-lamp
