# -*- coding: utf-8 -*-
"""이미지 한 장 + 제목 글자 → 1280x720 썸네일(굵은 글씨 + 외곽선). 한글 글꼴을 PC에서 찾아 쓴다.
사용: python thumb.py image.jpg "제목 두 줄\n나눔" thumb.png [--variants 3]
--variants N : 글자 위치·색을 바꾼 안을 N개 만든다(thumb_1.png ...)"""
import argparse, os, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS = ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"]
STYLES = [("bottom", (255, 235, 59)), ("top", (255, 255, 255)), ("center", (255, 82, 82))]


def font(size):
    for f in FONTS:
        if os.path.exists(f): return ImageFont.truetype(f, size)
    sys.exit("한글 글꼴을 찾지 못했습니다. 글꼴 파일 경로를 FONTS 목록에 추가하세요.")


def make(img, text, pos, color, out):
    im = img.copy(); d = ImageDraw.Draw(im); lines = text.replace("\\n", "\n").split("\n"); size = 150
    while size > 50:
        f = font(size)
        if max(d.textlength(l, font=f) for l in lines) <= 1180: break
        size -= 6
    lh = int(size * 1.2); total = lh * len(lines); y0 = {"top": 40, "center": (720 - total) // 2, "bottom": 720 - total - 40}[pos]
    for i, l in enumerate(lines):
        x = (1280 - d.textlength(l, font=f)) / 2; d.text((x, y0 + i * lh), l, font=f, fill=color, stroke_width=max(6, size // 14), stroke_fill=(0, 0, 0))
    im.save(out); print("저장:", out)


ap = argparse.ArgumentParser(); ap.add_argument("image"); ap.add_argument("text"); ap.add_argument("out"); ap.add_argument("--variants", type=int, default=1); a = ap.parse_args()
base = Image.open(a.image).convert("RGB"); s = max(1280 / base.width, 720 / base.height); base = base.resize((int(base.width * s) + 1, int(base.height * s) + 1))
base = base.crop(((base.width - 1280) // 2, (base.height - 720) // 2, (base.width + 1280) // 2, (base.height + 720) // 2))
if a.variants <= 1: make(base, a.text, *STYLES[0], a.out)
else:
    p = Path(a.out)
    for i in range(min(a.variants, len(STYLES))): make(base, a.text, *STYLES[i], str(p.with_name(f"{p.stem}_{i+1}{p.suffix}")))
