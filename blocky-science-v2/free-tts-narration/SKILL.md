---
name: free-tts-narration
description: Free long-form narration with edge-tts: one voice, sentence by sentence, joined into one clean wav, plus a sentence time table that cuts and captions follow. 무료 edge-tts 나레이션과 문장별 시간표.
---

# Free TTS Narration

## Before you start
- Install: `pip install edge-tts`, and ffmpeg.
- edge-tts is an unofficial client for a Microsoft online voice service. Whether it may be used in monetised videos is not clearly stated. Tell the user this and let them decide; offer a licensed TTS as the alternative.
- List voices: `edge-tts --list-voices`. Pick one and keep it for the whole series.

## 1. Prepare the text
1. Take the narration from `script.md` and apply the TTS replacement table (digits -> spoken words).
2. Write `narration.txt`: **one line = one sentence**, **empty line = block boundary**.

## 2. Generate sentence by sentence
`edge-tts --voice <voice> --text "<sentence>" --write-media s001.mp3 --write-subtitles s001.vtt`

Generating per sentence makes it easy to redo one sentence and gives clean timings.

## 3. Join
- Put a short silence between sentences and a slightly longer one between blocks.
- Join with the ffmpeg **concat filter** into one wav (`-filter_complex "...concat=n=N:v=0:a=1"`). Do not use the `concat:` protocol on mp3 parts; it produces decoding errors at the joins.

## 4. Timings
- Measure each part's length (`ffprobe`) and add them up to get each sentence's start and end second in the joined file.
- Save a sentence table: sentence | start s | end s | start frame (s x fps + 1).

## 5. Check
- Listen to the first minute and the joins between blocks.
- Total length within the target. If not, change the script, not the speed.

## Output
`narration.wav` and the sentence frame table. Next: `science-scene-design` and `narration-synced-cuts`.

---
만든이: sphereai.work (https://sphereai.work)
