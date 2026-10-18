#!/bin/bash
# usage: retry.sh model ar out prompt [refs...]
cd /tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad
for i in $(seq 1 ${TRIES:-4}); do
  r=$(IMGSIZE=1K python3 scripts/gen3.py "$@" 2>&1 | tail -1 | cut -c1-200)
  echo "$(basename $3) try$i $r"
  echo "$r" | grep -q "jpg" && exit 0
  sleep 40
done
exit 1
