---
name: blocky-character-acting
description: Design original blocky characters in Blender Python and make them act: jointed boxes, pixel faces, expressions, simple poses and walks, feet on the ground. 블록 캐릭터 설계와 기본 연기.
---

# Blocky Character Acting

Claude writes the character builder and the animation itself, in Blender Python, from the rules below. Build it once, reuse it in every short.

## 1. Build the character
- **Unit**: 1 pixel = 1/16 m. A character is about 2 m tall (32 px). Head 8x8x8 px, body 8x4x12, arms and legs 4x4x12.
- **Origin at the feet, facing -Y.** Then placing a character is just its floor position and a Z rotation.
- **One box per part**: head, torso, two upper arms + forearms, two thighs + shins. Put each part's origin at its joint (shoulder, elbow, hip, knee, neck) so rotating it bends correctly.
- **Pixel textures per face of the box**, drawn in code as small images (16x16 or 8x8), with **Closest** interpolation so pixels stay sharp.
- **Faces are textures, not geometry.** Make one face image per expression (normal, blink, happy, angry, shocked, scared) and switch with a constant keyframe.
- **Characters are data.** Keep a spec per character (hair, eyes, jacket, shirt, pants, shoes colours, accessories). A new character = copy a spec and change the clothes.
- Original designs only. No official game characters, skins or textures.

## 2. A small animation API
Write helper functions so shot scripts stay short:

| Helper | Does |
|---|---|
| `rest(ch, f)` | key all joints to neutral at frame f |
| `pose(ch, f, joint=(x,y,z))` | key some joints in degrees |
| `face(ch, f, name)` | switch expression |
| `walk / run(ch, f0, f1)` | cycle legs and arms between two frames |
| `move(obj, [(f, (x,y,z))])`, `turn(obj, [(f, deg)])` | root motion |

## 3. Basic acting
1. Before a big move, a small move the other way (crouch before a jump, pull back before a punch).
2. After a strong pose, hold it for a moment before the next move.
3. Change the face before the action, not after.
4. When the knees bend, lower the hips so the feet stay on the ground.
5. Check one still per shot before rendering.

## Output
A reusable character builder script, one spec per character, and section scripts that animate the shot list.

---
만든이: sphereai.work (https://sphereai.work)
