# -*- coding: utf-8 -*-
"""Step 5 helper: fill each highlight's "subs" from transcript.json so you only write the Korean.

Usage:
  python prepare_subs.py work/my-video            # fills highlights that have no subs yet
  python prepare_subs.py work/my-video --force    # rebuild subs for every highlight

For each highlight {start, end} in cards.json it copies the caption lines inside that span with
their exact timing. Long lines are split in two (timed by length). For Korean videos "ko" is
pre-filled with the spoken line; for foreign videos "ko" is left empty and "orig" holds the
original - translate each "ko", then run check.py.
"""
import argparse
import json
import sys
from pathlib import Path

SPLIT_AT = 70  # characters (original language) above which a line is split in two


def split_line(seg):
    text = seg["text"]
    if len(text) <= SPLIT_AT:
        return [seg]
    mid = len(text) // 2
    cut = text.rfind(" ", 0, mid + 10)
    cut = cut if cut > 10 else mid
    a, b = text[:cut].strip(), text[cut:].strip()
    t = seg["start"] + (seg["end"] - seg["start"]) * len(a) / max(1, len(text))
    return [{"start": seg["start"], "end": round(t, 2), "text": a}, {"start": round(t, 2), "end": seg["end"], "text": b}]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    work = Path(a.work)
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    meta = json.loads((work / "meta.json").read_text(encoding="utf-8"))
    segs = json.loads((work / "transcript.json").read_text(encoding="utf-8"))
    korean = meta.get("language") == "ko"
    hls = data.get("highlights") or []
    if not hls:
        sys.exit('Add "highlights": [{"start": .., "end": ..}, ...] to cards.json first')
    for i, h in enumerate(hls, 1):
        if h.get("subs") and not a.force:
            print(f"highlight {i}: already has {len(h['subs'])} subs (use --force to rebuild)")
            continue
        s0, s1 = float(h["start"]), float(h["end"])
        inside = [s for s in segs if s["end"] > s0 + 0.1 and s["start"] < s1 - 0.1]
        subs = []
        for seg in inside:
            for part in split_line(seg):
                subs.append({"start": round(max(part["start"], s0), 2), "end": round(min(part["end"], s1), 2),
                             "ko": part["text"] if korean else "", "orig": part["text"]})
        h["subs"] = subs
        print(f"\nhighlight {i} ({s0:.1f}-{s1:.1f}s): {len(subs)} lines" + ("" if korean else " - translate each into \"ko\""))
        for k, s in enumerate(subs, 1):
            print(f"  {k:2d}. [{s['start']:.1f}-{s['end']:.1f}] {s['orig']}")
    (work / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
