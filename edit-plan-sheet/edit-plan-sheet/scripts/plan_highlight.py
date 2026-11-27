#!/usr/bin/env python3
"""Turn a highlight plan (the parts of the source you picked) into edit.json.

Usage:
    python plan_highlight.py WORKDIR                  # reads WORKDIR/highlight.json, writes WORKDIR/edit.json
    python plan_highlight.py WORKDIR --plan other.json --out edit.json
    python plan_highlight.py WORKDIR --dry-run        # only print the timeline and length

WORKDIR is the folder analyze.py filled (source video, transcript.json, meta.json).
The plan format is in references/highlight-plan.md. In short:

    {
      "format": "9:16", "target_length": 60,
      "crop": {"bottom": 0.17},          # optional: cut burned-in subtitles or a logo
      "title": {"text": "...", "duration": "all"},
      "segments": [
        {"start": 600.6, "end": 606.2, "reason": "punchline as hook", "hook": true},
        {"start": 65.9, "end": 75.5, "reason": "the promise"}
      ]
    }

What it does:
  - snaps each segment to speech boundaries (never starts or ends inside a word; prefers sentence edges)
  - puts "hook" segments first, the rest in the order you listed them
  - original sound at volume 1, short crossfades between segments, a short fade at the very end
  - captions from the transcript (or from your own "caption" text per segment), timed to the new timeline
  - title card, vertical/horizontal framing (9:16 uses a blurred fill behind horizontal footage)
  - prints the timeline and compares the length with target_length
"""
import argparse
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transcribe_captions as tc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

# Characters per caption line. Shorts captions are big (about 1/12 of the width per character),
# so Korean and Japanese lines stay short; captions may use two lines.
LINE_MAX = {"shorts": {"ko": 10, "ja": 10, "en": 22}, "standard": {"ko": 16, "ja": 13, "en": 42}}
VERTICAL = {"9:16", "4:5"}


def num(v, default=None):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*(\d+):(\d+(?:\.\d+)?)\s*", str(v))
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    return float(v)


def fmt_t(sec):
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m)}:{s:04.1f}"


def load_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


# ------------------------------------------------------------------ snapping
def snap(seg_start, seg_end, words, sentences, duration, notes):
    """Move the edges to pauses so no word is cut.

    An edge that already sits in a pause stays where it is (plus a little breathing room).
    An edge inside a word moves to the nearer edge of that word. Pick edges from transcript.txt
    (sentence starts and ends) and this only fixes small rounding.
    """
    s, e = seg_start, seg_end
    if words:
        inside = [w for w in words if w["s"] + 0.02 < s < w["e"] - 0.02]
        if inside:  # move to the nearer edge of that word
            w = inside[0]
            s = w["s"] if s - w["s"] <= w["e"] - s else w["e"]
        nxt_w = min([w["s"] for w in words if w["s"] >= s - 0.02], default=None)
        prev_end = max([w["e"] for w in words if w["e"] <= s + 0.02], default=0.0)
        if nxt_w is not None and nxt_w - s < 0.12:  # give the first word a little air before it
            s = max(prev_end + 0.02, nxt_w - 0.12) if prev_end < nxt_w else s
        inside = [w for w in words if w["s"] + 0.02 < e < w["e"] - 0.02]
        if inside:
            w = inside[-1]
            e = w["s"] if e - w["s"] < w["e"] - e else w["e"]
        last_e = max([w["e"] for w in words if w["e"] <= e + 0.02], default=None)
        next_start = min([w["s"] for w in words if w["s"] >= e - 0.02], default=duration or e + 1)
        if last_e is not None and e - last_e < 0.2:  # let the last word ring out
            e = min(next_start - 0.03, last_e + 0.2) if next_start > last_e else e
        # mid-sentence hints: no pause at the edge and not at a recognised sentence edge
        starts = [x["start"] for x in sentences]
        ends = [x["end"] for x in sentences]
        before = [w for w in words if w["e"] <= s + 0.02]
        if before and s - before[-1]["e"] < 0.1 and not any(abs(t - s) < 0.2 for t in starts)                 and not re.search(r"[.!?。！？]$", before[-1]["w"].strip()):
            notes.append(f"starts right after '{before[-1]['w'].strip()}' (mid-sentence?)")
        after = [w for w in words if w["s"] >= e - 0.02]
        if after and after[0]["s"] - e < 0.1 and not any(abs(t - e) < 0.25 for t in ends):
            notes.append(f"ends right before '{after[0]['w'].strip()}' (mid-sentence?)")
    s = max(0.0, s)
    e = min(duration, e) if duration else e
    return round(s, 2), round(e, 2)


# ------------------------------------------------------------------ captions
PUNCT_END = r"[.!?,\u3001\u3002\uff01\uff1f]$"
SENT_END = r"[.!?\u3002\uff01\uff1f]$"


