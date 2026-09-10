#!/usr/bin/env bash
# Encode rendered PNG sequences -> mp4 (h264, yuv420p, faststart) + a poster frame.
# Usage:  bash build/assemble.sh <renders_subdir> <out_name> [fps]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SUB="${1:?renders subdir}"
NAME="${2:?out name}"
FPS="${3:-30}"
SRC="$ROOT/deliverables/renders/$SUB"
OUT="$ROOT/deliverables/video"
mkdir -p "$OUT"

ffmpeg -y -framerate "$FPS" -i "$SRC/f%03d.png" \
  -c:v libx264 -profile:v high -crf 17 -preset slow -pix_fmt yuv420p \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -movflags +faststart \
  "$OUT/$NAME.mp4"

# looping gif-style preview (smaller, 12fps)
ffmpeg -y -framerate 24 -i "$SRC/f%03d.png" \
  -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p \
  -vf "scale=900:-2" -movflags +faststart \
  "$OUT/${NAME}_web.mp4"

# poster = middle frame
CNT=$(ls "$SRC"/f*.png | wc -l)
MID=$(printf "f%03d.png" $((CNT/2)))
cp "$SRC/$MID" "$OUT/${NAME}_poster.png"
echo "wrote $OUT/$NAME.mp4  (+_web, +_poster)"
