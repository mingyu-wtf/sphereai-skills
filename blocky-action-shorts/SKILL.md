---
name: blocky-action-shorts-start-here
description: Map for making blocky 3D justice action shorts in Blender (9:16, about 30 s): which skill at each step, what to install, rules for the set. Start here. 블록 액션 쇼츠 시작 안내.
---

# Blocky Action Shorts: Start Here

This skill is the map. It does not build anything itself. It tells the user which skill to use next and checks that they have what each step needs.

The format: a vertical short (1080x1920, 60 fps, about 25-35 seconds) set in a blocky voxel world. A bully does something bad to someone weaker, a hero arrives, chases, stops them, and sends them flying with one hit. Cute characters, over-the-top action, a satisfying ending.

## The path
| Step | What you want | Skill | Needs |
|---|---|---|---|
| 1 | Learn how good action shorts are directed | `action-shorts-directing-research` | Web search, yt-dlp, ffmpeg |
| 2 | Turn the idea into a shot list | `justice-story-formula` | nothing |
| 3 | Build and animate the characters | `blocky-character-acting` | Blender 4.2+ |
| 4 | Add impact effects | `impact-fx-recipes` | Blender |
| 5 | Make it fast-then-slow | `speed-ramp-quick-slow` | ffmpeg |
| 6 | Render, assemble and check | `shorts-finish-checklist` | Blender, ffmpeg |

Steps 1 and 2 are pure planning. Steps 3-6 are done by Claude writing Blender Python scripts and running Blender in the background (`blender -b --factory-startup -P script.py`). No paid service is needed anywhere.

## First-time check (5 minutes)
1. Is Blender installed and can it run from the command line? Is ffmpeg on the PATH?
2. Ask for the story in one line: who is the bully, what do they take, who is the hero.
3. Ask whether there is a reference short. If yes, use it only to study directing (step 1), never to copy characters, music or shots one to one.
4. Suggest the first run: one short, 4 sections of about 7 seconds, checked as still images before any full render.

## Rules for the whole set
- **Original characters only.** Follow the blocky style, but never use a game's official characters, textures, logos or UI. Do not use the word for a trademarked game in your title.
- **Stills before renders.** Check one still per shot as a contact sheet, then render.
- **One full render at a time** on a single PC. Render frames as JPG (quality 95) instead of PNG: about 1/9 the disk space with no visible loss.
- **One shared timeline.** Every section script uses the same absolute frame numbers (section A 1-447, section B 448-1034, and so on) so the parts join with no gap.
- **Music is not part of this set.** If you add music later, use a track you have the rights to.
- Keep a short changelog of user feedback; turn each repeated note into a rule in the skill it belongs to.

## Output
A short plan for the first short: the one-line story, which skills in which order, and the first question to answer.

---
만든이: sphereai.work (https://sphereai.work)
