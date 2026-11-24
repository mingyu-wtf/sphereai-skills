---
name: blocky-render-review
description: Check blocky Blender scenes before rendering (V2 kit) - still sheets, a look checklist and fixes for the most common defects such as streak glare, burnt highlights, white blobs, cut-off heads and skating feet. 블록 3D 장면 검수 기본.
---

# Blocky Render Review (basic)

Uses `blocky-3d-kit`. A long render takes hours; finding a broken shot afterwards is expensive. **Check stills first.**

## 1. Stills before any long render
```bash
NAME=my_cut bash stills.sh 30 100 145      # one frame from the middle of each shot, plus before and after each event
```
Open `st/sheet.png` yourself and check:
1. No cell fully black or white (black = camera inside an object, white = too much glow).
2. The subject is in frame; heads are not cut.
3. Blocks read as blocks: cube faces have different brightness.
4. Bright areas keep colour (sun, water, windows).
5. Glare is round, not a cross of streaks.
6. The edges are not empty.

Change one thing at a time and re-render only 2-3 stills of that shot.

## 2. Common defects
| What you see | Fix |
|---|---|
| Cross or streak glare | `BF.look3(L)` right after `render_setup` |
| Bright areas burn white or yellow | `BF.grade3(L)`; still burning -> lower that object's emission |
| White blob around an effect | lower emission |
| Frame fully black or only a wall | the camera is inside an object; check its coordinates |
| Comet hidden | build clouds last with `keep_rays` |
| Head cut off | wider lens or aim lower |
| Feet skate | walk with `CR.walk_to`, not `move` |
| Pose jumps after a walk | key the pose from `f1+2` |
| Blinks overwrite faces | call `auto_blink` last |

## 3. After the render
- One full render at a time. Check that the frame count and the video length match the narration.
- Look through the finished video as a frame sheet: `ffmpeg -v error -y -i cut.mp4 -vf "fps=1/2.5,scale=384:-1,tile=5x5" -q:v 3 rev_%02d.jpg` (cell number x 2.5 s = time).

## Output
Still sheets where every shot passes, and the frame sheets of the finished cut.

---
만든이: sphereai.work (https://sphereai.work)
