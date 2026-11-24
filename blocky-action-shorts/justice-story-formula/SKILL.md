---
name: justice-story-formula
description: Turn a one-line idea into a 30 s justice action shot list: wrong, hero arrives, chase, face-off, one hit, sent flying, ending, with 60 fps frame ranges. 참교육 이야기 공식과 컷 구성표.
---

# Justice Story Formula

A justice short works because the viewer is angry in the first seconds and satisfied at the end. This skill turns a one-line idea into a shot list that Blender scripts can follow.

## Inputs
- One-line story: bully, victim, what is taken or done, hero.
- `directing_note.md` from `action-shorts-directing-research` if it exists.

## The seven beats
| Beat | What happens | Must have |
|---|---|---|
| 1. The wrong | Bully takes something from or hurts someone weaker | A close-up of the act |
| 2. Hero arrives | Lands from the sky or walks in from far away | A landing impact and a low-angle hero shot |
| 3. Chase and block | Runs or dashes, gets ahead, blocks the way | Blocker and blocked in the same frame |
| 4. Face-off | Hero gets ready, bully trembles | Face close-ups of both |
| 5. One hit | A single punch or kick | A clear contact frame with an impact effect |
| 6. Sent flying | Bully flies into the sky and disappears | A twinkle when they vanish |
| 7. Ending | Object returned, cheering, a dance or a joke | A strong last image |

Keep beat 1 short. The audience must be on the victim's side early.

## Shot list format
Write one row per shot. Frame = seconds x 60 + 1.

| Shot | Frames | Beat | What we see | Camera | Effects | Speed |
|---|---|---|---|---|---|---|
| 01 | 1-90 | 1 | Bully walks up behind the victim | wide, eye level | - | normal |
| 02 | 91-150 | 1 | Hand grabs the bag (insert) | close-up | - | slow |

Group shots into 4-5 **sections** of 5-8 seconds. One Blender script per section. Sections share one absolute timeline (section B starts at the frame after section A ends).

## Basic checks
- Every key act (stealing, blocking, hitting) is visible on screen.
- Both sides of an action are in the same frame.
- Feet stay on the ground.
- The hero's face is never hidden.

## Output
`shot_list.md`: the seven beats, the shot table, and the section split with frame ranges. Next: `blocky-character-acting`.

---
만든이: sphereai.work (https://sphereai.work)
