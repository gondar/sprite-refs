#!/usr/bin/env bash
# Etap A dla 14 nowych tajemnic — uruchom, gdy klucz APIYI znów działa.
# Użycie: cd <scratchpad> && bash process/resume_phaseA.sh [ID ...]
set -u
cd "$(dirname "$0")/.."
code=$(curl -s -o /dev/null -w "%{http_code}" -m 20 https://api.apiyi.com/v1/models)
if [ "$code" != "200" ]; then echo "APIYI nadal nie działa (HTTP $code) — przerywam."; exit 1; fi
IDS=${*:-"R3 R4 R5 S3 S4 S5 B2 B3 B4 B5 C2 C3 C4 C5"}
for s in $IDS; do
  case $s in
    R*) out=scripts/i5/R3R5/${s}_full_a.jpg
        bash scripts/i5/retry.sh gemini-3-pro-image-preview 16:9 $out scripts/i5/R3R5/${s}_full.txt scripts/i5/v2/ref_B1.jpg scripts/i5/v2/ref_C1.jpg scripts/i5/v2/ref_R1.jpg ;;
    S*) D=scripts/i5/S345; out=$D/${s}_v1.jpg
        MAXW=1376 TRIES=4 bash scripts/i5/S1/retry.sh 16:9 $out $D/${s}_full.txt $D/ref_S1.jpg $D/ref_B1.jpg $D/ref_R1.jpg ;;
    B*) out=scripts/i5/B/${s}_a.jpg
        MAXW=1376 bash scripts/i5/retry.sh gemini-3-pro-image-preview 16:9 $out scripts/i5/B/${s}_full.txt scripts/i5/B/ref_B1.jpg scripts/i5/B/ref_R1.jpg ;;
    C*) out=scripts/i5/Cg/${s}_a.jpg
        bash scripts/i5/retry.sh gemini-3-pro-image-preview 16:9 $out scripts/i5/Cg/${s}_full.txt scripts/i5/Cg/ref_C1.jpg scripts/i5/Cg/ref_R1.jpg ;;
  esac
  if [ -s "$out" ]; then cp "$out" pub/i5/${s}_full.jpg; echo "{\"id\":\"$s\",\"what\":\"full\",\"model\":\"gemini-3-pro-image-preview\",\"usd\":0.09}" >> process/costs.jsonl; echo "OK $s"; else echo "BRAK $s"; fi
done
