#!/usr/bin/env python3
"""List the media in a folder with length and size, for step 0 of the plan (the clip list).

Usage:
    python media_inventory.py WORKDIR            # prints a Markdown table
    python media_inventory.py WORKDIR --starter  # also writes WORKDIR/edit.json with every clip in order
                                                 # (never overwrites an existing edit.json)
Needs ffprobe (comes with ffmpeg).
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_edit  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", default=".")
    ap.add_argument("--starter", action="store_true", help="write a starter edit.json")
    ap.add_argument("--format", default="9:16", help="format for the starter: 16:9, 9:16, 1:1, 4:5")
    args = ap.parse_args(argv)

    if not check_edit.ffprobe_bin():
        sys.exit("ffprobe not found: install ffmpeg first.")
    rows = []
    for dp, dirs, files in os.walk(args.folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in ("out", "node_modules"))
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            kind = ("video" if ext in check_edit.VIDEO_EXT else "image" if ext in check_edit.IMAGE_EXT
                    else "audio" if ext in check_edit.AUDIO_EXT else None)
            if not kind:
                continue
            p = os.path.join(dp, f)
            info = check_edit.probe(p) or {}
            rel = os.path.relpath(p, args.folder).replace("\\", "/")
            rows.append((rel, kind, info.get("duration"), info.get("width"), info.get("height"), info.get("has_audio")))

    if not rows:
        print("No video, image or audio files found.")
        return 1
    print("| File | Kind | Length (s) | Size | Has audio |")
    print("|---|---|---|---|---|")
    total = 0.0
    for rel, kind, dur, w, h, aud in rows:
        d = f"{dur:.2f}" if dur and kind != "image" else "-"
        if kind == "video" and dur:
            total += dur
        size = f"{w}x{h}" if w and h else "-"
        print(f"| {rel} | {kind} | {d} | {size} | {'yes' if aud else 'no'} |")
    print(f"\n{len(rows)} files, {total:.1f}s of video in total.")
    print("Add one line per clip about what is in it (the agent cannot see inside the files without looking at frames).")

    if args.starter:
        dst = os.path.join(args.folder, "edit.json")
        if os.path.exists(dst):
            print(f"\n{dst} already exists, not overwritten.")
            return 0
        clips = [{"src": r[0], "in": 0, "out": round(r[2], 2)} if r[1] == "video" else {"src": r[0], "duration": 3}
                 for r in rows if r[1] in ("video", "image")]
        audio = [r[0] for r in rows if r[1] == "audio"]
        edit = {"format": args.format, "fps": 30, "clips": clips, "narration": [], "captions": [],
                "notes": "Starter file: every clip once, in name order. Audio found: " + (", ".join(audio) or "none")}
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(edit, f, ensure_ascii=False, indent=2)
        print(f"\nWrote starter {dst}. Edit it to follow the shot list before rendering.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
