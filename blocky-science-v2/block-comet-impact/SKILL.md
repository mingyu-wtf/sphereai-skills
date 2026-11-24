---
name: block-comet-impact
description: Put a block comet in the sky of a blocky Blender scene (V2 kit) - cube ice head, rays, blue and yellow block tails flowing, the right tail direction, clouds kept out of the way, and a simple block explosion. 블록 혜성 연출 기본.
---

# Block Comet (basic)

Uses `blocky-3d-kit` (`block_fx3.py`). The working example is `examples/walk_basic.py`.

## How it works
Every effect is block particles: a geometry-nodes setup puts a cube on each point and moves it with a formula. No simulation and no baking, so any frame renders directly.

## A comet in the sky
```python
cm = BF.block_comet3(L, "CMT", head, sun_dir=-tdir, scale=40, tail_len=12, flow=(F0, F1), side=right, N=6, glow=0.0, emit=1.5)
#   cube ice head slowly rolling + rays + blue ion tail + curved yellow dust tail, flowing all the time
```
1. **Position**: camera position + view direction x 1100 m, about 23-28 deg above the horizon. `scale=40` makes the head about 8% of the frame width.
2. **Tail direction**: the tail should point away from the sun on screen. Copy the `tdir` lines from `walk_basic.py`; using the raw sun direction lays the tail toward the camera and it looks short.
3. **Clouds**: build clouds after the comet and keep its line of sight clear: `W.clouds3(..., keep_rays=[(cam, head + tdir*k, 250) for k in (0, 200, 400, 600)])`.

## A simple explosion
```python
BF.block_burst3(L, "BB", center, f, R=50)     # fire blocks, block smoke, embers, debris and a white ring at frame f
```
Start the camera shake on the same frame (`CN.handheld(cam, f0, f1, dist, kicks=[(f, 2.2, 26)])`).

## Keep it readable
- Glow stays low: comet head emission at most 0.75 so the cube faces stay visible; tail 1-1.8.
- If the effect turns into a white blob, lower emission first.
- Keep particles away from the camera: anything right in front of the lens becomes a big white square.

## Output
Comet code inside the cut and a still of each shot where it appears.

---
만든이: sphereai.work (https://sphereai.work)
