# Picking highlights

You have read `overview.txt`, `transcript.txt` and every `contact_sheet_*.jpg`. Now choose the parts.
Write the choice as `highlight.json` (format: `highlight-plan.md`).

## 1. Decide what the highlight is for
Ask (or assume from the request) one sentence: *"After watching, the viewer should feel / know ___."*
- Talk, lecture, podcast, explainer: the one idea worth sharing, with its best example.
- Vlog, trip, event: the feeling of the day: arrival, best moments, a closing moment.
- Game, sport: the build-up and the big moment(s), reactions.
- Product, review: the problem, the reveal, the verdict.
Everything you pick must serve that sentence. Leave out the rest, even if it is good.

## 2. The hook goes first (first 1-3 seconds)
The first segment decides whether people keep watching. Pick the strongest moment, not the start of the video:
- a surprising claim or a punchline ("being tired after people is not weakness, it is your brain working")
- a question the rest of the video answers
- the most striking picture, the loudest reaction, the moment of the goal or the reveal
Mark it `"hook": true`. It may come from the middle or the end of the source. Do not open with greetings,
"hello everyone", intros, logos or "in this video".

## 3. Tell a small story with the rest
After the hook, order the segments so they make sense to someone who never saw the source:
hook -> why / setup -> example or best moments -> fact or turn -> payoff -> closing line.
- Each segment should lead to the next. Read them in order as plain text: it must still make sense.
- Avoid references to things you cut ("as I said before", "this one", "here you can see" without the picture).
- End on a line or a picture that feels like an ending (a conclusion, a laugh, a wave, the sunset), not mid-thought.

## 4. Cut on clean edges
- **Never cut in the middle of a word**, and try not to cut in the middle of a sentence.
  Use the seconds in `transcript.txt` (each line is a phrase between pauses). Start at a line's start, end at a line's end.
  `plan_highlight.py` snaps edges that land inside a word and warns when an edge looks mid-sentence.
- Drop filler at the edges ("so", "and then", "um"): start one word later if the first word is a filler.
- Without speech, cut on a scene change (`scenes.json`) or on a beat in the sound, not in the middle of a movement.
- Keep a breath (0.1-0.3 s) after the last word so the voice does not sound clipped. The script adds it.

## 5. Variety and rhythm
- **Do not repeat the same scene.** Check the frame numbers: two segments should not show the same picture.
  Two segments from the same place in the source are a mistake (the script warns).
- Change something at every cut: a different picture, framing, speaker or place.
- Vary segment length: 2-4 s for quick beats, 6-12 s for a point that needs explaining. Avoid long runs of equal lengths.
- A segment over about 15 s in a Short should be very strong; otherwise split it or trim it.
- Contiguous parts of the source belong in one segment (a crossfade between two touching parts looks like a glitch).

## 6. When there is little or no speech (`meta.json` "speech": "little" or "none")
Pick by picture and sound instead:
- **Sound**: `LOUD` and `JUMP` marks in `overview.txt` and `audio_energy.json` (`loud`, `jumps`) point at laughs,
  cheers, impacts, goals, music drops. Look at the frames around them before you trust them: loud can also be wind or traffic.
- **Picture**: the contact sheets show every shot. Prefer frames with a face, action, a clear subject, good light, a view.
  Skip blurry, dark, shaky or empty frames and near-duplicates.
- **Scene changes**: many short shots close together = action or a montage; one long shot = a calm moment or a talk.
- Keep the original sound (ambience makes a vlog feel real). Captions: none, or a few short ones you write yourself
  (place names, "Day 1"), given as `caption` on a segment.

## 7. Fit the target length
- Sum of segment lengths minus about 0.3 s per crossfade = final length. `plan_highlight.py --dry-run` prints it.
- Aim within 10% of the target (Shorts: at most 3 minutes; 30-60 s is typical).
- Too long: drop the weakest segment first, then trim the edges of long ones. Do not speed speech up.
- Too short: add the next best moment that fits the story, not filler.

## 8. Captions and title
- Speech: `"captions": "auto"` makes captions from the transcript, one phrase each, 1-2 lines.
  Read them: speech recognition gets names, numbers and similar-sounding words wrong. Fix a segment by giving
  its exact words as `"caption"` (the timing still comes from the audio).
- `highlight` (one or two words per segment) shows the key word in the accent colour. Use it for numbers and the key idea.
- A title states the topic in a few words. Vertical: `"duration": "all"` at the top is common for Shorts.
- If the source already has captions burned into the picture, crop them off (`crop`) or turn ours off;
  never show two sets of captions.

## 9. Framing
- Horizontal source -> vertical Short: `fit: "blur"` (whole picture, blurred fill) is the safe default.
  `fit: "cover"` fills the screen but crops the sides away: only for footage with the subject in the middle.
- `crop` removes burned-in subtitles, logos or black bars before fitting (fractions of the picture).
  Check the contact sheet for where they sit, then look at the rendered frames to confirm they are gone.

## 10. Be honest about the material
Only the user's own videos or videos they have permission to use. Do not invent quotes in captions: they must
match what is said. If the source has nothing worth a highlight in some part, say so instead of padding.
