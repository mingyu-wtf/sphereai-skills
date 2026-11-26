# -*- coding: utf-8 -*-
"""prompts.txt 의 각 블록을 생성 전에 검사한다(크레딧·시간 낭비 방지).
검사: 글자 수(3,500 이하) / 필수 문구(첫 프레임·렌즈 히트·무언·무글자·음향) / 금지어(전환어·잔혹 어휘·현대 사물·립싱크 암시) / 한글 포함 / 렌즈 히트 개수(2~6) / 인물 중앙 구도 금지 문구.
사용: python lint_t2v_prompts.py prompts.txt        (문제가 있으면 종료코드 1)"""
import re, sys
from pathlib import Path

try: sys.stdout.reconfigure(errors="replace")
except Exception: pass

REQUIRED = [
    ("FROM THE VERY FIRST FRAME", "첫 프레임부터 보일 것 문단"),
    ("Lens-hit events in order", "렌즈 히트 정리 줄"),
    ("no lip movement", "무언 문장"),
    ("No on-screen text", "무글자 문장"),
    ("LIGHTING:", "조명 문단"),
    ("Camera:", "카메라 문단"),
    ("Audio:", "음향 지시"),
]
BANNED = {
    "전환어(화면 전환 효과로 나옴)": r"\b(dissolve|cross-?fade|fade (in|out|to)|morphs?|morphing|transition)\b",
    "잔혹 어휘(생성 필터)": r"\b(blood|bloody|corpses?|dead bod(y|ies)|drown(s|ed|ing)?|massacre|slaughter|decapitat\w*|dismember\w*|gore|gory|bleeding)\b",
    "현대 사물": r"\b(cars?|trucks?|phones?|smartphones?|airplanes?|helicopters?|asphalt|neon|plastic|camera crew|drones? shadow)\b",
    "립싱크 암시": r"\b(lips part|speaks|speaking|says|shouts|whispers|screams|yells)\b",
    "음악 요구": r"\b(soundtrack plays|orchestral|epic music|score swells)\b",
}


def lint(cid, t):
    errs = []
    if len(t) > 3500: errs.append(f"{len(t)}자: 3,500자 초과")
    for key, label in REQUIRED:
        if key not in t: errs.append(f"필수 없음: {label} ('{key}')")
    for label, pat in BANNED.items():
        m = re.search(pat, t, re.I)
        if m: errs.append(f"금지어 [{label}]: '{m.group(0)}'")
    if re.search(r"[가-힣]", t): errs.append("한글이 들어 있음(프롬프트는 영어)")
    m = re.search(r"Lens-hit events in order:(.*)$", t, re.S)
    if m:
        n = len([x for x in m.group(1).strip().rstrip(".").split(",") if x.strip()])
        if not 2 <= n <= 6: errs.append(f"렌즈 히트 {n}개(2~6개)")
    if not re.search(r"OFF-CENTER|off-center|from behind|in profile|three-quarter|silhouette", t):
        errs.append("인물 비중앙·뒷모습·옆모습 지시가 없음(정면 중앙 인물이 나올 수 있음)")
    if not re.search(r"BEHIND|backlit|rim of light|rim light", t):
        errs.append("역광 지시가 없음(조명 문단에 광원을 인물 뒤에 둘 것)")
    return errs


def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    txt = Path(sys.argv[1]).read_text(encoding="utf-8")
    blocks = [b.strip() for b in re.split(r"\n\s*\n(?=\[C\d+\])", txt) if b.strip()]
    bad = 0
    for b in blocks:
        m = re.match(r"\[(C\d+)\]\s*(.*)", b, re.S)
        if not m: print("블록 머리말 [C001] 형식이 아님:", b[:40]); bad += 1; continue
        errs = lint(m.group(1), m.group(2))
        if errs:
            bad += 1; print(f"[{m.group(1)}] 문제 {len(errs)}건"); [print("   -", e) for e in errs]
    print(f"\n검사 {len(blocks)}블록, 문제 있는 블록 {bad}개")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
