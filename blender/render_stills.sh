#!/bin/bash
# Final stills (Cycles CPU). Usage: bash render_stills.sh [samples] [scenes...]
cd "$(dirname "$0")"
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
S=${1:-64}; shift
SCENES=${@:-studio hero_dark livingroom mars neon exploded macro printbed}
for s in $SCENES; do
  "$B" -b -P scenes.py -- $s still $S 100 2>&1 | grep -E "\[still\]|Error|Traceback"
done
