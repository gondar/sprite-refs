#!/bin/sh
# The donkey play (Stajenka, port) made smooth with MiniMax-H3, the sprite-pipeline §2 recipe at its cheapest:
# first frame = last frame = one home picture on flat blue, TWO movements per 4 s clip, one colour (blue: neither
# the grey donkey nor the brown townsman carries blue), no second colour test.
#   1 Nano Banana edit   townsman without his lantern, hands free              $0.025
#   4 H3 clips, 4 s      donkey-A (bray · stubborn lean) donkey-B (buck · proud hop)
#                        townsman-A (haul twice · fall and get up) townsman-B (shove twice · startled jump)   4 x $0.12
#   total ≈ $0.51. The walk on, the flight over the band and the rope stay in code (stajenka-acts.js).
# Needs APIYI_API_KEY. Run from the repo root, after `python3 scripts/wintertown_donkey_h3.py` and a push (H3
# downloads the home pictures from jsDelivr, pinned to the pushed commit).
set -e
P=jobs/prompts/wintertown/h3; S=skill/sprite-pipeline/scripts; A=skill/asset-sheet/scripts
SHA=$(git rev-parse HEAD); CDN="https://cdn.jsdelivr.net/gh/gondar/sprite-refs@$SHA/refs/wintertown/h3"
step=${1:-all}
if [ "$step" = edit ] || [ "$step" = all ]; then
  python3 $A/gen_image.py --model gemini-3.1-flash-image --prompt-file $P/townsman-edit.txt \
    --ref refs/wintertown/style/townsman-src.webp --aspect 16:9 --out refs/wintertown/h3/townsman-home.png --tag wintertown-townsman-home
  echo "LOOK at refs/wintertown/h3/townsman-home.png, then commit + push it and run: $0 clips"; exit 0
fi
if [ "$step" = clips ]; then
  for c in donkey-A donkey-B; do
    python3 $S/h3.py submit --tag wintertown-$c --prompt-file $P/$c.txt --duration 4 --ratio adaptive --first $CDN/donkey-home.png --last $CDN/donkey-home.png
  done
  for c in townsman-A townsman-B; do
    python3 $S/h3.py submit --tag wintertown-$c --prompt-file $P/$c.txt --duration 4 --ratio adaptive --first $CDN/townsman-home.png --last $CDN/townsman-home.png
  done
  echo "poll each: python3 $S/h3.py poll <job_id> --every 15 ; then cut with lock.py --pose-s 2"
fi
