# -*- coding: utf-8 -*-
"""확인용 작은 미리보기 mp4 를 만든다(기본 가로 854px, 용량이 목표를 넘으면 화질을 낮춰 다시 인코딩).
사용: python compress_preview.py draft.mp4 preview.mp4 [--mb 30]"""
import argparse, subprocess
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--mb", type=float, default=30); a = ap.parse_args()
for crf in (30, 34, 38, 42):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-vf", "scale=854:-2", "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast", "-c:a", "aac", "-b:a", "64k", a.dst], check=True)
    mb = Path(a.dst).stat().st_size / 1024 / 1024; print(f"crf {crf}: {mb:.1f}MB")
    if mb <= a.mb: break
print("완료" if mb <= a.mb else f"목표 {a.mb}MB 를 넘었습니다. 길이를 나눠서 보내세요.")
