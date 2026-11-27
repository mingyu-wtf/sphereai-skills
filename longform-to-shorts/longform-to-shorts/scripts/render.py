# -*- coding: utf-8 -*-
"""Step 3: cut the picked moments into vertical 1080x1920 Shorts with word-by-word captions.

Usage:
  python render.py work/<name> [--only 1,3] [--no-tighten] [--crop face|center|fit] [--font path/to/font.ttf] [--accent "#FFD60A"]

Reads : work/<name>/clips.json (written by the agent), video.mp4, transcript.json
Writes: work/<name>/clips/clip_01.mp4 ... + clip_01.srt, clips/_preview.png, clips/posts.txt
What it does per clip:
  1. cuts the moment frame-accurately,
  2. "tighten": removes pauses longer than ~0.4 s between words (jump-cut feel, keeps every word),
  3. reframes to 9:16 - `face` follows the speaker (OpenCV face detection), `center`, or `fit`
     (whole frame on a blurred background - use for screen recordings, slides, wide shots),
  4. burns big word-by-word captions (current word highlighted) and an optional title bar on top.
Needs: ffmpeg (with libass), pip install opencv-python pillow. No API key.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 1080, 1920
FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
             Path("/usr/share/fonts/truetype/noto"), Path("/usr/share/fonts/opentype/noto"), Path.home() / ".fonts"]
FONT_NAMES = ["Pretendard-Bold.ttf", "Pretendard-ExtraBold.ttf", "NotoSansKR-Bold.ttf", "NotoSansCJK-Bold.ttc", "NotoSansJP-Bold.ttf",
              "malgunbd.ttf", "YuGothB.ttc", "arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
CJK = ("ko", "ja", "zh")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-1200:]}")
    return r.stdout


def find_font(user):
    cands = ([Path(user)] if user else []) + [d / n for d in FONT_DIRS for n in FONT_NAMES]
    for p in cands:
        if p.exists():
            try:
                from PIL import ImageFont
                fam = ImageFont.truetype(str(p), 40).getname()[0]
            except Exception:  # noqa: BLE001
                fam = p.stem
            return p, fam
    sys.exit("No usable font found - pass --font path/to/BoldFont.ttf (one that covers your language).")


def ass_color(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def esc(t):
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def keep_intervals(words, start, end, tighten, max_gap=0.40, pad=0.06):
    """Spans (relative to `start`) to keep. With tighten, pauses longer than max_gap between words are removed."""
    if not tighten or not words:
        return [(0.0, end - start)]
    spans = []
    for w in words:
        a, b = max(start, w["start"] - pad), min(end, w["end"] + pad)
        if spans and a - spans[-1][1] <= max_gap:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    if spans:
        spans[0][0] = start if spans[0][0] - start < 0.25 else spans[0][0]
        spans[-1][1] = min(end, spans[-1][1] + 0.12)
    return [(round(a - start, 3), round(b - start, 3)) for a, b in spans if b - a > 0.05]


def remap(t, spans):
    """Time in the cut source (relative) -> time in the tightened clip."""
    acc = 0.0
    for a, b in spans:
        if t < a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc


YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"


def _detector(cv2, w, h):
    """Returns detect(frame)->list of (x, y, w, h). Uses Haar (OpenCV 4) or YuNet (OpenCV 4.8+/5, model fetched once)."""
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data"):
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        return lambda g: [tuple(f) for f in casc.detectMultiScale(cv2.cvtColor(g, cv2.COLOR_BGR2GRAY), 1.15, 5, minSize=(max(24, h // 20),) * 2)]
    if hasattr(cv2, "FaceDetectorYN"):
        model = Path.home() / ".cache" / "longform-to-shorts" / "face_detection_yunet_2023mar.onnx"
        if not model.exists():
            try:
                import urllib.request
                model.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(YUNET_URL, model)
            except Exception as e:  # noqa: BLE001
                print(f"[info] could not fetch the face model ({e}) - using centre crop", file=sys.stderr)
                return None
        det = cv2.FaceDetectorYN.create(str(model), "", (w, h), 0.7)

        def run_(g):
            det.setInputSize((g.shape[1], g.shape[0]))
            _, faces = det.detect(g)
            return [tuple(int(v) for v in f[:4]) for f in (faces if faces is not None else [])]
        return run_
    return None


def face_x(video, start, end, src_w, src_h):
    """Median horizontal centre of the largest face across the clip (0..1), or None when no face is found."""
    try:
        import cv2
    except ImportError:
        print("[info] opencv is not installed - using centre crop (pip install opencv-python)", file=sys.stderr)
        return None
    sw, sh = src_w // 2, src_h // 2
    detect = _detector(cv2, sw, sh)
    if detect is None:
        return None
    cap = cv2.VideoCapture(str(video))
    xs = []
    n = max(6, int((end - start) / 1.0))
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_MSEC, (start + (end - start) * (i + 0.5) / n) * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        faces = [f for f in detect(cv2.resize(fr, (sw, sh))) if f[2] >= sh // 20]
        if faces:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            xs.append((x + w / 2) / sw)
    cap.release()
    if len(xs) < max(2, n // 4):
        return None
    xs.sort()
    return xs[len(xs) // 2]


def line_groups(words, lang, max_chars):
    """Split words into short caption lines (1 line on screen at a time)."""
    lines, cur, cur_len = [], [], 0
    for w in words:
        t = w["word"].strip()
        if not t:
            continue
        add = len(t) + (0 if lang in CJK and not w["word"].startswith(" ") else 1)
        end_punct = t[-1] in ".?!,。？！、" if t else False
        if cur and (cur_len + add > max_chars):
            lines.append(cur)
            cur, cur_len = [], 0
        cur.append(w)
        cur_len += add
        if end_punct and cur_len >= max_chars * 0.5:
            lines.append(cur)
            cur, cur_len = [], 0
    if cur:
        lines.append(cur)
    return lines


def build_ass(path, words, spans, clip, style, fam, lang, total):
    acc = ass_color(style.get("accent", "#FFD60A"))
    size = int(style.get("caption_size", 100))
    y = int(H * float(style.get("caption_y", 0.70)))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{fam},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,9,4,5,60,60,0,1
Style: Title,{fam},{int(style.get("title_size", 78))},&H00000000,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,22,0,8,110,110,{int(style.get("title_y", 200))},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def ts(t):
        t = max(0.0, t)
        h, m = int(t // 3600), int(t % 3600 // 60)
        return f"{h}:{m:02d}:{t % 60:05.2f}"

    ev = []
    title = (clip.get("title_on_screen") or clip.get("title") or "").strip()
    if title and style.get("title_bar", True):
        ev.append(f"Dialogue: 1,{ts(0)},{ts(total)},Title,,0,0,0,,{esc(title)}")
    if style.get("captions", True):
        mw = [dict(w, s=remap(w["start"] - clip["start"], spans), e=remap(w["end"] - clip["start"], spans)) for w in words]
        max_chars = int(style.get("max_chars", 12 if lang in CJK else 22))
        for ln in line_groups(mw, lang, max_chars):
            l_start, l_end = ln[0]["s"], max(ln[-1]["e"], ln[0]["s"] + 0.3)
            for i, w in enumerate(ln):
                a = w["s"] if i else l_start
                b = ln[i + 1]["s"] if i + 1 < len(ln) else l_end
                if b - a < 0.02:
                    continue
                parts = []
                for j, x in enumerate(ln):
                    t = esc(x["word"].strip())
                    sep = "" if (lang in CJK and not x["word"].startswith(" ")) or j == 0 else " "
                    parts.append(sep + (f"{{\\c{acc}}}{t}{{\\c&H00FFFFFF&}}" if j == i else t))
                ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos({W // 2},{y})}}" + "".join(parts))
    Path(path).write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def write_srt(path, words, spans, clip):
    out, k = [], 1
    mw = [(remap(w["start"] - clip["start"], spans), remap(w["end"] - clip["start"], spans), w["word"].strip()) for w in words]
    chunk = []
    for s, e, t in mw:
        chunk.append((s, e, t))
        if len(chunk) >= 6 or t[-1:] in ".?!。？！":
            out.append((chunk[0][0], chunk[-1][1], " ".join(x[2] for x in chunk)))
            chunk = []
    if chunk:
        out.append((chunk[0][0], chunk[-1][1], " ".join(x[2] for x in chunk)))

    def f(t):
        return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(t * 1000 % 1000):03d}"
    Path(path).write_text("\n".join(f"{i}\n{f(a)} --> {f(b)}\n{t}\n" for i, (a, b, t) in enumerate(out, 1)), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--only", default="", help="comma-separated clip ids to render")
    ap.add_argument("--no-tighten", action="store_true", help="keep natural pauses")
    ap.add_argument("--crop", choices=["face", "center", "fit"], default="", help="override every clip's crop mode")
    ap.add_argument("--font", default="")
    ap.add_argument("--accent", default="")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg is not on PATH")
    work = Path(a.work)
    data = json.loads((work / "clips.json").read_text(encoding="utf-8"))
    meta = json.loads((work / "meta.json").read_text(encoding="utf-8"))
    tr = json.loads((work / "transcript.json").read_text(encoding="utf-8"))
    allw = [w for s in tr for w in s.get("words", [])]
    style = data.get("style", {})
    if a.accent:
        style["accent"] = a.accent
    lang = (data.get("language") or meta.get("language") or "en")[:2]
    fpath, fam = find_font(a.font or style.get("font", ""))
    fontsdir = Path(tempfile.mkdtemp(prefix="sc_fonts_"))
    shutil.copy(fpath, fontsdir / fpath.name)
    src_w, src_h = meta["width"], meta["height"]
    out = work / "clips"
    out.mkdir(exist_ok=True)
    only = {int(x) for x in a.only.split(",") if x.strip()}
    posts, made = [], []

    for n, clip in enumerate(data["clips"], 1):
        cid = int(clip.get("id", n))
        if only and cid not in only:
            continue
        s, e = float(clip["start"]), float(clip["end"])
        words = [w for w in allw if w["start"] >= s - 0.01 and w["end"] <= e + 0.01]
        tighten = not a.no_tighten and clip.get("tighten", style.get("tighten", True))
        spans = keep_intervals(words, s, e, tighten)
        total = sum(b - a_ for a_, b in spans)
        mode = a.crop or clip.get("crop") or style.get("crop", "face")
        tb = float(clip.get("trim_bottom", style.get("trim_bottom", 0)) or 0)  # share of the source height to cut off (burned-in subtitles)
        pre = f"crop=iw:ih*{1 - tb:.3f}:0:0," if tb > 0 else ""
        eff_h = int(src_h * (1 - tb)) // 2 * 2
        vertical = src_h >= src_w

        tmp = Path(tempfile.mkdtemp(prefix="sc_"))
        cut = tmp / "cut.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(work / "video.mp4"),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "aac", "-b:a", "192k", str(cut)])

        if vertical:
            vf = f"{pre}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        elif mode == "fit":
            vf = None
        else:
            cw = int(eff_h * 9 / 16) // 2 * 2
            fx = face_x(work / "video.mp4", s, e, src_w, src_h) if mode == "face" else None
            cx = (fx if fx is not None else 0.5) * src_w
            x0 = int(min(max(cx - cw / 2, 0), src_w - cw)) // 2 * 2
            vf = f"{pre}crop={cw}:{eff_h}:{x0}:0,scale={W}:{H}"
            clip["_crop_note"] = f"face x={fx:.2f}" if fx is not None else ("centre" if mode != "face" else "centre (no face found)")

        ass = tmp / "cap.ass"
        build_ass(ass, words, spans, clip, style, fam, lang, total)
        ass_arg = str(ass).replace("\\", "/").replace(":", "\\:")
        fd_arg = str(fontsdir).replace("\\", "/").replace(":", "\\:")
        parts = []
        for i, (a_, b) in enumerate(spans):
            parts.append(f"[0:v]trim=start={a_}:end={b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim=start={a_}:end={b},asetpts=PTS-STARTPTS[a{i}]")
        cat = "".join(f"[v{i}][a{i}]" for i in range(len(spans))) + f"concat=n={len(spans)}:v=1:a=1[vc][ac]"
        fz = float(clip.get("fit_zoom", style.get("fit_zoom", 1.35)))  # fit: zoom the picture so it fills more of the frame (sides trimmed)
        if vf is None:  # fit: blurred cover background + whole frame in the middle
            frame = (f"[vc]{pre}split[bg][fg];[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,eq=brightness=-0.08[bgb];"
                     f"[fg]scale={int(W * fz) // 2 * 2}:-2,crop={W}:ih[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2-{int(H * 0.04)}[vf]")
        else:
            frame = f"[vc]{vf}[vf]"
        fc = ";".join(parts) + ";" + cat + ";" + frame + f";[vf]subtitles=filename='{ass_arg}':fontsdir='{fd_arg}'[vo]"
        dst = out / f"clip_{cid:02d}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(cut), "-filter_complex", fc, "-map", "[vo]", "-map", "[ac]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(min(60, round(meta.get("fps") or 30))),
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst)])
        write_srt(out / f"clip_{cid:02d}.srt", words, spans, clip)
        shutil.rmtree(tmp, ignore_errors=True)
        made.append(dst)
        cut_s = (e - s) - total
        print(f"clip {cid:02d}: {total:5.1f}s  (pauses removed {cut_s:4.1f}s, {mode}{', ' + clip['_crop_note'] if clip.get('_crop_note') else ''}) -> {dst.name}")
        tags = " ".join("#" + t.lstrip("#") for t in clip.get("hashtags", []))
        posts.append(f"[clip_{cid:02d}]  {total:.0f}s  source {int(s // 60)}:{int(s % 60):02d}-{int(e // 60)}:{int(e % 60):02d}\n"
                     f"title: {clip.get('title', '')}\ncaption: {clip.get('caption', '')}\n{tags}\n")

    if made:
        sheet = []
        for p in made:
            fr = p.with_suffix(".jpg")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1.2", "-i", str(p), "-frames:v", "1", "-vf", "scale=270:480", str(fr)])
            sheet.append(fr)
        cols = min(5, len(sheet))
        rows = math.ceil(len(sheet) / cols)
        try:
            from PIL import Image
            canvas = Image.new("RGB", (270 * cols, 480 * rows), "black")
            for i, f in enumerate(sheet):
                canvas.paste(Image.open(f), ((i % cols) * 270, (i // cols) * 480))
            canvas.save(out / "_preview.png")
        except ImportError:
            pass
        for f in sheet:
            f.unlink(missing_ok=True)
        (out / "posts.txt").write_text("\n".join(posts), encoding="utf-8")
        print(f"preview  {out / '_preview.png'}")
        print(f"posts    {out / 'posts.txt'}")
    shutil.rmtree(fontsdir, ignore_errors=True)


if __name__ == "__main__":
    main()
