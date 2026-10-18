#!/bin/bash
# usage: retry.sh ar out prompt [refs...]  (gen3s.py, 1K, 40 s waits)
cd /tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad
for i in $(seq 1 ${TRIES:-6}); do
  r=$(IMGSIZE=1K python3 scripts/i5/gen3s.py gemini-3-pro-image-preview "$@" 2>&1 | tail -1 | cut -c1-300)
  echo "$(basename $2) try$i $r"
  echo "$r" | grep -q "jpg" && exit 0
  sleep 40
done
exit 1
