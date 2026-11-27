# edit.json reference

`edit.json` is the shot list in a form the renderer can read. Put it in the work folder next to the media
(or anywhere; file paths are relative to the folder that holds `edit.json`, absolute paths also work).

All times are **seconds** (numbers, or `"m:ss.s"` strings such as `"1:05.5"`). The total length is worked out
automatically: the longest of the picture track, the narration (+ `tail`), captions and titles.

## Minimal example (vertical Short)

```json
{
  "format": "9:16",
  "fps": 30,
  "style": {"captions": "shorts", "lang": "en"},
  "clips": [
    {"src": "clips/c01_note_write.mp4", "in": 1.0, "out": 2.5, "zoom": "in"},
    {"src": "clips/c02_monitor_notes.mp4", "in": 0, "out": 2.5},
    {"src": "img/clean_desk.jpg", "duration": 4, "zoom": "in", "transition": "crossfade"}
  ],
  "narration": [{"src": "audio/narration.mp3", "start": 0}],
  "music": {"src": "audio/music.mp3", "volume": 0.25, "duck_db": 10},
  "sfx": [{"src": "sfx/whoosh.wav", "at": 1.4}],
  "captions": [
    {"text": "Writing it down\n= never done", "start": 0.0, "end": 1.5, "highlight": ["never done"]},
    {"text": "Every tiny task → a note", "start": 1.5, "end": 4.0}
  ],
  "titles": [{"kind": "title", "text": "The 2-minute rule", "start": 0, "end": 1.2}]
}
```

## Top level

| Key | Default | Meaning |
|---|---|---|
| `format` | `"9:16"` | `"16:9"` 1920x1080, `"9:16"` 1080x1920, `"1:1"` 1080x1080, `"4:5"` 1080x1350 |
| `width`, `height` | from format | Custom size (both even numbers). Overrides `format` |
| `fps` | `30` | Frames per second |
| `background` | `"#000000"` | Colour behind everything (shows in `contain` bars) |
| `duration` | auto | Force the total length. Leave out to compute it |
| `tail` | `0.4` | Seconds kept after the last narration ends |
| `target_length` | - | Planned length; the check warns if the result is more than 10% off |
| `style` | see below | Caption and title look |
| `notes`, `title` | - | Free text, ignored by the renderer |

## `style`

| Key | Default | Meaning |
|---|---|---|
| `captions` | `"shorts"` for vertical, `"standard"` otherwise | `shorts` = big bold outlined words with a pop-in, one highlight colour. `standard` = smaller line on a dark box at the bottom (long-form) |
| `lang` | detected from caption text | `ko`, `ja`, `en`, ... Picks the font fallback order and line-breaking rules |
| `font_file` | - | A `.ttf`/`.otf`/`.woff2` file to use for all text. Recommended for a consistent look |
| `font_family` | - | An installed font name to try first (e.g. `"Pretendard"`) |
| `font_weight` | `800` | Weight for captions and titles |
| `text_color` | `"#FFFFFF"` | Main text colour |
| `accent_color` | `"#FFD43B"` | Highlight colour (the one emphasis colour) |
| `outline_color` | `"#000000"` | Outline of `shorts` captions and titles |
| `box_color` | `"rgba(0,0,0,0.55)"` | Box behind `standard` captions and lower thirds |
| `caption_scale` | `1.0` | Make all captions bigger or smaller |

Without `font_file` the renderer tries, in order: your `font_family`, then fonts that cover Korean and Japanese
on Windows, macOS and Linux (Pretendard, Noto Sans KR/JP, Noto Sans CJK, Apple SD Gothic Neo, Malgun Gothic,
Hiragino Sans, Yu Gothic, Meiryo). On a Linux server with no CJK fonts, install `fonts-noto-cjk` or give a `font_file`.

## `clips` - the picture track

Clips play **back to back in list order**. Each one starts where the previous one ends
(a crossfade makes it start `transition_duration` earlier, overlapping the previous clip).

