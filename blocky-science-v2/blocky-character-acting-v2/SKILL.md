---
name: blocky-character-acting-v2
description: Act with block characters in Blender (V2 kit rig) - walking with planted feet, pointing at the sky, looking up, faces, breathing and blinking, and framing people so heads are not cut. 블록 캐릭터 연기 v2 기본(걷기·가리키기).
---

# Blocky Character Acting v2 (basic)

Uses `blocky-3d-kit` (`char_rig2.py`). The working example is `examples/walk_basic.py`.

## The rig
```python
ch = CR.build(L, "BORA", CR.HERO, loc=(x, y, z), rot_z=0)   # returns a dict; ch["root"] is the whole body
CR.rest(ch, F0); CR.face(ch, F0, "normal")
CR.walk_to(ch, [(x0, y0), (x1, y1)], f0, f1)               # feet stay where they land
CR.pose(ch, f, head=(x, y, z), armR=(...), torso=(...))     # joint angles in degrees
CR.idle(ch, f0, f1)                                         # breathing
CR.auto_blink(ch, f0, f1, seed=1)                           # last, after every face key
```
- Characters: `CR.HERO`, `CR.BOY`, `CR.BUDDY`, `CR.THIEF`. Faces: `normal`, `blink`, `wink`, `happy`, `smile`, `angry`, `excited`, `scared`, `shocked`.
- Joints: `hips`, `torso`, `head`, `armL/R`, `elbowL/R`, `legL/R`, `kneeL/R`, `ankleL/R`, plus `hips_z`. Negative head x = looks up; arm x -150 points at the sky.
- Front is -Y, origin at the soles.

## Walking
- Natural speed about 1 m/s: 6 m in 140 frames at 30 fps.
- Put the next pose at least **2 frames after the walk ends** (`f1+2`), or it jumps.
- Add a path point at every corner so the body does not cut through walls.
- Never slide a character with `move` to walk; the feet skate.

## Simple acting
| Moment | Keys |
|---|---|
| Notice something in the sky | `head=(-22,0,6), torso=(-3,0,0)`, then 12 frames later `head=(-30,0,8), armR=(-150,0,-18), elbowR=(-15,0,0)`; face `shocked` |
| Look up, scared | `head=(-26,0,-8), armL=(-20,0,10), torso=(-3,0,0)`, face `scared` |

Change the face a frame or two before the move, and hold a strong pose for a moment before the next one.

## Framing people
- Full body: 35 mm or wider at 3-5 m.
- People and the sky together: 24 mm, aimed only about 8 deg up. Aiming high cuts people off at the bottom.
- From directly behind, arm and head moves barely read; move the camera to the side for actions.

## Output
Character keys in the cut and a still at every pose change.

---
만든이: sphereai.work (https://sphereai.work)
