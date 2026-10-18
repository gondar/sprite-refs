#!/usr/bin/env bash
# Cały film do MP4: bash process/make_film.sh <out.mp4> [fps=30] [workers=3] [crf=20]
# Klatki renderuje render_frames.js równolegle, potem ffmpeg dokłada muzykę.
set -eu
cd "$(dirname "$0")/.."
OUT=$1; FPS=${2:-30}; WK=${3:-3}; CRF=${4:-20}
export NODE_PATH=$(npm root -g)
DUR=$(grep -o 'DUR=[0-9.]*' pub/index.html | head -1 | cut -d= -f2)
N=$(python3 -c "print(round($DUR*$FPS))")
rm -rf film/fr; mkdir -p film/fr
pids=()
for w in $(seq 0 $((WK-1))); do
  a=$((N*w/WK)); b=$((N*(w+1)/WK))
  node process/render_frames.js film/fr $FPS $a $b > film/log_$w.txt 2>&1 & pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
cat film/log_*.txt | grep -h '^{' 
ffmpeg -y -loglevel error -framerate $FPS -i film/fr/f%05d.jpg -i pub/utwor.mp3 -map 0:v -map 1:a \
  -c:v libx264 -preset slow -tune animation -crf $CRF -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$OUT"
