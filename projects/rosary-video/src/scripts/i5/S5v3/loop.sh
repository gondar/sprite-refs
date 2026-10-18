#!/bin/bash
# loop.sh out prompt label refs...   (retries 502, logs cost on success)
cd /tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad
out=$1; pr=$2; label=$3; shift 3
for i in $(seq 1 ${TRIES:-8}); do
  r=$(IMGSIZE=1K timeout 320 python3 scripts/gen3.py ${MODEL:-gemini-3-pro-image-preview} ${AR:-16:9} $out $pr "$@" 2>&1 | tail -1 | cut -c1-200)
  echo "$(basename $out) try$i $r"
  if echo "$r" | grep -q "jpg ("; then echo "{\"id\":\"S5\",\"what\":\"$label\",\"model\":\"${MODEL:-gemini-3-pro-image-preview}\",\"usd\":${USD:-0.07}}" >> process/costs.jsonl; exit 0; fi
  sleep 45
done; exit 1
