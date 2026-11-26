# Making the thumbnail image: Google Flow free image generation

This is the procedure for turning the thumbnail concept the user picked (out of the three) into an image. It covers Google Flow's image generation. Google can change the free allowance, the regions where it's available, and the menu names, so **check on the current screen**. The menu descriptions below only show the general flow.

If Flow isn't available to the user, the same prompt template and finishing steps work with any image generator they have the right to use.

## 0. Before you start
- The user signs in with their own Google account (never type a password into the chat; neither the skill nor the agent signs in on the user's behalf).
- On the Flow screen, check the free allowance (generations per day / month) and that image generation is open for this account. If the limit is reached, stop for the day and continue tomorrow. Whether to pay is the user's decision.
- If a face photo will be used, confirm it's the user's own, or that they have permission from the person in it. Don't put real people, trademarks or logos, or copyrighted characters into the prompt.

## 1. Writing the prompt
English prompts often give steadier results (this is not a confirmed rule: try the user's language first and switch to English if results are poor). Combine the seven slots below into one paragraph.

| Slot | Content | Example |
|---|---|---|
| Subject | Who or what is the center of the frame | a surprised young man holding a phone |
| Expression / action | Emotion readable at a glance | wide eyes, open mouth, leaning forward |
| Background | Simple, contrasting with the subject | plain bright yellow background |
| Composition | Subject position, leave room for text | subject on the right, empty space on the left for text |
| Lighting / color | Contrast and mood | high contrast, soft rim light, saturated colors |
| Format | Aspect ratio and quality | 16:9, sharp focus, no text |
| Exclusions | What to leave out | no watermark, no logo, no extra fingers |

- **Don't put text in the image** (`no text`). Image generators often get lettering wrong, especially non-Latin scripts such as Korean or Japanese, and sometimes English too. Add the copy afterwards in an editor.
- Don't expect a finished image in one go: generate several with the same prompt and pick the best.

## 2. Generation flow (screen names may differ)
1. Open Flow and choose image generation mode. Don't confuse it with video mode.
2. Set the aspect ratio to landscape 16:9.
3. Paste the prompt and generate. If you don't like the result, change only one slot (expression, background color, etc.) and generate again.
4. Download the image you like.

## 3. Finishing after generation
- Size: use 1280×720 (16:9) as the baseline for a YouTube thumbnail. Shrink it if it exceeds the file-size limit (about 2 MB). Check the current spec in YouTube Help.
- Text: add the 3–5 word copy in an editor. Use a bold font, strong color contrast with the background, and an outline around the letters. Use only fonts licensed for commercial use, and make sure the font supports the script you need (Korean and Japanese need fonts that include those characters).
- Small-screen check: shrink the image to mobile size (about 300 px wide) and check that the copy reads and the facial expression is visible.
- Saving: put the video's key word and the concept letter in the file name (e.g. `topic-keyword_thumb-A.png`).

## 4. Don't
- Bait with scenes that differ from the video, or with exaggerated threatening or shocking images
- Create real people's faces, famous characters, or brand logos
- Rotate several accounts to stretch the free allowance
- Make requests that break Google's terms of use or image generation policies

## 5. Things to confirm (the skill can't verify these)
- Whether generated images can be used commercially, and any attribution requirements, follow Google's current terms.
- Google may embed an invisible watermark in generated images. Tell the user, without stating it as certain.
