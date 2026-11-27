---
name: longform-to-shorts
description: Turn one long video (file or YouTube link) into 5-10 vertical Shorts/Reels/TikToks for free on your own PC - local word-level transcription, AI-picked viral moments, face-tracking 9:16 crop, word-by-word captions, pause removal. Works in any language.
---

# Long-form to Shorts Clipper

One long video in, several ready-to-post vertical clips out. Everything runs locally: speech recognition with faster-whisper (GPU if available, CPU otherwise), cutting and captions with ffmpeg. You (the agent) read the transcript and pick the moments - that is the part paid clipping services charge for. No API key, no upload, no watermark.

**Language rule:** reply to the user and write titles, captions and hashtags in the user's language. Captions on the video are always in the language spoken in the video. Ask once if unclear.

## Setup (once)
```
pip install faster-whisper yt-dlp opencv-python pillow
```
- `ffmpeg` with libass on PATH (Windows: `winget install ffmpeg`, macOS: `brew install ffmpeg`).
- NVIDIA GPU (optional, much faster): `pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"`. Without it the script falls back to CPU automatically.
- A bold font that covers the spoken language is found automatically; otherwise pass `--font path/to/Bold.ttf`.
- Use a work folder path without `#`.

## Steps

1. **Ask only what you cannot decide** (one message): the video (file path or URL), how many clips (default 5-8), target length (default 20-60 s), platform (Shorts / Reels / TikTok - same 9:16 output), and whether they have the rights to the video.

2. **Prepare** - `python scripts/prepare.py "<file or URL>" --out work/<name> [--model small|medium|large-v3] [--lang auto]`
   - `small` is fast; `medium` is the best balance; `large-v3` for hard audio. A 10-minute video takes about 1-2 minutes on a recent GPU.
   - Read **all** of `work/<name>/transcript.txt` (`[mm:ss|seconds] text`).
   - Look at 2-3 frames of the source (`ffmpeg -ss <t> -i work/<name>/video.mp4 -frames:v 1 f.png`) to choose the crop mode and to see if the video already has burned-in subtitles.

3. **Pick the moments** and write `work/<name>/clips.json` - rules in `references/picking-moments.md`, format in `references/clips-format.md`. In short:
   - each clip is **self-contained** (makes sense with no context), starts on the hook sentence, ends on a payoff line;
   - score 1-10 and keep only 7+; no two clips overlap; prefer 25-50 s;
   - start/end on segment boundaries from the transcript, never mid-sentence;
   - write a short on-screen title (max ~14 CJK characters or ~6 English words), a caption and 3-5 hashtags per clip.

4. **Render** - `python scripts/render.py work/<name> [--only 1,3] [--crop face|center|fit] [--no-tighten] [--accent "#FFD60A"]`
   - Output: `clips/clip_01.mp4 ...` (1080x1920) + `.srt`, `clips/_preview.png`, `clips/posts.txt`.
   - `tighten` (default on) removes pauses longer than ~0.4 s between words; every word stays.
   - Crop modes: `face` follows the speaker (talking head, podcast); `center`; `fit` puts the whole frame on a blurred background, zoomed 1.35x (slides, screen recordings, animation, wide shots). Vertical sources are just resized.
   - If the source already has subtitles burned in at the bottom, set `"trim_bottom": 0.2` (share of height to cut) so they do not double up with ours.

5. **Check before delivering** - open `_preview.png`, then grab 3 frames from every clip (start, middle, end). Fix and re-render (`--only`) if:
   - the first second is not a hook or a sentence is cut at either end -> move start/end to the nearest segment boundary;
   - the face is cut off -> use `fit` or `center`;
   - captions overlap something important -> change `style.caption_y` (0.55-0.80);
   - a transcription error appears in the captions -> fix the word in `transcript.json` and re-render.

6. **Deliver**: full paths of the clips, the preview and `posts.txt` (title / caption / hashtags per clip, with the source time range). Recommend posting one clip per day rather than all at once. Do not upload anything.

## Rules
- **Rights**: only clip videos the user owns or has permission to use. For someone else's video, say that reposting clips can break copyright and platform rules; do not help strip credits or watermarks.
- **No invented content**: titles and captions must match what is said in the clip. No clickbait that the clip does not deliver.
- Do not change meaning by cutting (e.g. removing a "not"). `tighten` only removes silence between words.
- Never put API keys or logins in files. This skill needs none.

## Troubleshooting
- `cublas64_12.dll not found` -> install the two NVIDIA pip packages above, or ignore it (CPU fallback).
- Captions show boxes -> `--font` with a font for that language.
- Download fails -> `pip install -U yt-dlp`; some sites need the user's own downloaded file.
- Face crop jumps or misses -> `--crop fit`.

Worked example: `references/example_en.md`.

---
만든이: sphereai.work (https://sphereai.work)
