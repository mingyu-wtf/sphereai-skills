#!/usr/bin/env python3
"""Render an edit.json to mp4 with the Remotion template in ../remotion.

Usage:
    python render.py WORKDIR                 # WORKDIR/edit.json -> WORKDIR/out/edit.mp4
    python render.py WORKDIR --preview       # half resolution, faster, for a first look
    python render.py WORKDIR --out final.mp4 --crf 16

What it does:
  1. Runs the same checks as check_edit.py and stops on errors.
  2. Copies the template into an engine folder (default ~/.cache/edit-plan-sheet/engine-<version>)
     and runs `npm install` there the first time (a few minutes, ~300 MB, needs internet once).
  3. Copies every media file into the engine's public/ folder under plain ASCII names,
     so paths with spaces, '#' or non-Latin characters never break the bundler.
  4. Runs `npx remotion render`, then saves check frames with ffmpeg:
     out/frames/start.jpg, mid.jpg, end.jpg and one frame per caption (cap_01.jpg ...).

Needs: Python 3.8+, Node.js 18+ (npm/npx), ffmpeg + ffprobe on PATH. No API keys.
"""
import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_edit  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace", line_buffering=True)
    except Exception:
        pass

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL_DIR, "remotion")
TEMPLATE_FILES = ["package.json", "tsconfig.json", "remotion.config.ts"]

# Fonts tried in order when the first one lacks a character. Covers Windows, macOS and Linux.
FONT_STACK = {
    "ko": ["Pretendard", "Noto Sans KR", "Noto Sans CJK KR", "Apple SD Gothic Neo", "Malgun Gothic",
           "Noto Sans JP", "Noto Sans CJK JP", "Hiragino Sans", "Yu Gothic", "Meiryo"],
    "ja": ["Noto Sans JP", "Noto Sans CJK JP", "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo",
           "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic"],
    "en": ["Inter", "Segoe UI", "Helvetica Neue", "Arial", "Noto Sans", "Noto Sans KR", "Noto Sans JP",
           "Apple SD Gothic Neo", "Malgun Gothic", "Hiragino Sans", "Yu Gothic"],
}


def tool(name):
    exe = shutil.which(name) or shutil.which(name + ".cmd")
    if not exe:
        sys.exit(f"'{name}' not found. Install it and make sure it is on PATH (see SKILL.md, Setup).")
    return exe


def remotion_version():
    with open(os.path.join(TEMPLATE, "package.json"), encoding="utf-8") as f:
        return json.load(f)["dependencies"]["remotion"]


def engine_dir(arg):
    if arg:
        d = arg
    elif os.environ.get("EDIT_PLAN_ENGINE"):
        d = os.environ["EDIT_PLAN_ENGINE"]
    else:
        d = os.path.join(os.path.expanduser("~"), ".cache", "edit-plan-sheet", f"engine-{remotion_version()}")
    if "#" in d or not d.isascii():
        # The bundler mis-reads '#' and some non-ASCII paths. Fall back to the temp folder.
        alt = os.path.join(tempfile.gettempdir(), "edit-plan-sheet-engine")
        if "#" in alt or not alt.isascii():
            sys.exit(f"Engine path {d} contains '#' or non-ASCII characters. Pass --engine C:/edit-engine or similar.")
        print(f"Engine path has '#' or non-ASCII characters, using {alt} instead")
        d = alt
    return os.path.abspath(d)


def sync_template(eng, skip_install):
    os.makedirs(eng, exist_ok=True)
    pkg_changed = not os.path.exists(os.path.join(eng, "package.json")) or not filecmp.cmp(
        os.path.join(TEMPLATE, "package.json"), os.path.join(eng, "package.json"), shallow=False)
    for f in TEMPLATE_FILES:
        shutil.copy2(os.path.join(TEMPLATE, f), os.path.join(eng, f))
    shutil.rmtree(os.path.join(eng, "src"), ignore_errors=True)
    shutil.copytree(os.path.join(TEMPLATE, "src"), os.path.join(eng, "src"))
    has_modules = os.path.isdir(os.path.join(eng, "node_modules", "remotion"))
    if (pkg_changed or not has_modules) and not skip_install:
        print(f"Installing Remotion into {eng} (first run only, a few minutes)...")
        r = subprocess.run([tool("npm"), "install", "--no-audit", "--no-fund"], cwd=eng)
        if r.returncode != 0:
            sys.exit("npm install failed. Check your internet connection and Node.js version (18+), then retry.")


def stage_media(res, eng):
    """Copy media to public/job/ with ASCII names and return {abs path: public-relative path}."""
    job = os.path.join(eng, "public", "job")
    shutil.rmtree(job, ignore_errors=True)
    os.makedirs(job, exist_ok=True)
    mapping = {}
    paths = list(res["media"])
    for i, p in enumerate(sorted(paths), 1):
        name = f"m{i:03d}{os.path.splitext(p)[1].lower()}"
        dst = os.path.join(job, name)
        try:
            os.link(p, dst)  # hard link: instant, no extra disk space (same drive only)
        except OSError:
            shutil.copy2(p, dst)
        mapping[p] = f"job/{name}"
    return mapping


