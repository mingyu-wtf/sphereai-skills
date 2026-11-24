---
name: blocky-science-start-here
description: Map for 8-9 minute What-if science videos in a blocky 3D world (Blender, free TTS, Remotion): which skill at each step, setup and folder layout. Start here. 3D 롱폼 시작 안내.
---

# Blocky Science Long-form: Start Here

This skill is the map. It tells the user which skill to use next and checks that they have what each step needs.

The format: a 16:9 long-form video, 8-9 minutes, that asks "What if...?" (What if mosquitoes disappeared? What if the Earth's magnetic field vanished?) and answers with real science, shown in a cute blocky 3D world. The contrast between cute visuals and serious content is the point.

## The path
| Step | What you want | Skill | Needs |
|---|---|---|---|
| 1 | Pick a topic and write a fact-checked script | `what-if-topic-script` | Web search |
| 2 | Make the narration and sentence timings | `free-tts-narration` | Python, edge-tts, ffmpeg |
| 3 | Design the 3D scenes for each idea | `science-scene-design` | Blender 4.2+ |
| 4 | Place cuts and cameras on the narration | `narration-synced-cuts` | Blender, ffmpeg |
| 5 | Add captions and cards | `text-overlay-remotion` | Node.js, Remotion |
| 6 | Make the thumbnail | `blocky-thumbnail` | an image tool, Python |
| 7 | Cut a 60-90 s vertical highlight | `vertical-highlight-reshoot` | Blender, ffmpeg |

Nothing in this set needs a paid service. Blender and Remotion renders are free to repeat.

## Folder layout per episode
```
episodes/<NN - title>/
  script.md        narration by block, shot table, fact-check table, TTS replacement table
  01_blend/        one script per section
  02_render/       <section>/####.jpg, _stills/
  03_audio/        narration wav, timings
  04_final/        preview without text, final with text
output/            finished videos only
```

## Rules for the whole set
- **Facts first**: every number and quote is checked against a source before narration. Unsourced claims are cut.
- **Blocky style, original assets**: follow the look, never use a game's official characters, textures, logos or UI.
- **One shared timeline**: frame = narration second x fps + 1. Every section script and every text card uses it.
- **Stills before renders**, **one full render at a time**, frames as **JPG 95**.
- **Never edit a finished episode**; apply improvements from the next one.

## Output
A plan for the first episode: topic options, which skills in which order, and the first question to answer.

---
만든이: sphereai.work (https://sphereai.work)
