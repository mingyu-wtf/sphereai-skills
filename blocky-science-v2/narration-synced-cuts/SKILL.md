---
name: narration-synced-cuts
description: Place Blender cuts and cameras on narration sentence times, render by section as JPG sequences and assemble with the narration and a gap check. 나레이션에 맞춘 컷 배치와 조립.
---

# Narration-synced Cuts

## 1. One timeline
- **Frame = narration second x fps + 1.** Every section script and every text card uses this.
- Example at 24 fps: a block starting at 17.33 s starts at frame 417.
- Pick fps once per episode (24 or 30) and set it in every script.

## 2. Sections
- One section per script block, or split a long block.
- Start the script with a header comment: section name, narration time, and each shot's frame range with its sentence.
- A script must be safe to run again: it wipes and rebuilds only its own scene.

## 3. Cuts on sentences
- A cut lands at a **sentence start** (from the sentence frame table).
- Shot length: a few seconds. If one idea needs longer, move the camera inside the shot.

## 4. Stills, then render
1. Render one still per shot (half resolution), tile into a sheet and check it.
2. Fix and repeat until clean.
3. Render the section as a **JPG 95** sequence named by absolute frame number, in the background (`blender -b --factory-startup ...`).
4. To fix one shot, re-render only that shot's frame range.

## 5. Assemble
1. Collect all sections' frames, sort **numerically**, and check there is no gap from first to last frame.
2. Encode with the full narration: `ffmpeg -framerate <fps> -i ... -i narration.wav -c:v libx264 -crf 16 -pix_fmt yuv420p preview_full.mp4`.
3. Watch the whole preview once before adding text.

## Output
One script per section, a still sheet per section, JPG frames, and `preview_full.mp4` (3D + narration, no text). Next: `text-overlay-remotion`.

---
만든이: sphereai.work (https://sphereai.work)
