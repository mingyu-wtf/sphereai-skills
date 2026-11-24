---
name: text-overlay-remotion
description: Remotion captions plus title and info cards over a 3D science video, with outline-only text and times taken from the narration. 리모션 자막과 기본 설명 카드.
---

# Text Overlay with Remotion

Claude builds a Remotion composition that plays the finished 3D preview (`preview_full.mp4`) and draws captions and cards on top. Card content lives in the composition's default props so the user can edit text and timing in Remotion Studio without touching code.

## 1. Card types
| Type | Use | Behaviour |
|---|---|---|
| `title` | section title | big centred text + short subtitle |
| `info` | explanation | a line of text + items that appear one by one |

Each card: start frame, end frame, text, colour, optional items.

## 2. Design rules
- **No black boxes** behind text. Readability comes from a thick black outline.
- Pixel fonts with an open licence suit the blocky look; check the licence and credit it.
- Explanations at the top, captions at the bottom. Keep the middle for the 3D subject.
- **Do not repeat the caption** in a card. Cards add what the voice does not say.

## 3. Captions
- Sentence start and end from the sentence table.
- Short lines of similar length, break after a comma when you can.

## 4. Render
- Card times come from the narration, on the same frame timeline as the 3D.
- After rendering, look through the video for overlaps and cut-off text.

## Output
A Remotion composition with editable card props and the final video with text.

---
만든이: sphereai.work (https://sphereai.work)
