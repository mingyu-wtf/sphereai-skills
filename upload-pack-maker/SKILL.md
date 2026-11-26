---
name: upload-pack-maker
description: Build a YouTube upload pack - 10 titles (3 picked), description with chapters, tags, 3 thumbnail concepts - and guide a free thumbnail image in Google Flow. Click-worthy, never misleading.
---

# Upload Pack Maker

Use this right before uploading, once the video is finished. Take the script or a summary of the video and produce every piece of text the upload needs. The standard: earn the click without promising anything the video doesn't deliver.

## Language
Reply and write all deliverables in the user's language (Korean, English, Japanese, …). Ask once if unclear. Write titles, description, tags, and thumbnail copy in the language of the video's audience; if that differs from the chat language, keep explanations in the chat language. For a multilingual audience, offer the title and the first two description lines in a second language too (YouTube lets you add translated titles and descriptions).

Worked example: `references/example_en.md` (upload pack for "How to fall asleep faster").

## 0. Get these first
1. The script, or a summary of the video with timestamps
2. Audience and channel tone (if there are 3–5 existing titles, match their length and voice)
3. Video length (Short or long-form)

## 1. Titles (10 options → 3 recommended)
Mix these patterns:
| Pattern | Example |
|---|---|
| Result first | "I did ○○ and ○○ changed" |
| Question | "Why is ○○ so ○○?" |
| Number | "3 ○○ that ○○" (only if the video really has 3) |
| Twist | "I thought ○○, but actually…" |
| Fix | "How to fix ○○ in one go" |
- Put the main keyword near the front.
- Keep it short enough not to get cut on mobile; put the important words first. Rough guide: Korean and Japanese within the first ~20 characters; English within the first few words (long titles, past roughly 60–70 characters, commonly get truncated). Check on a phone preview.
- **Never promise what isn't in the video.** Exaggeration may raise clicks but it lowers watch time.
- Give each of the 3 recommended titles a one-line "why this title".

## 2. Description
```
[First two lines] What the video is and why to watch. This part shows in search results, so work the main keyword in naturally.
[Chapters] 0:00 Intro
           1:10 ○○
           …
[Related videos & links]
[Channel / contact info]
[Hashtags, 3 or fewer]
```
- Chapters are only recognized if they start at `0:00`, there are at least 3, and each lasts at least 10 seconds.
- Name chapters so viewers know what's inside ("How to compare prices", not "Part 2").
- Disclose ads or sponsorships in the description (and use the platform's paid-promotion setting where your country's rules require it).

## 3. Tags
- A comma-separated keyword list: the topic, synonyms, and common misspellings.
- Tags have little effect, so aim for accuracy, not volume.
- For a bilingual audience, include the main keyword in both languages.

## 4. Thumbnail plan
- Text: 3–5 words at most (in Korean or Japanese, one short phrase). Don't repeat the title; complement it.
- One face or object, large, on a color that contrasts with the background.
- Check that it still reads when shrunk (mobile size).
- Three thumbnail concepts, each written as "scene / text / color combo".
- If the user wants a prompt for an image generator, give it separately in English, including scene, composition, lighting, and aspect ratio (16:9).
- **Making the thumbnail image (optional)**: if the user wants the image too, walk them through generating it with Google Flow's image generation (within the free allowance). Follow `references/thumbnail-image-flow.md` for the prompt template, resizing, and adding text. If Flow isn't available in the user's region or account, the same prompt works in any image generator they have the right to use. The skill never signs in for the user; the user signs in to their own account.

## 5. For Shorts
- Short title, one key sentence in the first line of the description, 2–3 hashtags.
- The first frame of the video acts as the thumbnail in the feed, so check the first frame's text and composition.

## 6. Output format
```
[10 title options] → [3 recommended with reasons]
[Full description (ready to copy and paste)]
[Tag list]
[3 thumbnail concepts]
[Fact check: do the numbers in the title and description match the video?]
```

## 7. Checklist
- [ ] The title's promise is delivered in the video
- [ ] The key point is in the first two lines of the description
- [ ] Chapters start at 0:00 and there are at least 3
- [ ] Thumbnail text reads on a small screen
- [ ] Sponsorship / ad disclosure is checked

---
만든이: sphereai.work (https://sphereai.work)
