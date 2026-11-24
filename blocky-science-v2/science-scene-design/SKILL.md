---
name: science-scene-design
description: Turn science ideas into blocky Blender scenes: the pixel-box look, cross-sections, size comparisons and fixed-camera time-lapses, with simple staging rules. 과학 개념을 블록 장면으로.
---

# Science Scene Design

Claude writes the scene scripts in Blender Python from these rules. Build a small library of helpers once (box with pixel texture, camera, sky) and a props file per episode that later episodes can reuse.

## 1. The look
- Big boxes in **1/16 m pixel units**, each face with a small **pixel texture** drawn in code (16x16), **Closest** interpolation so pixels stay sharp.
- Many identical things (insects, trees): one source collection + collection instances.
- EEVEE, 1920x1080, 24-30 fps, 32-64 samples.
- Never pure black for space or night: keep a deep navy.
- Original assets only; follow the blocky style, never a game's official characters, textures, logos or UI.

## 2. Idea -> scene patterns
| Idea | Scene |
|---|---|
| Inside the Earth, ice, soil | **Cross-section diorama**: cut the object in half and show the layers |
| Size comparison | **Objects side by side, popping in one by one** |
| Over time | **Time-lapse from one fixed camera**: blocks grow, change or vanish |

## 3. Staging
- One section = one scene. Switch cameras with timeline markers.
- Even still diagram shots move a little: a slow rotation or push-in.
- The key object is the brightest thing in the frame.
- People: simple faceless block figures, only when needed.

## Output
A props file for the episode and a list of which pattern each block of the script uses. Next: `narration-synced-cuts`.

---
만든이: sphereai.work (https://sphereai.work)
