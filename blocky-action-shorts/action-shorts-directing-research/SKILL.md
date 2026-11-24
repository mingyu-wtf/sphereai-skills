---
name: action-shorts-directing-research
description: Research how hit action shorts are directed (hook, anticipation, hit-stop, shake, cut rhythm, hero shots) and write a directing note for your next short. 액션 쇼츠 연출 리서치.
---

# Action Shorts Directing Research

The goal is not to copy one video. It is to collect **directing techniques** from several well-performing action shorts and write a directing note that the next short is built from.

## 1. Collect samples (5-8 videos)
- Search shorts platforms and the web for the genre: "justice", "bully gets punished", "hero saves", blocky / voxel / 3D animation action shorts. Prefer videos with views far above the channel's average (outliers).
- Mix sources: at least 2 channels, at least 1 non-blocky animation (good directing transfers across styles).
- For each sample note: link, length, views, upload date. Download only for private analysis (`yt-dlp`), never re-upload.

## 2. Look at each sample
1. **Cut points**: `ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null -` and read the `pts_time` values. Count the cuts.
2. **Contact sheet**: one frame every 0.5 s in a grid (`ffmpeg -i ref.mp4 -vf "fps=2,scale=270:-1,tile=8x6" sheet.jpg`) so the whole short is visible at once.
3. **Speed changes**: note where motion slows down, freezes or jumps.
4. **First second**: what is on screen in the first second? Movement, a face, a threat, text?

## 3. Fill the technique table
| Technique | What to look for |
|---|---|
| Hook | Is the conflict visible in the first second? |
| Insert close-up | Is the key act (stealing, blocking, hitting) shown in a close-up? |
| Anticipation | Does a big move start with a small opposite move? |
| Hit-stop | Does the image freeze at contact? |
| Impact package | flash, star, shockwave, speed lines, dust, shake |
| Camera shake | Short and strong, or long and soft? |
| Hero shot | Low angle, slow motion, freeze frame when the hero appears |
| Cut rhythm | Where do shots get shorter? |
| Two in one frame | Are both sides of the fight in the same frame? |
| Environment reacts | clouds part, ground cracks, wind |
| Ending | Twist, reward, dance, loop back to the start |

## 4. Write the directing note
Save as `directing_note.md` next to the project:
- **Keep (seen in 3+ samples)**: techniques that repeat across hits.
- **Try (seen once, looked strong)**: one or two to experiment with.
- **Avoid**: what made a sample feel slow or confusing.

## Rules
- Never copy a sample's characters, story beats in order, music, or exact shots. Mix techniques from several sources.
- Do not name or tag other creators in your upload.
- Keep downloaded samples private and delete them when the note is done.

## Output
`directing_note.md` with the technique table filled for each sample and the keep / try / avoid summary. Hand it to `justice-story-formula`.

---
만든이: sphereai.work (https://sphereai.work)
