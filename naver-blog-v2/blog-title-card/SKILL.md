---
name: blog-title-card
description: Make a 1080x1080 blog title card from one background image with a label, two-line title and sub line, rendered free with headless Chrome. Crops the corner mark of free image tools. 블로그 제목 카드 만들기.
---

# Blog Title Card

Use this to make the first image of a blog post: one background picture plus clean Korean text. Everything runs on the user's computer, no account, no cost.

## Requirements
- Python 3 and Google Chrome (or Edge/Chromium). No Python packages needed to render.
- A background image (see `flow-nano-banana-images`; ask for a calm dark lower half and the subject in the upper half).

## Steps
1. Pick the background. The subject should sit in the **upper half**. The **lower half** must be calm and dark because the title goes there.
2. Write the text. Keep it short: label (about 10 characters), small line above the title, title line 1 and line 2 (about 12 Korean characters each at this size), one sub sentence. Put the key word of line 2 inside `<u>...</u>` for an accent underline. The title should carry the same main keyword and twist as the post title.
3. Render:

```
python references/render_card.py --bg card_bg.png --out card.png \
  --tag "Label" --chip "Small line" --l1 "Title line 1" --l2 "Title line <u>2</u>" \
  --sub "One sentence" --accent "#ffb347"
```

4. Open `card.png` and check: text is not cut off, text does not cover the main subject, the bottom-right corner shows no leftover sparkle mark, and the contrast is readable on a phone-size preview.
5. Fix by editing the text length or the `--zoom` value (default 1.12; the zoom is what crops the corner mark), then render again.

## Notes
- Fonts: the template uses fonts already on the computer (Malgun Gothic on Windows, Apple SD Gothic Neo on Mac, Noto Sans CJK on Linux). If you add a custom font, make sure its license allows it.
- Do not add the blog name, other channel names or a face to the card unless the user asks.
- One card per post. The same size works for the post's top image and for social previews.

## Output
`card.png` (1080x1080) and the exact text used, so the user can reuse it in the post caption.

---
만든이: sphereai.work (https://sphereai.work)
