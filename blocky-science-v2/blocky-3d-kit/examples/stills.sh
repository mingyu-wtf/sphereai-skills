# Build one script in this folder, render the given frames, make a contact sheet.
# usage (Git Bash):  NAME=walk_basic bash stills.sh 30 100 145
#   -> st/s_0045.png ... and st/sheet.png (3 columns, 1920 px wide)
# Works for any folder: copy this file next to your test script. NAME = script file name without .py
B="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"   # set BLENDER=... if Blender is elsewhere
S="$(cd "$(dirname "$0")/../scripts" && pwd -W)"   # the kit scripts folder
D="$(cd "$(dirname "$0")" && pwd -W)"
N="${NAME:-walk_basic}"
cd "$D" || exit 1
"$B" -b --factory-startup -P "$S/bg_build.py" -- "$D/$N.py" "$D/$N.blend" 2>&1 | grep -E "SAVED|Error|Traceback|line [0-9]+"
[ -f "$N.blend" ] || { echo "BUILD FAILED: read the Traceback above"; exit 1; }
mkdir -p st; IN=""; n=0
for f in "$@"; do
  "$B" -b "$N.blend" -P "$S/vol_handler.py" -o "//st/s_####" -F PNG -f "$f" 2>&1 | grep -E "Error|Traceback"
  IN="$IN -i st/s_$(printf %04d "$f").png"; n=$((n+1))
done
if [ "$n" -eq 1 ]; then cp "st/s_$(printf %04d "$1").png" st/sheet.png; echo "SHEET $D/st/sheet.png"; exit 0; fi
L=""; for ((i=0;i<n;i++)); do c=$((i%3)); r=$((i/3)); x=0; for ((k=0;k<c;k++)); do x="$x+w0"; done; y=0; for ((k=0;k<r;k++)); do y="$y+h0"; done; L="$L|${x}_${y}"; done
ffmpeg -y -loglevel error $IN -filter_complex "xstack=inputs=$n:layout=${L:1}:fill=black,scale=1920:-1" st/sheet.png && echo "SHEET $D/st/sheet.png"
