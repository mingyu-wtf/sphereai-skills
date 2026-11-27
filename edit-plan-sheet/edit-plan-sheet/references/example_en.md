# Worked example: edit plan for "The 2-minute rule" (30 s Short)

Inputs from step 0:

1. Narration: the 10 lines from the shorts-blueprint example ("Writing it down is why it never gets done." … "So next time you reach for a sticky note…").
2. Clips provided:
   | File | Length | Content |
   |---|---|---|
   | c01_note_write.mp4 | 6 s | Close-up, hand writing on a sticky note |
   | c02_monitor_notes.mp4 | 8 s | Wide, monitor covered in sticky notes |
   | c03_sink.mp4 | 5 s | Top-down, sink with one cup and a plate |
   | c04_timer.mp4 | 4 s | Close-up, phone timer set to 2:00 |
   | c05_email_send.mp4 | 7 s | Medium, typing and sending an email |
   | c06_wash_cup.mp4 | 9 s | Top-down, washing a cup (natural water sound) |
   | c07_clean_desk.mp4 | 5 s | Wide, clean desk |
3. Format: vertical Short, 30 s
4. Mood: fast and friendly

---

## Summary
30-second vertical Short / 1080×1920 / 10 shots, 2–4 s each / narration at about 1.1x.

## Shot list
| # | Time (s) | Visual | Narration | Caption | Sound | Notes |
|---|---|---|---|---|---|---|
| 1 | 0–1.5 | c01_note_write 0:01–0:02.5 | Writing it down is why it never gets done. | Writing it down = never done | Pen scratch (SFX) | Hook. Note in center third |
| 2 | 1.5–4 | c02_monitor_notes 0:00–0:02.5 | Every tiny task becomes a note. | Every tiny task → a note | Paper rustle, low | Wide after close-up |
| 3 | 4–7 | c03_sink 0:00–0:03 | And notes turn into piles. | Notes → piles | — | Top-down |
| 4 | 7–10 | **missing**: hand peeling a note off the screen | Try this instead. | Try this instead | Whoosh (SFX) | See missing scenes |
| 5 | 10–14 | c04_timer 0:00–0:04 | If it takes less than two minutes… | Under 2 minutes? | Timer beep | Emphasis color on "2 minutes" |
| 6 | 14–17 | c05_email_send 0:03–0:06 | …do it right now. | Do it now | Send sound (SFX) | Cut on the click |
| 7 | 17–20 | c06_wash_cup 0:02–0:05 | Don't write it. Don't plan it. | Don't write it | Original water sound, low | Keep clip audio here only |
| 8 | 20–22 | **missing**: binning a stack of sticky notes | Just finish it. | Just finish it | Crumple (SFX) | |
| 9 | 22–26 | c07_clean_desk 0:00–0:04 (slow push-in) | Ten small things, gone before lunch. | 10 things, gone | Light chime on "gone" | Payoff |
| 10 | 26–30 | c01_note_write 0:04–0:06 (hand reaching, stops) | So next time you reach for a sticky note… | Next time… | Pen click | Loops into shot 1 |

Note on reuse: only c01 appears twice, at different moments (shots 1 and 10 are the deliberate loop). Everything else is used once.

## Missing scenes
1. Shot 4: hand peeling a sticky note off the monitor (medium, 3 s)
2. Shot 8: dropping a stack of crumpled notes into a bin (wide, 2–3 s)
3. Optional, shot 9: empty clean sink (top-down, 2 s) for a desk + sink split screen

## Caption rules
- One line per caption, a few words each; every caption readable in about 1 second
- One bold sans-serif font; emphasis color (yellow) only on "2 minutes" (shot 5) and "gone" (shot 9)
- Captions sit in the middle third, clear of the title area, the bottom bar, and the right-side buttons
- Final check: "2" is a digit everywhere in captions; narration says "two"

## Sound plan
- Narration: recorded at normal speed, sped to about 1.1x; trim breaths, keep the pause before "…do it right now."
- Music: one upbeat track with a clear license; source and license terms: **[fill in before export]**. Start at 15–20 dB under the narration and adjust by ear; no music in the last 0.5 s so the loop into shot 1 is clean.
- SFX: pen scratch (1), whoosh (4), timer beep (5), send (6), crumple (8), chime (9), pen click (10). Each marks a cut or an emphasis.
- Clip audio: muted on every clip except c06 (water).

## Color and picture
- c03 and c06 are top-down kitchen shots under warmer light than the desk clips; nudge white balance so the desk and kitchen shots match.
- Check c02 for any visible brand logo on the monitor; crop or blur if present.

## Final checklist (before export)
- [ ] Hook (shot 1) grabs attention within the first 1.5 s
- [ ] Picture doesn't linger after the last narration line
- [ ] Caption typos and numbers checked
- [ ] Music doesn't cover the voice on phone speakers
- [ ] Ending: no trailing silence; total length is 30 s
- [ ] First, middle, and last frames checked by eye; loop from shot 10 to shot 1 plays smoothly

---

## Part B: the same plan as edit.json (first shots)

Narration recorded as one file per line (`audio/n01.mp3` …), so each caption follows its file and the files play back to back.
The two missing scenes stay as labelled placeholders until the real clips arrive.

```json
{
  "format": "9:16",
  "fps": 30,
  "target_length": 30,
  "style": {"captions": "shorts", "lang": "en", "accent_color": "#FFD43B"},
  "clips": [
    {"src": "clips/c01_note_write.mp4", "in": 1.0, "out": 2.5},
    {"src": "clips/c02_monitor_notes.mp4", "in": 0, "out": 2.5},
    {"src": "clips/c03_sink.mp4", "in": 0, "out": 3},
    {"color": "#333333", "duration": 3},
    {"src": "clips/c04_timer.mp4", "in": 0, "out": 4},
    {"src": "clips/c05_email_send.mp4", "in": 3, "out": 6},
    {"src": "clips/c06_wash_cup.mp4", "in": 2, "out": 5, "volume": 0.4},
    {"color": "#333333", "duration": 2},
    {"src": "clips/c07_clean_desk.mp4", "in": 0, "out": 4, "zoom": "in"},
    {"src": "clips/c01_note_write.mp4", "in": 4, "out": 6}
  ],
  "narration": [
    {"src": "audio/n01.mp3"}, {"src": "audio/n02.mp3"}, {"src": "audio/n03.mp3"}
  ],
  "music": {"src": "audio/music_licensed.mp3", "volume": 0.25, "duck_db": 12, "fade_out": 0.5},
  "sfx": [
    {"src": "sfx/pen_scratch.wav", "at": 0.1},
    {"src": "sfx/whoosh.wav", "at": 7.0},
    {"src": "sfx/timer_beep.wav", "at": 10.2}
  ],
  "captions": [
    {"text": "Writing it down\n= never done", "start": 0.0, "end": 1.5, "highlight": ["never done"]},
    {"text": "Every tiny task\n→ a note", "start": 1.5, "end": 4.0},
    {"text": "Notes → piles", "start": 4.0, "end": 7.0},
    {"text": "Under 2 minutes?", "start": 10.0, "end": 14.0, "highlight": ["2 minutes"]}
  ],
  "titles": [
    {"kind": "lower_third", "text": "MISSING: peel a note off the screen", "start": 7.0, "end": 10.0, "position": "top"}
  ]
}
```

Then: `python scripts/check_edit.py work` → fix errors → `python scripts/render.py work --preview` →
look at `work/out/frames/` → adjust → `python scripts/render.py work`.
