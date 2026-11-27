# Edit plan (shot list, rhythm, captions, sound)

Use this when the user brings a script and several clips instead of one video, or wants only a plan to edit
by hand in Premiere, DaVinci Resolve, CapCut or another editor. The same rules also apply to highlights.
Worked example: `example_en.md` (a 30-second Short, "The 2-minute rule").

## 0. Get these first
1. The script or narration text
2. The list of clips (file name, length, what's in it). If the files are on disk, run
   `python scripts/media_inventory.py <folder>`, then look at a frame of any clip whose content you don't know.
3. Final format: horizontal long-form / vertical Short, and target length
4. Mood: calm / fast / humorous / documentary (pick one)
5. For rendering: the narration audio (or none), music and sound effects the user has rights to, a font file if preferred

## 1. Shot list
| # | Time (s) | Visual | Narration | Caption | Sound | Notes |
- Split the script into sentences and assign a matching visual to each line.
- Fit visual length to narration length. If you run short of footage, add a scene rather than stretching a slow section.
- Don't reuse the same clip over and over. If there aren't enough clips, list the missing scenes separately.

## 2. Rhythm
- Don't make every cut the same length. Explanations run longer, transitions shorter.
- At each cut, change the framing or the distance.
- In long videos, add a change every 3-4 minutes (a scene change, a graphic, a sound effect, or a shift in mood).

## 3. Caption rules
- Captions say the same thing as the voice. Do a final check on numbers and proper nouns.
- Each caption should be readable in about 1-1.5 seconds per line. If the voice keeps going after a caption
  disappears, the caption was too short-lived.
  - Common subtitle guides cap a line at about 42 characters in English, 16 in Korean, 13 in Japanese.
    Shorts captions should be much shorter than that.
  - Break lines at natural phrase boundaries; don't split a name, a number and its unit, or (in Korean and
    Japanese) a word and its particle.
- One font throughout, one colour for emphasis. The font must cover the script (Korean/Japanese need CJK fonts).
- In Shorts, keep captions away from the top, bottom and right edges.

## 4. Sound plan
- The voice matters most. Duck music clearly under it (15-20 dB below the voice to start, adjust by ear).
- Clean up breaths and long pauses, but don't break the rhythm of speech.
- Sound effects only at scene changes and emphasis points. Every one needs a reason.
- Fully mute clips whose original audio isn't needed.
- Only music and sound effects you have the rights to (write the source and license terms in the plan).

## 5. Colour and picture
- If clips differ in brightness and colour, match them scene by scene. Keep grading light.
- Check that no clip still carries a logo, watermark or burned-in subtitles you don't want (`crop` removes them).

## 6. Output format of a plan
```
[One-line summary / format / target length]
[Shot list table]
[Missing scenes] (if any)
[Caption rules summary]
[Sound plan] narration / music (source and terms) / SFX positions
[Final checklist]
```

## 7. Final checklist (before export)
- [ ] Something grabs attention in the first 3 seconds
- [ ] The picture doesn't linger long after the voice ends
- [ ] Caption typos and numbers are checked
- [ ] The music doesn't cover the voice
- [ ] Silence at the end and total length are checked
- [ ] First, middle and last frames checked by eye

## 8. From the plan to edit.json
Each shot list row becomes one `clips` entry (`edit-json.md`):
- Push-in -> `"zoom": "in"`. Horizontal footage in a vertical video -> `"fit": "blur"`.
- Narration -> `narration` (one file per sentence plays back to back; or one file with `start`).
- Captions -> `captions` with `start`/`end` from the narration timing; the emphasis word -> `highlight`.
  One long narration file: `python scripts/transcribe_captions.py narration.mp3 --lang ko --script script.txt --into <workdir>/edit.json`.
- Music -> `music` (`duck_db` 10-15). SFX -> `sfx` with `at`. Title / name bar -> `titles`.
- Missing scenes -> a `color` placeholder plus a title saying what belongs there; tell the user.
- Clip audio is muted unless you set `volume`.
Then check, render and look at the frames exactly as in SKILL.md steps 5-7.
