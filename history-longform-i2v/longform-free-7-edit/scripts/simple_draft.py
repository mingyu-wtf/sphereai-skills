# -*- coding: utf-8 -*-
"""[무료판] 이미지 폴더 + 나레이션 mp3 → 가편집 mp4. 이미지 개수만큼 나레이션 길이를 똑같이 나눠 천천히 확대한다. ffmpeg 만 필요.
사용: python simple_draft.py images narration.mp3 draft.mp4"""
import subprocess, sys, tempfile
from pathlib import Path

imgs_dir, audio, out = sys.argv[1:4]
imgs = sorted(p for p in Path(imgs_dir).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio], capture_output=True, text=True).stdout.strip())
d = total / len(imgs); fps = 24; frames = int(d * fps); tmp = Path(tempfile.mkdtemp()); parts = []
for i, p in enumerate(imgs):
    o = tmp / f"{i:03d}.mp4"
    vf = f"scale=2400:-2,zoompan=z='min(zoom+0.0006,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps},format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(p), "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-crf", "18", str(o)], check=True); parts.append(o)
lst = tmp / "l.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", audio, "-c:v", "copy", "-c:a", "aac", "-shortest", out], check=True)
print(f"완료: {out} ({len(imgs)}컷, 컷당 {d:.1f}초)")
