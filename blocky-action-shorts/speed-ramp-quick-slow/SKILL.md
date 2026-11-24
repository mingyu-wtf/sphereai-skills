---
name: speed-ramp-quick-slow
description: Simple fast-then-slow speed changes and freeze frames on a rendered action clip with ffmpeg: split, retime, freeze, rejoin. 렌더한 영상에 퀵앤 슬로우 속도 변화 넣기.
---

# Speed Ramp: Quick and Slow

The "quick and slow" look: motion rushes in, slows down at the key moment, then rushes out. This skill does it on a finished render with ffmpeg, so no extra 3D work is needed.

## 1. Plan
- Pick 2-3 moments in a 30-second short: the hero landing, the punch contact, the bully flying away. Do not slow everything; the contrast is what makes it hit.
- For each moment write: start second, end second, speed (for example 0.5 = half speed, 2 = double speed).
- Render that section at a higher frame rate if you can (for example 120 fps) so the slow part stays smooth.

## 2. Cut and retime
1. Cut the clip into parts at the planned seconds: `ffmpeg -i in.mp4 -ss <a> -to <b> -an part1.mp4`.
2. Change the speed of each part with `setpts`:
   - half speed: `-vf "setpts=2.0*PTS"`
   - double speed: `-vf "setpts=0.5*PTS"`
3. Freeze frame at contact: hold the last frame of a part with `-vf "tpad=stop_mode=clone:stop_duration=0.1"`.
4. Re-encode every part with the same size, fps and codec (`-r 60 -c:v libx264 -pix_fmt yuv420p`).
5. Join with a concat list: `ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4`.

## 3. Check
- Watch the result at full speed on a phone-size screen.
- The total length still fits the plan (a slow part makes the video longer).

## Output
The retimed clip and the list of moments with their speeds.

---
만든이: sphereai.work (https://sphereai.work)
