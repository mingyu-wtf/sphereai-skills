# cards.json format and writing rules

```json
{
  "cards": [
    {"role": "cover",      "title": "...", "body": "...", "time": 60},
    {"role": "background", "title": "...", "body": "..."},
    {"role": "point_1",    "title": "...", "body": "..."},
    {"role": "closing",    "title": "...", "body": "..."}
  ],
  "description": "Instagram caption: hook + 2-3 sentences + about 5 hashtags",
  "first_comment": "Suggested first comment that includes the original video link",
  "highlights": [
    {"start": 245.0, "end": 260.8, "title": "optional clip title",
     "subs": [{"start": 245.0, "end": 247.3, "ko": "한글 자막", "orig": "original line"}]}
  ]
}
```

- `time` (seconds) picks the video frame used as that card's image; without it frames are spaced evenly. Pick frames that show what the card says.
- `**word**` in a title or body colors that word with the accent. Use it for one or two key words per title, not more. Markers do not count toward the limits.
- `highlights` are part of every run (2 clips). `prepare_subs.py` fills `subs` from the transcript. All times are absolute seconds in the source video.

## Card roles (in order)
| role | count | content |
|---|---|---|
| `cover` | 1 (required) | title: the video's idea rewritten as a hook; body: one curiosity-raising line |
| `background` | 1 | the topic or situation |
| `point_1` ... `point_N` | 1 or more | key claims/information, most important first; the last one leads naturally to the conclusion |
| `closing` | 1 (required) | one-line takeaway + a nudge to watch the original video |

5-10 cards in total, decided by length and information density. One message per card.

## Character limits (Korean, hard caps - the layout overflows above these)
- cover: title 24, body 36
- every other card: title 20, body 110

## Style
- Korean, short clear sentences, a light spoken tone.
- No emoji on cards. A few emoji are fine in `description`.
- `description`: hook + 2-3 sentences + about 5 hashtags. Mention the source channel.
- `first_comment`: one or two sentences including `https://www.youtube.com/watch?v=<video id>`.

## Highlight selection
- Two spans from different parts of the video, not overlapping.
- 10-20 s each; start where a caption line starts, end where one ends; never cut a sentence in half.
- Pick the strongest claim, a reversal, or a quotable line.

## Subtitle lines (`subs`)
- One entry per caption line (or half a line when a line is long). Use the caption timing from `transcript.json`.
- `ko`: 34 characters or fewer is best (two short lines); hard warning above 44.
- For Korean videos `ko` is simply the spoken line. For foreign videos translate naturally; keep `orig` if the user wants the original shown (`--show-original`).
