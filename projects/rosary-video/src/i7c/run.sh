#!/bin/bash
# run.sh ID_name crop.png  -> ed/ID_name.jpg (+_raw.png); logs cost
n=$1; c=$2; S=/tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad
cd $S/i7c
for i in 1 2 3 4 5; do
  python3 $S/scripts/gen3.py gemini-3.1-flash-image-preview 1:1 ed/$n.jpg p/$n.txt $c > ed/$n.log 2>&1 && grep -q "ed/$n.jpg" ed/$n.log && { echo "$n ok try $i" >> calls.log; echo "{\"id\":\"${n%%_*}\",\"what\":\"cutout face edit $n\",\"model\":\"gemini-3.1-flash-image-preview\",\"usd\":0.0245}" >> $S/process/costs.jsonl; exit 0; }
  echo "$n fail try $i $(tail -c 200 ed/$n.log | tr '\n' ' ')" >> calls.log; sleep 40
done
