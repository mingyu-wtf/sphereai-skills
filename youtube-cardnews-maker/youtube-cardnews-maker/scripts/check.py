# -*- coding: utf-8 -*-
"""Check cards.json against the rules before rendering. Prints problems; exit code 1 if any must be fixed.

Usage:  python check.py work/my-video
"""
import json
import re
import sys
from pathlib import Path

LIMITS = {"cover": (24, 36), "other": (20, 110)}


def plain(t):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", t or "").replace("\n", " ")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    work = Path(sys.argv[1])
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    meta = json.loads((work / "meta.json").read_text(encoding="utf-8")) if (work / "meta.json").exists() else {}
    dur = float(meta.get("duration") or 0)
    errors, warns = [], []

    cards = data.get("cards", [])
    roles = [c.get("role", "") for c in cards]
    if not roles or roles[0] != "cover":
        errors.append("first card must be role 'cover'")
    if not roles or roles[-1] != "closing":
        errors.append("last card must be role 'closing'")
    if not 3 <= len(cards) <= 12:
        warns.append(f"{len(cards)} cards (usual range 5-10)")
    for i, c in enumerate(cards, 1):
        tmax, bmax = LIMITS["cover"] if c.get("role") == "cover" else LIMITS["other"]
        t, b = plain(c.get("title")), plain(c.get("body"))
        if len(t) > tmax:
            errors.append(f"card {i} title {len(t)} chars > {tmax}: {t}")
        if len(b) > bmax:
            errors.append(f"card {i} body {len(b)} chars > {bmax}")
        if not t or not b:
            errors.append(f"card {i} has an empty title or body")
        if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t + b):
            warns.append(f"card {i} contains emoji (cards should not)")
    if not data.get("description"):
        errors.append("description (caption) is missing")
    vid = meta.get("video_id", "")
    if vid and vid not in data.get("first_comment", ""):
        warns.append("first_comment does not include the original video link")

    hls = data.get("highlights") or []
    if len(hls) < 2:
        errors.append(f"{len(hls)} highlight(s) - the default deliverable is 2 highlight videos")
    spans = []
    for i, h in enumerate(hls, 1):
        s0, s1 = float(h.get("start", 0)), float(h.get("end", 0))
        spans.append((s0, s1, i))
        if not 8 <= s1 - s0 <= 30:
            warns.append(f"highlight {i} is {s1 - s0:.1f}s (aim for 10-20s)")
        if dur and s1 > dur + 0.5:
            errors.append(f"highlight {i} ends after the video ({s1} > {dur})")
        subs = h.get("subs") or []
        if not subs:
            errors.append(f"highlight {i} has no subs - run prepare_subs.py")
        for k, s in enumerate(subs, 1):
            ko = (s.get("ko") or "").strip()
            if not ko:
                errors.append(f"highlight {i} sub {k} has no Korean text")
            elif len(ko) > 40:
                warns.append(f"highlight {i} sub {k} is {len(ko)} chars (34 or fewer reads best)")
            if float(s.get("end", 0)) <= float(s.get("start", 0)):
                errors.append(f"highlight {i} sub {k} ends before it starts")
            if float(s.get("start", 0)) < s0 - 0.5 or float(s.get("end", 0)) > s1 + 0.5:
                warns.append(f"highlight {i} sub {k} is outside the clip span")
    spans.sort()
    for (a0, a1, i), (b0, b1, j) in zip(spans, spans[1:]):
        if b0 < a1:
            errors.append(f"highlights {i} and {j} overlap")

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("FIX  ", e)
    print(f"\n{len(errors)} to fix, {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
