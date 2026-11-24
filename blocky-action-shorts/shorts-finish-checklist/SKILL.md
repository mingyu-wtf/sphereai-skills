---
name: shorts-finish-checklist
description: Render, assemble and check a vertical 3D short: background Blender renders, JPG sequences, gap check, ffmpeg at 1080x1920 60 fps, still sheets, upload checklist. 쇼츠 마무리 점검표.
---

# Shorts Finish Checklist

From section scripts to one finished vertical video, with checks at each step so problems are found in stills, not after an hour of rendering.

## 1. Render settings
- Resolution 1080x1920, 60 fps, set **after** any helper that resets fps.
- EEVEE is enough for blocky scenes. A few samples (32-64) and light motion blur.
- Run Blender in the background: `blender -b --factory-startup -P section.py`. `--factory-startup` keeps the user's add-ons and preferences out of the way.
- Output **JPG quality 95** sequences, not PNG (about 1/9 the size, no visible loss).
- Name frames by their **absolute frame number** on the shared timeline (`0448.jpg`, not `0001.jpg` for section B).
- One full render at a time on one PC.

## 2. Stills first
1. For each section, render one frame per shot at half resolution.
2. Tile them into one sheet: `ffmpeg -i still_%04d.jpg -vf "scale=540:-1,tile=4x2" sheet.jpg`.
3. Look at the sheet yourself before showing it. Check: anyone floating or sinking, faces covered, a key action off screen, colour tone jumping between shots, effects visible too early, empty frames.
4. Fix, re-render the stills, then render the section.

## 3. Assemble
1. Gather every section's frames and sort them **numerically** (frame 10000 sorts before 9999 as text).
2. **Gap check**: every number from first to last must exist. Stop and report the missing range if not.
3. Encode: `ffmpeg -framerate 60 -start_number <first> -i %04d.jpg -c:v libx264 -crf 16 -pix_fmt yuv420p -r 60 out.mp4` (use a file list for mixed digit counts).
4. Apply speed changes with `speed-ramp-quick-slow` if planned.

## 4. Before upload
- [ ] Length 25-35 s; the conflict is visible in the first second
- [ ] Every key act is on screen; both sides of every hit are in frame
- [ ] No floating feet, no covered faces, no off-screen hits
- [ ] One lighting tone across shots
- [ ] Watched once at full speed on a phone-size screen
- [ ] Characters, textures and sounds are original or licensed; no game logos or trademarked names in the title
- [ ] Final file is H.264, yuv420p, 1080x1920, 60 fps

## Output
The finished vertical mp4, the review sheet per section, and a list of what was fixed.

---
만든이: sphereai.work (https://sphereai.work)
