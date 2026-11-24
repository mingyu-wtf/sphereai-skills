---
name: blocky-science-start-here-v2
description: Map for 8-9 minute What-if science videos in a blocky 3D world, v2 - now with a ready-to-run Blender code kit (block city, walking characters, a comet in the sky). Which skill at each step and what you need. Start here. 블록 과학 롱폼 시작 안내(v2).
---

# Blocky Science Long-form: Start Here (v2)

This skill is the map. It tells the user which skill to use next and checks that they have what each step needs.

The format: a 16:9 long-form video, 8-9 minutes, that asks "What if...?" and answers with real science, shown in a cute blocky 3D world. Topics land best when they happen where the viewer lives.

## What is new in v2
- **Code, not only rules**: `blocky-3d-kit` ships tested Blender modules and skeleton cuts. A new cut starts as a copy of a skeleton that already works (a girl walks along a dusk riverside and points at a block comet).
- A block city with lit windows, pixel river and block clouds; a floating-island stage for explainer shots; colour that does not burn white.

## The path
| Step | What you want | Skill | Needs |
|---|---|---|---|
| 1 | Pick a topic and write a fact-checked script | `what-if-topic-script` | Web search |
| 2 | Make the narration and sentence timings | `free-tts-narration` | Python, edge-tts, ffmpeg |
| 3 | Install and test the 3D kit (once) | `blocky-3d-kit` | Blender 5.x, ffmpeg, bash |
| 4 | Build sets, stages, sky and colour | `blocky-world-v3` | the kit |
| 5 | Put a comet in the sky | `block-comet-impact` | the kit |
| 6 | Make characters walk and point | `blocky-character-acting-v2` | the kit |
| 7 | Place cuts and cameras on the narration | `narration-synced-cuts` | Blender, ffmpeg |
| 8 | Check stills before rendering | `blocky-render-review` | the kit |
| 9 | Add captions and cards | `text-overlay-remotion` | Node.js, Remotion |
| 10 | Make the thumbnail | `blocky-thumbnail` | an image tool, Python |
| 11 | Cut a 60-90 s vertical highlight | `vertical-highlight-reshoot` | Blender, ffmpeg |

`science-scene-design` still holds the idea -> scene patterns. Nothing in this set needs a paid service.

## Folder layout per episode
```
blocky-3d-kit/            shared code (one copy for all episodes)
episodes/<NN - title>/
  script.md               narration by block, shot table, fact-check table
  01_blend/               one script per section, copied from a kit skeleton
  02_render/              <section>/####.jpg, still sheets
  03_audio/               narration wav, timings
  04_final/               preview without text, final with text
output/                   finished videos only
```

## Rules for the whole set
- **Facts first**: every number and quote is checked against a source before narration.
- **Blocky style, original assets**: never use a game's official characters, textures, logos or UI.
- **One shared timeline**: frame = narration second x 30 + 1.
- **Stills before renders**, one full render at a time, frames as JPG 95.

## Output
A plan for the first episode: topic options, which skills in which order, and whether the kit test passed.

---
만든이: sphereai.work (https://sphereai.work)
