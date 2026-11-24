# -*- coding: utf-8 -*-
"""컷 설명(한 줄에 한 컷)에 고른 스타일 문구를 붙여 이미지 프롬프트 목록을 만든다.
사용: python build_prompts.py cuts.txt oil [--out prompts.txt]    스타일 이름 = styles/ 폴더의 파일 이름(oil, ink, watercolor, classical, woodblock, webtoon, clay, photoreal 또는 직접 추가한 것)"""
import argparse
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument("cuts"); ap.add_argument("style"); ap.add_argument("--out", default="prompts.txt"); a = ap.parse_args()
sf = Path(__file__).resolve().parent / "styles" / (a.style + ".md")
if not sf.exists(): raise SystemExit("없는 스타일: " + a.style + " (styles/ 폴더의 파일 이름을 쓰세요)")
style = next(l.strip() for l in sf.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#") and not l.startswith(">"))
tail = "16:9 wide cinematic composition. No text, no letters, no captions, no watermark, no modern objects."
lines = [l.strip() for l in Path(a.cuts).read_text(encoding="utf-8").splitlines() if l.strip()]
Path(a.out).write_text("\n\n".join(f"[C{i:03d}] {style}. {l}. {tail}" for i, l in enumerate(lines, 1)), encoding="utf-8")
print(f"{len(lines)}컷 → {a.out} (스타일: {a.style})")
