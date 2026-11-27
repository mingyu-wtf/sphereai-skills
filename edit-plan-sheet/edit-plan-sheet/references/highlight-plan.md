# highlight.json reference

`highlight.json` is your list of picked parts. Put it in the work folder that `analyze.py` filled and run
`python scripts/plan_highlight.py <workdir>`; it writes `edit.json` (see `edit-json.md`), which you can still edit by hand.

All times are **seconds in the source video** (numbers, or `"m:ss.s"` strings). Take them from `transcript.txt`
(`[start - end]` per phrase) and `overview.txt` (shots).

## Example (60-second vertical Short from a 10-minute horizontal talk with burned-in subtitles)

```json
{
  "format": "9:16",
  "target_length": 60,
  "fit": "blur",
  "crop": {"bottom": 0.19, "left": 0.05, "right": 0.05},
  "title": {"text": "Why quiet people\nget tired", "duration": "all"},
  "segments": [
    {"start": 109.82, "end": 118.36, "hook": true, "highlight": ["tired"], "reason": "the core claim"},
    {"start": 77.64, "end": 84.70, "reason": "why", "caption": "Their brains take in far more of what is around them."},
    {"start": 94.62, "end": 103.40, "reason": "example: the cafe"},
    {"start": 570.26, "end": 574.86, "reason": "closing line"}
  ]
}
```

## Top level

| Key | Default | Meaning |
|---|---|---|
| `segments` | - | The picked parts (below). Required |
| `format` | `"9:16"` | `9:16`, `16:9`, `1:1`, `4:5` |
| `target_length` | - | Seconds; the script prints the difference, the check warns if more than 10% off |
| `fit` | `blur` for horizontal source in a vertical video, else `cover` | `cover`, `contain`, `blur` |
| `crop` | - | Cut edges off the source before fitting: `{"top","bottom","left","right"}` as fractions (0.19 = 19%) or pixels. Use it for burned-in subtitles, logos, black bars |
| `volume` | `1` | Original sound level (0-1) |
| `transition` | `"crossfade"` | `crossfade` or `cut` between segments |
| `transition_duration` | `0.3` | Seconds |
| `end_fade` | `0.3` | Fade to black at the end, then black for the same time (0 = none) |
| `order` | `"as_listed"` | `as_listed` (your story order) or `source` (time order). Hook segments always go first |
| `snap` | `true` | Move edges that land inside a word to the word's edge, add a short breath |
| `captions` | `"auto"` | `auto` = from the transcript (or each segment's `caption`), `none` = no captions |
| `caption_position` | style default | `top`, `center`, `lower`, `bottom` |
| `caption_max_chars` | shorts: ko/ja 10, en 22; standard: ko 16, ja 13, en 42 | Characters per line (captions use up to 2 lines) |
| `lang` | from the transcript | `ko`, `ja`, `en` ... |
| `title` | - | `{"text", "sub", "duration", "position", "kind", "dim"}`. `duration` in seconds or `"all"`. Default position: `top` (vertical) / `center` |
| `end_title` | - | Same, shown for the last `duration` seconds |
| `style` | - | Passed to `edit.json` `style` (font, colours, caption scale) |
| `music`, `sfx` | - | Passed to `edit.json` unchanged (only music the user has rights to; usually leave it out and keep the original sound) |
| `source` | `meta.json` source | Video file in the work folder |

## `segments`

| Key | Default | Meaning |
|---|---|---|
| `start`, `end` | - | Seconds in the source |
| `reason` | - | Why you picked it (kept as a note in `edit.json`; also helps the user review) |
| `hook` | `false` | Put this segment first |
| `caption` | - | Exact words for this segment's captions (fixes speech-recognition mistakes, or adds text where nothing is said). Timing comes from the audio |
| `highlight` | - | Words shown in the accent colour |
| `zoom` | - | `in` / `out`: slow push across the segment |
| `fit`, `crop`, `volume`, `speed` | top-level value | Per-segment override. Avoid `speed` on speech |

## What the script prints

```
 # seg  source          in the video      len  reason
 1   1  1:49.8-1:58.4   0:00.0-0:08.5     8.5  [HOOK] the core claim
        note: starts right after '...' (mid-sentence?)
...
Total 60.1s (1:00.1), 8 segments, 31 captions; target 60s -> +0.1s
WARNING segment 4 repeats source 1:44.0-1:46.0 (also in segment 2)
```
Fix notes and warnings in `highlight.json` and run it again. `--dry-run` prints without writing.
