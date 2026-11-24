# Build one cut script, render a frame range as JPG (quality 95), then make an mp4 (optionally with narration).
# usage (Git Bash / macOS / Linux):
#   NAME=walk_basic bash render.sh 1 150                         -> render/walk_basic/####.jpg + render/walk_basic.mp4
#   NAME=cut03 AUDIO=../audio/narration.wav bash render.sh 3456 6851   -> audio is cut from (start-1)/fps seconds
#   NAME=cut03 bash render.sh 4673 4928   -> after fixing one shot: rebuilds the script, re-renders ONLY these frames
#                                            (JPGs outside the range are kept) and remakes the mp4 from all frames
#   FPS=30 by default. Set BLENDER=... if Blender is not in the default Windows location.
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
S="$(cd "$(dirname "$0")/../scripts" && (pwd -W 2>/dev/null || pwd))"
D="$(cd "$(dirname "$0")" && (pwd -W 2>/dev/null || pwd))"
N="${NAME:?set NAME=<script name without .py>}"
FPS="${FPS:-30}"
A0="$1"; A1="$2"
[ -n "$A0" ] && [ -n "$A1" ] || { echo "usage: NAME=x bash render.sh <start> <end>"; exit 1; }
cd "$D" || exit 1
"$B" -b --factory-startup -P "$S/bg_build.py" -- "$D/$N.py" "$D/$N.blend" 2>&1 | grep -E "SAVED|Error|Traceback|line [0-9]+"
[ -f "$N.blend" ] || { echo "BUILD FAILED: read the Traceback above"; exit 1; }
mkdir -p "render/$N"
T0=$(date +%s)
"$B" -b "$N.blend" -P "$S/vol_handler.py" --python-expr "import bpy; bpy.context.scene.render.image_settings.quality = 95" \
  -o "//render/$N/####" -F JPEG -s "$A0" -e "$A1" -a 2>&1 | grep -E "Error|Traceback"
echo "RENDERED $N $A0-$A1 in $(( $(date +%s) - T0 )) s"
# mp4 from ALL frames that exist in render/<NAME>/ (so a partial re-render still gives the whole cut)
FIRST=$(ls "render/$N" | grep -E '^[0-9]{4}\.jpg$' | sort | head -1 | cut -c1-4)
CNT=$(ls "render/$N" | grep -cE '^[0-9]{4}\.jpg$')
if [ -n "$AUDIO" ]; then
  SS=$(python -c "print(($((10#$FIRST)) - 1) / $FPS)")
  ffmpeg -y -loglevel error -framerate "$FPS" -start_number "$((10#$FIRST))" -i "render/$N/%04d.jpg" -ss "$SS" -t "$(python -c "print($CNT / $FPS)")" -i "$AUDIO" \
    -map 0:v -map 1:a -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -b:a 192k -shortest "render/$N.mp4"
else
  ffmpeg -y -loglevel error -framerate "$FPS" -start_number "$((10#$FIRST))" -i "render/$N/%04d.jpg" -c:v libx264 -pix_fmt yuv420p -crf 18 "render/$N.mp4"
fi
echo "VIDEO $D/render/$N.mp4 ($CNT frames from $FIRST)"