| Key | Default | Meaning |
|---|---|---|
| `src` | - | Video (`mp4 mov webm mkv m4v avi`) or image (`jpg png webp gif bmp`) |
| `color` | - | Instead of `src`: a plain colour shot, e.g. `"#1d3557"` (needs `duration`) |
| `in` | `0` | Video: where to start in the source file |
| `out` | end of file | Video: where to stop in the source file |
| `duration` | 3 for stills | Images and colours: time on screen. Videos: may be used instead of `out` |
| `speed` | `1` | Playback speed (2 = twice as fast, the shot lasts half as long) |
| `fit` | `"cover"` | `cover` fills the frame (crops edges), `contain` shows the whole picture with bars, `blur` = contain over a blurred copy (good for horizontal footage in a vertical video) |
| `zoom` | `null` | `"in"` or `"out"`: slow push (Ken Burns) across the shot |
| `zoom_amount` | `0.06` | How far the zoom goes (0.06 = 6%) |
| `volume` | `0` | Original clip audio. **Muted by default**; set e.g. `1` to keep it (highlights made by `plan_highlight.py` use `1`). It fades along with crossfades |
| `audio_fade` | `0.06` | Seconds of fade on the original sound at hard cuts, so cuts do not click (at least 2 frames) |
| `crop` | - | Cut edges off the source before `fit`: `{"top", "bottom", "left", "right"}`, fractions of the picture (`0.19` = 19%) or pixels. For burned-in subtitles, logos, black bars. The blurred fill uses the cropped picture too |
| `transition` | `"cut"` | `"cut"` or `"crossfade"` (from the previous clip) |
| `transition_duration` | `0.4` | Crossfade length; shortened automatically if a clip is too short |

The check reports an error if the picture track ends before the video does (black screen).

## `narration`

A list (or a single object). Files play **back to back** unless `start` is given, so one file per sentence works well.

| Key | Default | Meaning |
|---|---|---|
| `src` | - | Audio file (a video file's audio also works) |
| `start` | right after the previous narration | Position on the timeline |
| `gap` | `0` | Pause before this file when `start` is not given |
| `in`, `out` | whole file | Part of the file to use |
| `volume` | `1` | 0 to 1 |

## `music`

A single object (or a list for several pieces).

| Key | Default | Meaning |
|---|---|---|
| `src` | - | Audio file |
| `start` | `0` | Position on the timeline |
| `in` | `0` | Where to start in the file |
| `volume` | `0.25` | Base level, 0 to 1 |
| `duck_db` | `10` | How far the music drops while narration plays (dB). `0` = no ducking |
| `loop` | `true` | Repeat if the file is shorter than the video |
| `fade_in` | `0` | Seconds |
| `fade_out` | `1.0` | Seconds, at the end of the music |
| `duration` | to the end | Stop the music earlier |

## `sfx`

List of `{ "src": "...", "at": seconds, "volume": 0.7 }`. Each plays once, in full.

## `captions`

| Key | Default | Meaning |
|---|---|---|
| `text` | - | The words. `\n` forces a line break (put it at a phrase boundary) |
| `start`, `end` | - | Seconds on the timeline |
| `highlight` | `[]` | Words or phrases shown in `accent_color`, e.g. `["2 minutes"]` |
| `position` | `lower` (shorts) / `bottom` (standard) | `top`, `center`, `lower` (about 2/3 down), `bottom` |
| `style` | `style.captions` | Override per caption: `shorts` or `standard` |

Vertical videos keep `bottom` and `top` captions clear of the app buttons. Captions at the same position must not overlap.
The check also warns about lines that are long for the style (shorts: ko 12, ja 11, en 24 characters;
standard: ko 16, ja 13, en 42), more than 2 lines, less than 0.6 s on screen, and fast reading speed
(about 14 characters/s for Korean, 9 for Japanese, 20 for English).

## `titles`

| Key | Default | Meaning |
|---|---|---|
| `kind` | `"title"` | `title` = big centred card over a dimmed picture; `lower_third` = name bar at the lower left |
| `text` | - | Main line |
| `sub` | `""` | Smaller second line |
| `start`, `end` | - | Seconds |
| `position` | `center` (title) / `bottom` (lower third) | `top`, `center`, `lower`, `bottom` (lower thirds use `top` or `bottom`) |
| `dim` | `true` for a centred title, else `false` | Darken the picture behind a title card |

## From shot list to edit.json

| Shot list column | edit.json |
|---|---|
| Visual (file + source time) | one `clips` entry: `src`, `in`, `out` (or `duration`) |
| Time (s) | follows from the clip lengths; check the table that `check_edit.py` prints |
| Narration | `narration` files (one per line, or one file + caption times) |
| Caption | `captions` entry with the same start/end as the line; emphasis → `highlight` |
| Sound: SFX | `sfx` entry with `at` |
| Sound: keep clip audio | `"volume": 1` on that clip |
| Notes: remove burned-in subtitles / logo | `"crop": {"bottom": 0.15}` |
| Notes: push-in / slow zoom | `"zoom": "in"` |
| Missing scene | a placeholder: `{"color": "#333333", "duration": 2}` plus a `title` saying what goes there, until the real clip exists |
