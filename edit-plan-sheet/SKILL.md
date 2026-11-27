---
name: edit-plan-sheet
description: Auto highlight video editor. Give it one video (a file or a YouTube link) and the agent watches it - transcript with word times, scene changes, loudness, contact sheets of frames - picks the best moments with a hook first, and edits them into one highlight video with Remotion (original sound, crossfades, captions from the speech, title, vertical 9:16 or horizontal 16:9, crop for burned-in subtitles). Works for talks, lectures, podcasts, vlogs, games, sports and events, including videos with little or no speech. Also edits from a script plus clips, or makes only an edit plan. Free, runs locally, no API keys.
---

# Auto Highlight Video Editor

One video in, one highlight video out. The agent analyses the source, reads and looks at it, picks the parts
that tell the best short story (hook first), and renders the edit. No narration or TTS is added: the original sound is used.

The user brings a script and clips instead, or wants only a plan for their own editor? Use `references/edit-plan.md`
(shot list, rhythm, caption and sound rules), then steps 5-8 below to render.

## Language
Reply and write all deliverables in the user's language (Korean, English, Japanese, ...). Ask once if unclear.
Captions stay in the video's spoken language; if that differs from the chat language, write the notes in the chat language.

## Setup (once)
- **Node.js 18+** (npm/npx) https://nodejs.org and **ffmpeg** with ffprobe on PATH
  (Windows `winget install ffmpeg`, macOS `brew install ffmpeg`, Linux `apt install ffmpeg`)
- **Python 3.8+**
- `pip install faster-whisper` for speech (strongly recommended; without it the agent picks by picture and sound only).
  NVIDIA GPU on Windows: also `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`; the scripts find those DLLs.
  No GPU: it runs on the CPU automatically (slower: a 10-minute video takes a few minutes with `small`).
- Optional: `pip install Pillow` (labelled contact sheets), `pip install yt-dlp` (YouTube links)

The first render runs `npm install` into `~/.cache/edit-plan-sheet/engine-<version>` and downloads a headless
Chrome: a few minutes and about 400 MB, once. The first transcription downloads the whisper model (~500 MB for `small`).

Files: `references/highlight-picking.md` (how to choose), `references/highlight-plan.md` (highlight.json),
`references/edit-json.md` (edit.json), `references/edit-plan.md` (plan rules), `references/example_en.md`.

---

## 0. Get these first
1. **The video**: a file path or a link. Only the user's own videos or videos they have permission to use.
2. **Target length**: 30 s, 60 s, 3 min ... (Shorts: 3 minutes at most)
3. **Format**: vertical 9:16 (Shorts, Reels, TikTok), horizontal 16:9, square 1:1
4. **Mood**: energetic / calm / funny / informative (sets rhythm and which moments win)
5. **Captions**: from the speech (default when there is speech) / none / only a few of their own words
6. Anything that must be in or out (a person, a product, a scene), and whether the source has burned-in subtitles or a logo

If the user just says "make a highlight", assume 60 s, 9:16, captions on, and say so.

## 1. Analyse
Make a work folder **with a plain path** (no `#`, ideally ASCII) and run:
```
python scripts/analyze.py <video file or URL> <workdir> --lang ko        # --lang optional (auto-detect)
```
Options: `--model medium` (better speech recognition, slower), `--no-transcript` (skip speech),
`--scene-threshold 0.2` (more scene cuts for calm footage), `--frame-every 5` (more frames).
It writes into the work folder:
| File | What it is |
|---|---|
| `meta.json` | length, size, fps, audio yes/no, `speech`: none / little / some / mostly, language, number of shots |
| `transcript.txt` / `.json` | phrases with `[start - end]` seconds; the json has word times |
| `scenes.json` | shots between scene changes, with loudness and the words spoken in each |
| `audio_energy.json` | loudness per second, `loud` moments, sudden `jumps`, `silences` |
| `frames/`, `contact_sheet_NN.jpg` | one small frame per shot (more in long shots), tiled with frame number, time and shot |
| `overview.txt` | one line per shot: time, loudness, LOUD/JUMP marks, frames, what is said. **Read this first** |

## 2. Read and look at everything
- Read `overview.txt` fully, and `transcript.txt` fully when there is speech.
- **Open every contact sheet** and look at it: what is in each shot, faces, text cards, action, bad frames,
  burned-in subtitles or logos (and where they sit, for `crop`). Open single files in `frames/` when a cell is unclear.
- Note candidate moments with their seconds as you go.
Do not pick from the transcript alone: a great line over a bad picture is a weak highlight, and in a video
with little speech the picture and the sound are all you have.

