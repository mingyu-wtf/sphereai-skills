---
name: blocky-thumbnail
description: 1280x720 thumbnail for a blocky 3D video: a strong text-free scene with room for the title, then two outlined title lines drawn with Python. 블록 스타일 썸네일.
---

# Blocky Thumbnail

## 1. The picture (no text in it)
- Render the strongest shot of the episode in Blender at 2560x1440, or make a blocky 3D picture with an image tool.
- Leave an empty area for the title.
- Pick the moment, not a summary: one subject, big, readable at phone size.
- Never use a game's official characters, logos or textures.

## 2. The text
Two short lines:
- Line 1 (white): the premise in a few words.
- Line 2 (yellow): the hook or a number.

Draw it with Python (Pillow):
- Bold or pixel font with an open licence, thick black outline, no box behind it.
- Put it in the empty area with a margin from the edge.
- Output 1280x720 JPG plus a text-free copy.

## 3. Checks
- [ ] The text does not cover the subject's face or the key object.
- [ ] Readable at 160x90 (look at a scaled-down copy).
- [ ] Different from your previous thumbnails in colour and layout.
- [ ] The promise matches the video.

## Output
`<title>_thumbnail.jpg` (1280x720), the text-free copy and the original picture.

---
만든이: sphereai.work (https://sphereai.work)
