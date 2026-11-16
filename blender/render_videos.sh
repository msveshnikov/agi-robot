#!/bin/bash
# Render the NOVA animations with EEVEE (PNG frames, resumable) and encode MP4s.
# Usage: bash render_videos.sh [scene ...]      (default: all)
#        EEVEE_SAMPLES=16 bash render_videos.sh studio
cd "$(dirname "$0")"
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
SCENES=${@:-studio livingroom mars neon exploded}
mkdir -p out/videos
for s in $SCENES; do
  echo "=== $s"
  "$B" -b -P scenes.py -- $s video 2>&1 | grep -E "\[video\]|Error|Traceback"
  ffmpeg -y -loglevel error -framerate 24 -i "out/frames/$s/f_%04d.png" \
    -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
    "out/videos/nova_$s.mp4" && echo "encoded out/videos/nova_$s.mp4"
done
# showreel: all clips back to back
: > out/videos/list.txt
for s in neon studio livingroom mars exploded; do
  [ -f "out/videos/nova_$s.mp4" ] && echo "file 'nova_$s.mp4'" >> out/videos/list.txt
done
(cd out/videos && ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy nova_showreel.mp4 && echo "encoded showreel")