## 3. Pick the highlights
Follow `references/highlight-picking.md`. The short version:
- **Hook first**: the most striking moment (a claim, a punchline, the best picture, the loudest reaction), marked `"hook": true`.
- Then a small story: setup -> best moments / example -> turn -> payoff -> an ending that feels like an ending.
- **Never cut inside a word**, avoid cutting mid-sentence: use phrase edges from `transcript.txt`.
- **No repeated scenes**, vary the lengths, merge touching parts of the source into one segment.
- Little or no speech: pick by scene changes, LOUD/JUMP moments and the frames; keep the original sound.
- Fit the target length (within 10%).
Write `highlight.json` in the work folder (`references/highlight-plan.md`). Give each segment a `reason`.

## 4. Plan -> edit.json
```
python scripts/plan_highlight.py <workdir> --dry-run    # timeline and length only
python scripts/plan_highlight.py <workdir>              # writes <workdir>/edit.json
```
It snaps edges to word boundaries, puts hooks first, keeps the original sound (volume 1) with short crossfades
and a fade at the end, makes captions from the speech (one phrase each, 1-2 lines), adds the title, frames
the picture (9:16 from a horizontal source = blurred fill) and prints the length against the target.
Read the notes (mid-sentence edges, repeated source parts) and fix `highlight.json` until the length and story are right.
Read the captions in `edit.json`: fix recognition mistakes with a segment's `caption` (exact words), then run it again.
`edit.json` can also be edited by hand (`references/edit-json.md`), e.g. `zoom`, `position`, `highlight`.

## 5. Check
```
python scripts/check_edit.py <workdir>
```
Prints the resolved timeline. **Errors** must be fixed (missing files, `out` past the end, black screen, caption overlaps).
**Warnings** are for judgement (long caption lines, very short captions or shots, length off target, unknown keys).

## 6. Render
```
python scripts/render.py <workdir> --preview     # half size, quick look
python scripts/render.py <workdir>               # -> <workdir>/out/edit.mp4
```
Saves check frames in `<workdir>/out/frames/`: `start.jpg`, `mid.jpg`, `end.jpg`, `cap_01.jpg`... (one per caption).
Options: `--out`, `--crf` (quality, default 18; 23-28 for a smaller file), `--engine <dir>`, `--concurrency`.
A 60 s 1080x1920 highlight takes a few minutes. Run one render at a time per engine folder.

## 7. Look, fix, render again
Open the frames and look at them yourself before saying it is done:
- [ ] The first frame already shows the hook (not a blank card, a black frame or an intro)
- [ ] Burned-in subtitles, logos or black bars are fully cropped away; nothing important cropped off
- [ ] Every caption inside the frame, matching the words, no broken glyphs, no line starting with a particle,
      highlight on the right word, not covering a face or the key object (`caption_position`)
- [ ] Title readable and not covering the picture; no doubled captions (ours plus burned-in ones)
- [ ] Cuts land between words; nothing ends mid-sentence; no scene appears twice
- [ ] Sound: compare `ffmpeg -i out/edit.mp4 -af volumedetect -f null -` with the source; listen once if you can
Fix `highlight.json` (or `edit.json`), run steps 4-6 again. Usually one or two rounds.

## 8. Deliver
Give the user: the mp4 path, length and resolution, the table of picked segments (source time -> time in the
highlight, reason), what still needs their eyes and ears (caption spelling of names, anything left out on
purpose), and say that changes are cheap: "swap segment 3", "make it 30 seconds", "captions off", "horizontal version"
only need step 4 onward again.

## Troubleshooting
| Problem | Fix |
|---|---|
| `npm`/`npx` not found | Install Node.js 18+, open a new terminal |
| `npm install` fails | Check the internet connection / proxy; delete the engine folder and retry |
| Bundling fails with a path error | `#` or unusual characters in the engine path: `--engine C:/edit-engine` |
| Korean/Japanese shows boxes | No CJK font (common on Linux): install `fonts-noto-cjk`, or set `style.font_file` |
| Speech recognition is slow | No GPU in use: install the nvidia packages (Setup), or `--model base`, or accept CPU time |
| CUDA / cuDNN error | It retries on the CPU automatically; or pass `--device cpu` |
| Few or no scene changes found | Calm footage: `--scene-threshold 0.15`; frames are still sampled every `--frame-every` seconds |
| Transcript words wrong | Use `--model medium` or `large-v3`, and fix captions with a segment's `caption` |
| A cut clips a word | Take edges from `transcript.txt` (2 decimals); keep `snap` on |
| Video looks frozen or black | Re-encode the source: `ffmpeg -i in.mov -c:v libx264 -pix_fmt yuv420p -c:a aac fixed.mp4` |
| URL download fails | Download the video yourself and pass the file |

---
만든이: sphereai.work (https://sphereai.work)
