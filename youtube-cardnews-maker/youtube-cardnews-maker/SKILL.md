---
name: youtube-cardnews-maker
description: Turn a YouTube link into Instagram card-news images and 9:16 highlight clips; foreign videos get Korean-translated subtitles. Free - no API key, no browser login. 유튜브 주소로 카드뉴스와 하이라이트 쇼츠, 해외 영상은 한글 번역 자막.
---

# YouTube Card-News + Highlight Maker

Given a YouTube URL, you (the agent) read the transcript, write the card-news text yourself, render the card images, and cut two highlight clips with Korean subtitles. **Every run delivers both: the cards and the highlight videos.** **You do the summarizing and translating** - there is no paid API and no Aside/browser login. Everything else is free local tooling (`yt-dlp`, `ffmpeg`, a headless browser for rendering).

## Setup (once)
```
pip install yt-dlp youtube-transcript-api playwright
```
- `ffmpeg` and `ffprobe` must be on PATH (Windows: `winget install ffmpeg`).
- Rendering uses an installed Chrome/Edge. If neither exists: `playwright install chromium`.
- Optional, only for videos with no captions: `pip install faster-whisper` (local speech recognition, free).
- A Korean font is found automatically (Windows/macOS/Noto). Otherwise pass `--font path/to/font.ttf`.

Run scripts from this skill's `scripts/` folder. Use a work folder whose path has no `#` character (ffmpeg treats `#` as a URL fragment), e.g. `work/<video-id>`.

## Steps

1. **Ask** for: the URL; card count (default 5-10, you decide by length); card size (default 1080x1350, or 1080x1080); an optional brand label for the cover.
   - **Highlight videos are always made** (2 clips of 10-20 s) together with the cards. Do not ask whether to make them, and never skip them unless the user explicitly says "cards only" or the video cannot be downloaded (then say why).
2. **Fetch** - `python scripts/fetch.py "<url>" --out work/<id>`
   - Prefers Korean captions, then English, then any, then local speech recognition. If the video is foreign and you want the original captions to translate yourself, add `--lang en`.
   - Writes `meta.json`, `transcript.json`, `transcript.txt` and `video.mp4` (<=720p).
   - Read `transcript.txt` fully (it has `[mm:ss|seconds]` markers).
3. **Write `cards.json`** in the work folder (format and rules: `references/cards-format.md`). Summarize into Korean cards: cover -> background -> point_1..N -> closing. If the transcript is not Korean, translate while summarizing; keep names, numbers and quotes accurate. Wrap the one or two key words of a title in `**double asterisks**` to color them. Give each card a `time` (seconds) whose video frame fits that card. Also write the caption (`description`) and a first comment with the original link.
4. **Pick two highlights** right away (not overlapping, from different parts): the strongest claim, a reveal, or a quotable moment, 10-20 s each, starting and ending on caption-line boundaries. Add `"highlights": [{"start": .., "end": .., "title": "short Korean clip title"}]` to `cards.json`, then run
   `python scripts/prepare_subs.py work/<id>` - it copies the caption lines (with exact timing) into each highlight's `subs`. For foreign videos fill every empty `ko` with a natural Korean line (34 characters or fewer reads best). For Korean videos `ko` is pre-filled; just tidy it.
5. **Check** - `python scripts/check.py work/<id>`. Fix every `FIX` line (limits, missing Korean, overlaps) and re-run until it says `0 to fix`.
6. **Render cards** - `python scripts/render_cards.py work/<id> [--theme dark|light] [--accent "#ffcf3f"] [--size 1080x1080] [--brand "Name"]`
   - Output: `cards/card_01.png ...`, `cards/_preview.png` (all cards on one sheet) and `description.txt`.
   - Design: the cover is a full-bleed frame with the key words on an accent marker; inner cards show the frame as a rounded image, a label pill, a large faint point number, the title with a marker underline and the body. `dark` (default) or `light` theme.
   - **Open `_preview.png` and every card.** The script warns when text runs off a card; shorten it and re-render. Swap a card's `time` if its frame is dull or unrelated.
7. **Make the highlight videos** - `python scripts/make_highlights.py work/<id> [--show-original] [--accent "#ffcf3f"] [--brand "Name"]`
   - Output: `highlights/highlight_01.mp4` + `.ko.srt`, and `highlights/_preview_01.png` (3 frames). Layout: clean dark frame, a HIGHLIGHT pill + bold title + source on top, the video in a rounded window with a thin progress bar on its bottom edge, Korean subtitles under it (same font as the cards; `**word**` colors a key word). The lower part is left empty on purpose: shorts apps cover it with their own buttons and captions.
   - **Open each `_preview_NN.png`** to confirm subtitles are readable, in sync with the scene and not cut off.
8. **Deliver**: list the full paths of the cards, the preview sheet, the highlight videos, the `.srt` files and `description.txt`. Point out any names/terms you were unsure about in translation. Remind the user about the rules below. Do not upload anywhere unless asked.

## Rules
- **Copyright**: the clips are excerpts of someone else's video. Credit the channel on the cover (done automatically) and in the caption, link the original, keep excerpts short, and prefer your own videos, videos you have permission for, or openly licensed ones. Say so to the user; do not claim the content as theirs.
- **No invented facts.** Every claim, number and quote on a card must come from the transcript. If a caption is unclear, leave it out or say it is uncertain.
- **Translation**: translate for meaning, not word by word; keep proper names in their common Korean form, and point out names or terms you were unsure about so the user can check.
- Cards use no emoji and short sentences; one message per card. Respect the character limits in `references/cards-format.md`.
- Never put API keys, cookies or logins in any file. This skill needs none.
- If captions are blocked or the download fails, tell the user what failed and try again (update yt-dlp, `--stt`). Only as a last resort, with the user's OK, use `--no-video` (gradient cards, no clips) - the default deliverable always includes highlight videos.

## Troubleshooting
- `No browser could be started` -> install Chrome, or `playwright install chromium`.
- Download errors / 403 -> `pip install -U yt-dlp`, then retry.
- Subtitles look clipped -> shorten the Korean lines; the script shrinks long lines but warns above 44 characters.
- Korean text shows as boxes -> pass `--font` with a Korean `.ttf`/`.otf`.

---
만든이: sphereai.work (https://sphereai.work)
