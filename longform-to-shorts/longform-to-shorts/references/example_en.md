# Worked example

Source: a 10-minute animated explainer (16:9, Korean narration, subtitles burned in at the bottom) about why some people feel recharged by time alone.

## 1. Prepare
```
python scripts/prepare.py "alone-time.mp4" --out work/alone-time --model medium
```
Result: language `ko`, 160 transcript lines, about 80 s on an RTX-class GPU.

## 2. What the agent saw
- Animation with no on-camera speaker -> `crop: fit`, except one cafe scene with a large character -> `face` tried, no face found, the script fell back to centre.
- Korean subtitles burned in at 82-90 % of the height -> `trim_bottom: 0.2`.

## 3. Picked moments (clips.json, shortened)
| id | source | score | on-screen title (translated) | why |
|---|---|---|---|---|
| 1 | 1:17-2:15 | 9 | "An alone-time brain is 10 TV channels at once" | everyday scene (noisy cafe) + memorable metaphor + research payoff |
| 2 | 2:25-2:57 | 8 | "Sensitive people were the group's lookouts" | turns a weakness into a strength, strong last line |
| 3 | 6:23-7:00 | 8 | "Say this one line to a friend who asks why you went quiet" | copyable script, relationship pain point |
| 4 | 8:54-9:21 | 7 | "4 things to try from today" | numbered list -> saves |

Skipped: the opening (needs the whole video), the closing quote (no payoff on its own), the "next video" line.

## 4. Render
```
python scripts/render.py work/alone-time
```
```
clip 01:  57.2s  (pauses removed  0.2s, face, centre (no face found))
clip 02:  29.8s  (pauses removed  2.2s, fit)
clip 03:  35.9s  (pauses removed  0.6s, fit)
clip 04:  26.8s  (pauses removed  0.1s, fit)
```
About 80 s for all four clips.

## 5. Check
- First pass showed the source subtitles under ours -> added `trim_bottom: 0.2`.
- `fit` left large blurred bands -> `fit_zoom` 1.35 (picture fills more, sides trimmed slightly).
- Every clip starts on its hook sentence and ends right after the payoff line.

## 6. posts.txt (one entry)
```
[clip_03]  36s  source 6:23-7:00
title: Say this one line to a friend who asks why you went quiet
caption: When you need time alone, try telling your friend this
#relationships #introvert #psychology
```
