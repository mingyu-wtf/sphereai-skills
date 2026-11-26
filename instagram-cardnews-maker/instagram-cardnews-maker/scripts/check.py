# -*- coding: utf-8 -*-
"""Check cards.json against the Instagram card-news rules before rendering.
Prints FIX (must fix) and NOTE (worth a look) lines; exit code 1 if anything must be fixed.

Usage:  python check.py work/my-topic
"""
import json
import re
import sys
from pathlib import Path

LIMITS = {"cover": (26, 40), "text": (22, 120), "list": (22, 100), "stat": (22, 80),
          "compare": (22, 0), "checklist": (22, 0), "quote": (0, 90), "closing": (22, 70),
          "product": (30, 0), "table": (14, 0)}
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
HYPE = re.compile(r"무조건|100\s*%|완벽|최고의|기적|보장|절대 실패|무한|역대급")


def plain(t):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(t or "")).replace("\n", " ").strip()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    work = Path(sys.argv[1])
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    fix, note = [], []
    cards = data.get("cards", [])
    types = [c.get("type", "") for c in cards]

    if not types or types[0] != "cover":
        fix.append("first card must be type 'cover'")
    if not types or types[-1] != "closing":
        fix.append("last card must be type 'closing' (save/share/follow + a question)")
    if not 5 <= len(cards) <= 10:
        note.append(f"{len(cards)} cards - 5 to 10 works best on Instagram (max 20)")
    if len(cards) > 20:
        fix.append("Instagram allows at most 20 images per post")

    for i, c in enumerate(cards, 1):
        t = c.get("type", "")
        if t not in LIMITS:
            fix.append(f"card {i}: unknown type '{t}'")
            continue
        tmax, bmax = LIMITS[t]
        title = plain(c.get("title"))
        body = plain(c.get("quote") if t == "quote" else (c.get("sub") if t == "cover" else c.get("body")))
        if tmax and len(title) > tmax:
            fix.append(f"card {i} ({t}) title {len(title)} chars > {tmax}: {title}")
        if bmax and len(body) > bmax:
            fix.append(f"card {i} ({t}) text {len(body)} chars > {bmax}")
        if t not in ("quote",) and not title:
            fix.append(f"card {i} ({t}) has no title")
        if t == "list" and not str(c.get("num", "")).isdigit():
            note.append(f"card {i}: list card without a number (num)")
        if t == "stat" and not c.get("value"):
            fix.append(f"card {i}: stat card needs a value, e.g. \"73%\"")
        if t == "compare":
            for side in ("left", "right"):
                items = c.get(side, {}).get("items", [])
                if not items:
                    fix.append(f"card {i}: compare needs {side}.items")
                if len(items) > 4:
                    fix.append(f"card {i}: compare {side} has {len(items)} items > 4")
                if any(len(plain(x)) > 18 for x in items):
                    fix.append(f"card {i}: compare {side} item longer than 18 chars")
        if t == "product":
            if not c.get("price") and not c.get("reviews"):
                note.append(f"card {i}: product without price or review count")
            if len(c.get("good", [])) + len(c.get("bad", [])) > 3:
                fix.append(f"card {i}: product has more than 3 check lines")
            if any(len(plain(x)) > 20 for x in c.get("good", []) + c.get("bad", [])):
                fix.append(f"card {i}: product check line longer than 20 chars")
        if t == "table":
            if not 2 <= len(c.get("rows", [])) <= 5:
                fix.append(f"card {i}: table needs 2-5 rows")
            if any(len(r) != len(c.get("columns", [])) for r in c.get("rows", [])):
                fix.append(f"card {i}: every table row needs one value per column")
        if t == "checklist":
            items = c.get("items", [])
            if not 2 <= len(items) <= 6:
                fix.append(f"card {i}: checklist needs 2-6 items (has {len(items)})")
            if any(len(plain(x)) > 26 for x in items):
                fix.append(f"card {i}: checklist item longer than 26 chars")
        blob = " ".join(plain(v) for v in [c.get("title"), c.get("body"), c.get("sub"), c.get("quote"), *c.get("items", [])])
        if EMOJI.search(blob):
            note.append(f"card {i}: emoji on a card (cards read cleaner without)")
        if HYPE.search(blob):
            note.append(f"card {i}: exaggerated wording ({HYPE.search(blob).group(0)}) - keep claims you can back up")
        if title and title.count("**") == 0 and "**" not in str(c.get("title")) and t in ("cover",):
            note.append("cover: mark one key word with **...** so it stands out")
        if c.get("image") and not (work / c["image"]).exists():
            fix.append(f"card {i}: image not found: {c['image']}")
        if (data.get("style") or "cream") != "cream" and (data.get("image_mode") or "full") == "full" and not c.get("image"):
            note.append(f"card {i}: no background image (image) - every card gets one in full mode")
        if not c.get("alt"):
            note.append(f"card {i}: no alt text (alt) - add one line describing the card")

    # photo shape vs. the slot it goes into (cream): a very different shape is shown whole with blurred sides instead of filling the slot
    if (data.get("style") or "cream") == "cream":
        import math
        from render_cards import image_size
        for i, c in enumerate(cards, 1):
            sz = image_size(work, c.get("image")) if c.get("image") else None
            if not sz:
                continue
            t = c.get("type")
            if t != "product":
                continue
            bw, bh = 936, 600 if c.get("quotes") else 690
            if abs(math.log((sz[0] / sz[1]) / (bw / bh))) >= 0.16 and c.get("fit") != "cover":
                note.append(f"card {i}: photo is {sz[0]}x{sz[1]} but the slot is about {bw}x{bh} - it will be shown whole with blurred sides. "
                            f"For a full slot, make/crop the photo near {bw}:{bh} (product photos: 4:3 landscape, product whole with margin)")
    imgs = [c.get("image") for c in cards if c.get("image")]
    if len(imgs) != len(set(imgs)):
        note.append("the same image is used on more than one card - use a different one per card")
    if data.get("design_css") and not (work / data["design_css"]).exists():
        fix.append(f"design_css not found: {data['design_css']}")

    cap = (data.get("caption") or "").strip()
    if not cap:
        fix.append("caption is missing")
    else:
        first = cap.splitlines()[0]
        if len(first) > 60:
            note.append(f"caption first line is {len(first)} chars - the hook should fit before '...더 보기' (about 40-60)")
        if len(cap) > 2200:
            fix.append(f"caption {len(cap)} chars > 2200 (Instagram limit)")
        if "?" not in cap:
            note.append("caption has no question - end with one easy question to invite comments")
    tags = data.get("hashtags", [])
    if not 3 <= len(tags) <= 5:
        note.append(f"{len(tags)} hashtags - 3 to 5 relevant tags is the current recommendation")
    if len(tags) > 30:
        fix.append("more than 30 hashtags is rejected by Instagram")
    if data.get("needs_sources", True) and not data.get("sources"):
        note.append("no sources - add where numbers/facts came from (or set needs_sources false for opinion posts)")

    for line in fix:
        print("FIX ", line)
    for line in note:
        print("NOTE", line)
    print(f"{len(fix)} to fix, {len(note)} notes")
    sys.exit(1 if fix else 0)


if __name__ == "__main__":
    main()