def two_lines(words_text, max_chars):
    """Join words into one line, or two balanced lines broken at a space, if it is too long for one."""
    words_text = [w for w in words_text if w]
    text = " ".join(words_text)
    if len(text) <= max_chars or len(words_text) < 2:
        return text
    best, best_score = None, None
    for k in range(1, len(words_text)):
        a, b = " ".join(words_text[:k]), " ".join(words_text[k:])
        score = max(len(a), len(b))
        if len(words_text[k]) <= 1:  # a line should not start with a one-character word (often a particle)
            score += 3
        if re.search(PUNCT_END, words_text[k - 1]):  # breaking after a comma reads naturally
            score -= 2
        if best_score is None or score < best_score:
            best, best_score = a + "\n" + b, score
    return best


def split_words(ws, max_chars):
    """Split a run of words into caption pieces of at most two lines, cutting at the longest pauses."""
    text_len = len(" ".join(w["w"].strip() for w in ws))
    if text_len <= 2 * max_chars or len(ws) < 2:
        return [ws]
    n = -(-text_len // (2 * max_chars))  # pieces needed
    target = text_len / n
    best_k, best_score = 1, None
    pos = 0
    for k in range(1, len(ws)):
        pos += len(ws[k - 1]["w"].strip()) + 1
        gap = ws[k]["s"] - ws[k - 1]["e"]
        punct = 1.0 if re.search(PUNCT_END, ws[k - 1]["w"].strip()) else 0.0
        score = abs(pos - target) / max_chars - 2.0 * min(gap, 0.6) - punct
        if len(ws[k]["w"].strip()) <= 1:
            score += 0.5
        if best_score is None or score < best_score:
            best_k, best_score = k, score
    return split_words(ws[:best_k], max_chars) + split_words(ws[best_k:], max_chars)


def seg_captions(seg, words, sentences, max_chars):
    """Captions for one segment: one recognised phrase per caption (1-2 lines), timed by its words."""
    lo, hi = seg["start"] - 0.05, seg["end"] + 0.05
    if seg.get("caption"):
        inside = [w for w in words if lo <= (w["s"] + w["e"]) / 2 <= hi]
        if not inside:
            return []
        tuples = [(w["w"], max(seg["start"], w["s"]), min(seg["end"], w["e"])) for w in inside]
        caps = tc.captions_from_script(tuples, str(seg["caption"]), 2 * max_chars)
    else:
        caps = []
        for sent in sentences:
            ws = [w for w in sent.get("words", []) if lo <= (w["s"] + w["e"]) / 2 <= hi]
            for piece in split_words(ws, max_chars) if ws else []:
                caps.append({"text": " ".join(w["w"].strip() for w in piece),
                             "start": max(seg["start"], piece[0]["s"]), "end": min(seg["end"], piece[-1]["e"])})
    caps = [c for c in caps if c["text"].strip()]
    caps = merge_short(caps, max_chars)
    for c in caps:
        c["text"] = two_lines(re.sub(r"\s+", " ", c["text"]).strip().split(" "), max_chars)
        c["text"] = "\n".join(re.sub(r"[,\u3001]$", "", ln).strip() for ln in c["text"].split("\n"))
    return caps


def merge_short(caps, max_chars, min_dur=0.8, min_chars=4):
    """Join a piece that would flash by (under min_dur, or a stray word) with a neighbour.

    It joins the previous piece unless that one ends a sentence; the result may run a little long,
    which two_lines() then breaks over two lines.
    """
    i = 0
    while i < len(caps) and len(caps) > 1:
        c = caps[i]
        short = c["end"] - c["start"] < min_dur or len(c["text"].strip()) <= min_chars
        if not short:
            i += 1
            continue
        prev = caps[i - 1] if i > 0 else None
        nxt = caps[i + 1] if i + 1 < len(caps) else None
        tiny = c["end"] - c["start"] < 0.5 or len(c["text"].strip()) <= min_chars
        if prev is not None and not tiny and len(prev["text"]) + len(c["text"]) + 1 > 2 * max_chars:
            prev = None  # joining would make three lines; a 0.5-0.8 s caption is better
        if nxt is not None and not tiny and len(nxt["text"]) + len(c["text"]) + 1 > 2 * max_chars:
            nxt = None
        if prev is None and nxt is None:
            i += 1
            continue
        use_prev = prev is not None and not re.search(SENT_END, prev["text"].strip())
        if not use_prev and nxt is None:
            use_prev = prev is not None
        if use_prev:
            prev["text"] = prev["text"].strip() + " " + c["text"].strip()
            prev["end"] = c["end"]
            caps.pop(i)
        elif nxt is not None:
            nxt["text"] = c["text"].strip() + " " + nxt["text"].strip()
            nxt["start"] = c["start"]
            caps.pop(i)
        else:
            i += 1
    return caps


def place_captions(caps_by_clip, timeline, total, highlight_words, position):
    out = []
    for (clip_from, clip_end, seg_start, speed), caps, hl in zip(timeline, caps_by_clip, highlight_words):
        for c in caps:
            a = clip_from + (c["start"] - seg_start) / speed
            b = clip_from + (c["end"] - seg_start) / speed
            a, b = max(clip_from, a), min(clip_end, b)
            if b - a < 0.2:
                continue
            item = {"text": c["text"], "start": round(a, 2), "end": round(b, 2)}
            hits = [h for h in hl if h.lower() in c["text"].lower()]
            if hits:
                item["highlight"] = hits
            if position:
                item["position"] = position
            out.append(item)
    out.sort(key=lambda x: x["start"])
    # no overlaps, no flicker: close small gaps, keep each at least 0.6 s where room allows
    for i, c in enumerate(out):
        nxt = out[i + 1]["start"] if i + 1 < len(out) else total
        if nxt - c["end"] < 0.3:
            c["end"] = nxt
        c["end"] = round(min(max(c["end"], c["start"] + 0.6), nxt, total), 2)
    return [c for c in out if c["end"] - c["start"] >= 0.25]


# ------------------------------------------------------------------ main
def build(workdir, plan):
    meta = load_json(os.path.join(workdir, "meta.json"), {}) or {}
    tr = load_json(os.path.join(workdir, "transcript.json"))
    sentences = (tr or {}).get("segments", [])
    words = [w for s in sentences for w in s.get("words", [])]
    lang = plan.get("lang") or (tr or {}).get("language") or "en"
    lang = lang if lang in ("ko", "ja", "en") else "en"

    src = plan.get("source") or meta.get("source") or "source.mp4"
    if not os.path.isfile(src if os.path.isabs(src) else os.path.join(workdir, src)):
        sys.exit(f"Source video not found: {src}. Run analyze.py first or set 'source' in the plan.")
    duration = float(meta.get("duration") or 0)
    src_vertical = (meta.get("height") or 0) > (meta.get("width") or 1)

    fmt = plan.get("format", "9:16")
    vertical = fmt in VERTICAL
    cap_style = "shorts" if vertical else "standard"
    fit_default = plan.get("fit") or ("blur" if vertical and not src_vertical else "cover")
    trans = plan.get("transition", "crossfade")
    td = num(plan.get("transition_duration"), 0.3)
    volume = num(plan.get("volume"), 1.0 if meta.get("has_audio", True) else 0.0)  # silent source: nothing to play
    want_caps = plan.get("captions", "auto")
    max_chars = int(plan.get("caption_max_chars") or LINE_MAX[cap_style][lang])
    do_snap = plan.get("snap", True)

    segs = plan.get("segments") or []
    if not segs:
        sys.exit("The plan has no segments.")
    order = plan.get("order", "as_listed")
    indexed = list(enumerate(segs))
    if order == "source":
        indexed.sort(key=lambda x: num(x[1]["start"]))
    hooks = [x for x in indexed if x[1].get("hook")]
    rest = [x for x in indexed if not x[1].get("hook")]
    ordered = hooks + rest

    clips, timeline, caps_by_clip, hl_by_clip, rows, warnings = [], [], [], [], [], []
    cursor = 0.0
    used = []
    for k, (orig_i, sg) in enumerate(ordered):
        notes = []
        s0, e0 = num(sg["start"]), num(sg["end"])
        if e0 <= s0:
            sys.exit(f"segment {orig_i + 1}: end must be after start")
        s, e = snap(s0, e0, words, sentences, duration, notes) if (do_snap and words) else (s0, e0)
        speed = num(sg.get("speed"), 1.0)
        length = (e - s) / speed
        fade = 0.0
        clip = {"src": src, "in": s, "out": e, "fit": sg.get("fit", fit_default), "volume": num(sg.get("volume"), volume)}
        crop = sg.get("crop", plan.get("crop"))
        if crop:
            clip["crop"] = crop
        if speed != 1:
            clip["speed"] = speed
        if sg.get("zoom"):
            clip["zoom"] = sg["zoom"]
        if k > 0 and trans == "crossfade":
            fade = min(td, length / 2, (timeline[-1][1] - timeline[-1][0]) / 2) if timeline else 0
            clip["transition"] = "crossfade"
            clip["transition_duration"] = round(td, 3)
        clip["note"] = sg.get("reason", "")
        start_out = cursor - fade
        clips.append(clip)
        timeline.append((start_out, start_out + length, s, speed))
        cursor = start_out + length
        for a, b, j in used:
            if s < b - 0.5 and e > a + 0.5:
                warnings.append(f"segment {orig_i + 1} repeats source {fmt_t(max(a, s))}-{fmt_t(min(b, e))} (also in segment {j})")
        used.append((s, e, orig_i + 1))
        if length < 1.5:
            warnings.append(f"segment {orig_i + 1} is only {length:.1f}s on screen")
        if want_caps != "none" and words:
            caps_by_clip.append(seg_captions({**sg, "start": s, "end": e}, words, sentences, max_chars))
        else:
            caps_by_clip.append([])
        hl_by_clip.append([str(h) for h in (sg.get("highlight") or [])])
        rows.append((k + 1, orig_i + 1, s, e, start_out, start_out + length, sg.get("reason", ""), notes, sg.get("hook")))

    end_fade = num(plan.get("end_fade"), 0.3)
    total = cursor
    if end_fade and end_fade > 0:
        # A black shot twice the fade long: the picture fades out, then black holds for the same time.
        clips.append({"color": plan.get("background", "#000000"), "duration": round(2 * end_fade, 2),
                      "transition": "crossfade", "transition_duration": round(end_fade, 2), "note": "fade out at the end"})
        last_len = timeline[-1][1] - timeline[-1][0]
        fade = min(end_fade, last_len / 2)
        total = cursor - fade + 2 * end_fade

    edit = {
        "format": fmt, "fps": int(plan.get("fps") or round(meta.get("fps") or 30)),
        "style": {"captions": cap_style, "lang": lang, **(plan.get("style") or {})},
        "clips": clips,
        "notes": "Made by plan_highlight.py from highlight.json. Edit freely, then run check_edit.py.",
    }
    if edit["fps"] not in (24, 25, 30, 50, 60):
        edit["fps"] = 30
    if plan.get("target_length"):
        edit["target_length"] = num(plan["target_length"])

    if want_caps != "none" and words:
        edit["captions"] = place_captions(caps_by_clip, timeline, timeline[-1][1], hl_by_clip, plan.get("caption_position"))
    elif want_caps != "none" and not words:
        warnings.append("no transcript (no speech, or analyze.py ran with --no-transcript): no captions made")

    titles = []
    for key in ("title", "end_title"):
        t = plan.get(key)
        if not t:
            continue
        t = {"text": t} if isinstance(t, str) else dict(t)
        dur = t.pop("duration", 2.5)
        if key == "title":
            a = num(t.pop("start", 0.0))
            b = total if dur == "all" else min(total, a + num(dur))
        else:
            b = total
            a = 0.0 if dur == "all" else max(0.0, total - num(dur))
        t.setdefault("position", "top" if vertical else "center")
        titles.append({"kind": t.pop("kind", "title"), "start": round(a, 2), "end": round(b, 2), **t})
    if titles:
        edit["titles"] = titles
    if plan.get("music"):
        edit["music"] = plan["music"]
    if plan.get("sfx"):
        edit["sfx"] = plan["sfx"]
    return edit, rows, warnings, total


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--plan", help="plan file (default WORKDIR/highlight.json)")
    ap.add_argument("--out", help="edit.json to write (default WORKDIR/edit.json)")
    ap.add_argument("--dry-run", action="store_true", help="print the timeline, write nothing")
    args = ap.parse_args(argv)

    workdir = os.path.abspath(args.workdir)
    plan_path = args.plan or os.path.join(workdir, "highlight.json")
    plan = load_json(plan_path)
    if plan is None:
        sys.exit(f"Plan not found: {plan_path}")
    edit, rows, warnings, total = build(workdir, plan)

    print(f"{'#':>2} {'seg':>3}  {'source':<15} {'in the video':<15} {'len':>5}  reason")
    for n, orig, s, e, a, b, reason, notes, hook in rows:
        print(f"{n:>2} {orig:>3}  {fmt_t(s) + '-' + fmt_t(e):<15} {fmt_t(a) + '-' + fmt_t(b):<15} {b - a:>5.1f}  "
              f"{'[HOOK] ' if hook else ''}{reason}")
        for x in notes:
            print(f"{'':>8}note: {x}")
    tgt = num(plan.get("target_length"))
    line = f"\nTotal {total:.1f}s ({fmt_t(total)}), {len(rows)} segments, {len(edit.get('captions', []))} captions"
    if tgt:
        diff = total - tgt
        line += f"; target {tgt:.0f}s -> {'+' if diff >= 0 else ''}{diff:.1f}s"
        if abs(diff) / tgt > 0.1:
            line += "  (more than 10% off: add, drop or trim segments)"
    print(line)
    for w in warnings:
        print(f"WARNING {w}")
    if args.dry_run:
        return 0
    out = args.out or os.path.join(workdir, "edit.json")
    out = out if os.path.isabs(out) else os.path.join(workdir, out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(edit, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out}. Next: python scripts/check_edit.py {workdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
