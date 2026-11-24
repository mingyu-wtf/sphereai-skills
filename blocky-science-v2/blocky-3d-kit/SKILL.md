---
name: blocky-3d-kit
description: Ready-to-run Blender Python kit for blocky 3D science videos - block city and river, walking characters, a block comet in the sky, camera moves and colour that does not burn white. Copy a tested skeleton cut and change it. 블록 3D 장면 코드 키트(V2).
---

# Blocky 3D Kit (V2)

V1 gave rules and Claude wrote every scene from scratch. V2 ships the code: tested Blender modules and two skeleton cuts. **Start every new cut by copying a skeleton, never from an empty file.** Everything runs in background Blender from the command line.

## What is in the kit
```
blocky-3d-kit/
  scripts/                 the modules (import them; do not edit them)
    lib_mc.py              scene, boxes with pixel textures, cameras, render settings
    kit_base.py            helpers: show/hide keys, flat sky, sun lamp, point light, stars, ground, fr(), fps30()
    char_rig.py, char_rig2.py   block characters: walking with planted feet, poses, faces, blinking
    mc_world3.py           block city with lit windows, pixel river, bridge, cars, riverside, hills, block clouds, square sun
    block_fx3.py           block comet, glare (look3) and colour (grade3)
    sci_fx3.py             physical sky (sky3)
    cine3.py               orbit, crane, lens keys, handheld shake
    sets3.py               floating grass-island stage for explainer shots
    bg_build.py, vol_handler.py   build and render helpers
  examples/
    walk_basic.py          5 s: dusk riverside, a girl walks in and points at a block comet, two people look up
    stage_compare.py       6 s: floating island, a person, a bus, a tree and a building pop in one by one
    stills.sh, render.sh   build + stills sheet / build + JPG frames + mp4
    reference_sheet_basic.png   what walk_basic must look like (frames 30, 100, 145)
```

## Requirements
Blender 5.x, ffmpeg on PATH, Git Bash on Windows (or any bash). If Blender is not at `C:\Program Files\Blender Foundation\Blender 5.2\`, set `BLENDER=/path/to/blender`.

## First run
```bash
cd blocky-3d-kit/examples
mkdir ../my_test && cp walk_basic.py stills.sh render.sh ../my_test/ && cd ../my_test   # never work inside examples/
NAME=walk_basic bash stills.sh 30 100 145
```
Success = `SAVED ... WALK_basic` and `SHEET .../st/sheet.png`. Open the sheet and compare it with `examples/reference_sheet_basic.png`. Then `NAME=walk_basic bash render.sh 1 150` makes `render/walk_basic.mp4`.

## How to make a cut
1. Copy a skeleton: outdoor scene -> `walk_basic.py`; explainer or comparison -> `stage_compare.py`.
2. Write the shot list as comments at the top (`#  S1    1~90   description`). Frame = narration second x 30 + 1.
3. Keep the order of the skeleton: scene and **frame range first** -> sky and sun -> world -> comet -> clouds last -> characters (`auto_blink` last) -> cameras -> `render_setup` -> `BF.look3` -> `BF.grade3` -> `D.fps30`.
4. Build, render stills, **look at them yourself**, change one thing, repeat.
5. When every shot looks right, render the whole cut with `render.sh`.

## Basics
- Up = +Z, metres, degrees. Characters face -Y, origin at the feet. With the camera looking -Y, screen right is -X.
- Wider lens = more in frame: 20-24 mm for looking up at the sky with people in frame, 35 mm or less for a full body at 3-5 m.
- One full render at a time; frames as JPG quality 95.
- All textures are drawn in code; never use a game's official textures, characters or logos.

## Which skill next
Scenes and stages -> `blocky-world-v3`. The comet -> `block-comet-impact`. Walking and pointing -> `blocky-character-acting-v2`. Checking stills -> `blocky-render-review`.

---
만든이: sphereai.work (https://sphereai.work)
