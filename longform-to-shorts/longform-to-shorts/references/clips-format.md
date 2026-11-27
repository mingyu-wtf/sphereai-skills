# clips.json format

```json
{
  "language": "en",
  "style": {
    "crop": "face",
    "tighten": true,
    "accent": "#FFD60A",
    "caption_y": 0.70,
    "caption_size": 100,
    "max_chars": 22,
    "title_bar": true,
    "title_size": 78,
    "fit_zoom": 1.35,
    "trim_bottom": 0
  },
  "clips": [
    {
      "id": 1,
      "start": 77.8,
      "end": 135.2,
      "score": 9,
      "title": "Short on-screen title",
      "reason": "Why this moment works (for the user)",
      "caption": "Post caption, one or two lines",
      "hashtags": ["psychology", "introvert"],
      "crop": "fit"
    }
  ]
}
```

- `start` / `end`: absolute seconds in the source. Use the segment times from `transcript.txt` (`[mm:ss|seconds]`): start = the hook segment's start, end = the payoff segment's end.
- Per-clip keys override `style`: `crop`, `tighten`, `trim_bottom`, `fit_zoom`, `title_on_screen` (if the on-screen title should differ from `title`).
- `language`: the spoken language (from `meta.json`). For Korean, Japanese and Chinese captions are split by characters (`max_chars` default 12), otherwise by words (default 22).
- `caption_y`: vertical centre of the caption line, as a share of the height (0.55-0.80). Keep it above ~0.82 to stay clear of platform buttons.
- `trim_bottom`: share of the source height to cut off before framing (use 0.15-0.22 when the source has burned-in subtitles).
- `title_bar: false` hides the title; `captions: false` renders without captions.