def build_props(res, mapping):
    st = res["style"]
    stack = FONT_STACK.get(st["lang"], FONT_STACK["en"])
    families = ([("EditUserFont")] if st["font_path"] else []) + ([st["font_family"]] if st["font_family"] else []) + stack
    css = ", ".join(f'"{f}"' for f in families) + ", sans-serif"
    props = {
        "width": res["width"], "height": res["height"], "fps": res["fps"],
        "durationInFrames": res["durationInFrames"], "background": res["background"],
        "style": {
            "fontFamily": css, "fontUrl": mapping.get(st["font_path"]) if st["font_path"] else None,
            "fontWeight": st["font_weight"], "textColor": st["text_color"], "accentColor": st["accent_color"],
            "outlineColor": st["outline_color"], "boxColor": st["box_color"], "captionScale": st["caption_scale"],
            "lang": st["lang"],
        },
        "clips": [{
            "kind": c["kind"], "src": mapping.get(c["path"]) if c["path"] else None, "color": c["color"],
            "from": c["from"], "dur": c["dur"], "trimBefore": c["trimBefore"], "speed": c["speed"], "fit": c["fit"],
            "zoom": c["zoom"], "zoomAmount": c["zoomAmount"], "volume": c["volume"], "fadeIn": c["fadeIn"],
            "audioFadeIn": c["audioFadeIn"], "audioFadeOut": c["audioFadeOut"], "crop": c["crop"],
            "srcWidth": c["srcWidth"], "srcHeight": c["srcHeight"],
        } for c in res["clips"]],
        "audio": [{
            "src": mapping[a["path"]], "from": a["from"], "dur": a["dur"], "trimBefore": a["trimBefore"],
            "volume": a["volume"], "loop": a["loop"], "fadeIn": a["fadeIn"], "fadeOut": a["fadeOut"],
            "duck": a["duck"], "duckFactor": a["duckFactor"], "duckRamp": a["duckRamp"],
        } for a in res["audio"]],
        "captions": [{k: c[k] for k in ("text", "from", "dur", "style", "position", "highlight")} for c in res["captions"]],
        "titles": res["titles"],
    }
    return props


def grab(ffmpeg, video, t, dst):
    subprocess.run([ffmpeg, "-y", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", video, "-frames:v", "1",
                    "-q:v", "3", dst], check=False)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default=".", help="work folder with edit.json, or the edit.json path")
    ap.add_argument("--out", help="output mp4 (default WORKDIR/out/edit.mp4, or edit_preview.mp4 with --preview)")
    ap.add_argument("--preview", action="store_true", help="render at half size for a quick look")
    ap.add_argument("--crf", type=int, default=18, help="h264 quality, lower = better and bigger (default 18)")
    ap.add_argument("--concurrency", help="frames rendered in parallel (Remotion default if omitted)")
    ap.add_argument("--engine", help="engine folder (default ~/.cache/edit-plan-sheet/engine-<version>)")
    ap.add_argument("--skip-install", action="store_true", help="never run npm install")
    ap.add_argument("--no-caption-frames", action="store_true", help="skip the one-frame-per-caption check images")
    ap.add_argument("--force", action="store_true", help="render even if the check finds errors")
    args = ap.parse_args(argv)

    t0 = time.time()
    try:
        edit, workdir = check_edit.load_edit(args.target)
    except (FileNotFoundError, json.JSONDecodeError) as ex:
        sys.exit(f"Cannot read edit.json: {ex}")
    res, rep = check_edit.resolve(edit, workdir)
    if res is None:
        sys.exit("\n".join(rep.errors))
    print(check_edit.summary(res, rep))
    if rep.errors and not args.force:
        sys.exit("\nFix the errors above (or pass --force) and run again.")

    ffmpeg = tool("ffmpeg")
    npx = tool("npx")
    eng = engine_dir(args.engine)
    sync_template(eng, args.skip_install)
    mapping = stage_media(res, eng)
    props = build_props(res, mapping)
    props_path = os.path.join(eng, "props.json")
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False)

    out = args.out or os.path.join("out", "edit_preview.mp4" if args.preview else "edit.mp4")
    out = out if os.path.isabs(out) else os.path.join(workdir, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp_out = os.path.join(eng, "out", "render.mp4")
    os.makedirs(os.path.dirname(tmp_out), exist_ok=True)
    cmd = [npx, "remotion", "render", "src/index.ts", "Edit", tmp_out, f"--props={props_path}",
           "--codec=h264", f"--crf={args.crf}", "--audio-codec=aac"]
    if args.preview:
        cmd.append("--scale=0.5")
    if args.concurrency:
        cmd.append(f"--concurrency={args.concurrency}")
    print("\nRendering... (the first render also downloads a headless Chrome, about 100 MB)")
    t1 = time.time()
    r = subprocess.run(cmd, cwd=eng)
    if r.returncode != 0:
        sys.exit("Render failed. See the Remotion error above and SKILL.md, Troubleshooting.")
    shutil.move(tmp_out, out)
    t2 = time.time()

    frames = os.path.join(os.path.dirname(out), "frames")
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames, exist_ok=True)
    info = check_edit.probe(out) or {}
    dur = info.get("duration") or res["durationInFrames"] / res["fps"]
    # Half a second in from each end, so fade-ins and fade-outs do not hide what is on screen.
    grab(ffmpeg, out, min(0.5, dur / 4), os.path.join(frames, "start.jpg"))
    grab(ffmpeg, out, dur / 2, os.path.join(frames, "mid.jpg"))
    grab(ffmpeg, out, max(0.0, dur - 0.5), os.path.join(frames, "end.jpg"))
    if not args.no_caption_frames:
        for i, c in enumerate(res["captions"], 1):
            # A little after the pop-in finishes, so the caption is at full size.
            t = (c["from"] + min(c["dur"] - 1, max(10, c["dur"] // 2))) / res["fps"]
            grab(ffmpeg, out, t, os.path.join(frames, f"cap_{i:02d}.jpg"))

    print(f"\nDone: {out}")
    print(f"  {info.get('width')}x{info.get('height')}, {dur:.2f}s, "
          f"{os.path.getsize(out) / 1e6:.1f} MB, render {t2 - t1:.0f}s (total {time.time() - t0:.0f}s)")
    print(f"  Check frames: {frames}")
    print("  Open the frames and look at them before you hand the video over.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
