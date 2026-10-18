cd /tmp/claude-0/-home-user/7ead4a65-9a3f-5f74-8eac-6850f8d7f07d/scratchpad
for s in R1 R2; do for k in plate green; do
  scripts/i5/retry.sh gemini-3-pro-image-preview 16:9 pub/i5/${s}_${k}.jpg scripts/i5/$s/$k.txt scripts/i5/$s/in.jpg
done; done
