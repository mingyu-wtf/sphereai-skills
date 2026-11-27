#!/usr/bin/env python3
"""Check an edit.json and resolve it into an exact timeline.

Usage:
    python check_edit.py WORKDIR            # reads WORKDIR/edit.json
    python check_edit.py path/to/edit.json  # same thing
    python check_edit.py WORKDIR --json resolved.json   # also write the resolved timeline

Checks: files exist and can be read, clip in/out fits the source, no empty picture,
caption overlap / length / reading speed, items past the end, total length.
Exit code 0 = no errors (warnings allowed), 1 = errors, 2 = cannot read edit.json.

Needs Python 3.8+ and ffprobe (comes with ffmpeg). Standard library only.
The schema is documented in references/edit-json.md.
"""
import json
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2"}

TOP_KEYS = {"format", "width", "height", "fps", "background", "duration", "tail", "target_length", "style",
            "clips", "narration", "music", "sfx", "captions", "titles", "notes", "title"}
STYLE_KEYS = {"captions", "font_family", "font_file", "font_weight", "text_color", "accent_color", "outline_color",
              "box_color", "caption_scale", "lang"}
CLIP_KEYS = {"src", "color", "in", "out", "duration", "speed", "fit", "zoom", "zoom_amount", "volume", "transition",
             "transition_duration", "crop", "audio_fade", "note"}
CROP_SIDES = ("top", "bottom", "left", "right")
NARR_KEYS = {"src", "start", "in", "out", "volume", "gap", "note"}
MUSIC_KEYS = {"src", "start", "in", "volume", "duck_db", "loop", "fade_in", "fade_out", "duration", "note"}
SFX_KEYS = {"src", "at", "volume", "note"}
CAP_KEYS = {"text", "start", "end", "position", "highlight", "style", "note"}
TITLE_KEYS = {"text", "sub", "start", "end", "kind", "position", "dim", "note"}
POSITIONS = {"top", "center", "lower", "bottom"}

# Rough reading-speed ceilings (characters per second, spaces and punctuation not counted).
# Taken from common subtitle style guides; Shorts captions should sit well under them.
CPS = {"ko": 14.0, "ja": 9.0, "en": 20.0}
# Characters per line before the renderer has to wrap.
LINE_MAX = {"shorts": {"ko": 12, "ja": 11, "en": 24}, "standard": {"ko": 16, "ja": 13, "en": 42}}

_probe_cache = {}


def ffprobe_bin():
    return shutil.which("ffprobe")


def probe(path):
    """Return {'duration': float|None, 'width': int|None, 'height': int|None, 'has_audio': bool} or None."""
    if path in _probe_cache:
        return _probe_cache[path]
    exe = ffprobe_bin()
    info = None
    if exe:
        try:
            out = subprocess.run(
                [exe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,duration",
                 "-of", "json", path], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if out.returncode == 0:
                data = json.loads(out.stdout or "{}")
                streams = data.get("streams", [])
                dur = data.get("format", {}).get("duration")
                v = next((s for s in streams if s.get("codec_type") == "video"), {})
                info = {
                    "duration": float(dur) if dur not in (None, "N/A") else None,
                    "width": v.get("width"),
                    "height": v.get("height"),
                    "has_audio": any(s.get("codec_type") == "audio" for s in streams),
                }
        except Exception:
            info = None
    _probe_cache[path] = info
    return info


def lang_of(text):
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\uac00-\ud7a3]", text):
        return "ko"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "ja"
    return "en"


def count_chars(text):
    return len(re.sub(r"[\s\.,!?\u3001\u3002\uff01\uff1f\u2026'\"()\[\]\-~:;]", "", text))


def num(v, default=None):
    if v is None:
        return default
    if isinstance(v, bool):
        raise ValueError("expected a number")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        m = re.fullmatch(r"(\d+):(\d+(?:\.\d+)?)", s)  # "1:05.5" = 65.5 s
        if m:
            return int(m.group(1)) * 60 + float(m.group(2))
        return float(s)
    raise ValueError("expected a number")


class Report:
    def __init__(self):
        self.errors, self.warnings, self.infos = [], [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def info(self, msg):
        self.infos.append(msg)


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def unknown_keys(obj, allowed, where, rep):
    if isinstance(obj, dict):
        extra = sorted(set(obj) - allowed)
        if extra:
            rep.warn(f"{where}: unknown key(s) {extra} are ignored (typo?)")


def fmt_t(sec):
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m)}:{s:05.2f}"


def resolve(edit, workdir):
    """Validate edit.json and turn it into frame-exact props for the Remotion template.

    Returns (resolved, report). resolved['media'] lists every local file the render needs.
    """
    rep = Report()
    if not isinstance(edit, dict):
        rep.err("edit.json must be a JSON object")
        return None, rep
    unknown_keys(edit, TOP_KEYS, "edit.json", rep)

    fmt = edit.get("format", "9:16")
    if "width" in edit and "height" in edit:
        width, height = int(edit["width"]), int(edit["height"])
    elif fmt in FORMATS:
        width, height = FORMATS[fmt]
    else:
        rep.err(f"format '{fmt}' is not one of {list(FORMATS)} (or give width and height)")
        width, height = FORMATS["9:16"]
    if width % 2 or height % 2:
        rep.err("width and height must be even numbers for h264")
    fps = edit.get("fps", 30)
    try:
        fps = int(fps)
        assert 1 <= fps <= 120
    except Exception:
        rep.err("fps must be a whole number such as 24, 30 or 60")
        fps = 30

    def F(sec):
        return int(round(sec * fps))

    media = {}  # abs path -> kind

    def find(src, where, kinds):
        if not isinstance(src, str) or not src.strip():
            rep.err(f"{where}: 'src' is missing")
            return None, None
        p = src if os.path.isabs(src) else os.path.join(workdir, src)
        p = os.path.normpath(p)
        if not os.path.isfile(p):
            rep.err(f"{where}: file not found: {src}")
            return None, None
        ext = os.path.splitext(p)[1].lower()
        kind = "video" if ext in VIDEO_EXT else "image" if ext in IMAGE_EXT else "audio" if ext in AUDIO_EXT else "font" if ext in FONT_EXT else None
        if kind not in kinds:
            rep.err(f"{where}: {src} is not a supported {'/'.join(kinds)} file ({ext})")
            return None, None
        media[p] = kind
        return p, kind

    # ---------- style ----------
    style_in = edit.get("style", {}) or {}
    unknown_keys(style_in, STYLE_KEYS, "style", rep)
    cap_style = style_in.get("captions", "shorts" if height > width else "standard")
    if cap_style not in ("shorts", "standard"):
        rep.err("style.captions must be 'shorts' or 'standard'")
        cap_style = "standard"
    font_path = None
    if style_in.get("font_file"):
        font_path, _ = find(style_in["font_file"], "style.font_file", {"font"})
    all_text = " ".join(str(c.get("text", "")) for c in as_list(edit.get("captions")) if isinstance(c, dict))
    lang = style_in.get("lang") or lang_of(all_text)
    style = {
        "captions": cap_style,
        "font_family": style_in.get("font_family"),
        "font_path": font_path,
        "font_weight": int(style_in.get("font_weight", 800)),
        "text_color": style_in.get("text_color", "#FFFFFF"),
        "accent_color": style_in.get("accent_color", "#FFD43B"),
        "outline_color": style_in.get("outline_color", "#000000"),
        "box_color": style_in.get("box_color", "rgba(0,0,0,0.55)"),
        "caption_scale": float(style_in.get("caption_scale", 1.0)),
        "lang": lang,
    }

    # ---------- clips (one picture track, back to back) ----------
    clips = []
    cursor = 0
    prev_len = None
    clip_list = as_list(edit.get("clips"))
    if not clip_list:
        rep.err("'clips' is empty: the video needs at least one picture (video, image or color)")
    for i, c in enumerate(clip_list, 1):
        where = f"clips[{i}]"
        if not isinstance(c, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(c, CLIP_KEYS, where, rep)
        try:
            speed = num(c.get("speed"), 1.0)
            if speed <= 0:
                raise ValueError
        except Exception:
            rep.err(f"{where}: speed must be a positive number")
            speed = 1.0
        kind, path, src_dur = "color", None, None
        if c.get("src"):
            path, kind = find(c.get("src"), where, {"video", "image"})
            if path is None:
                continue
        elif not c.get("color"):
            rep.err(f"{where}: give 'src' (video/image file) or 'color'")
            continue
        try:
            t_in = num(c.get("in"), 0.0)
            t_out = num(c.get("out"))
            dur = num(c.get("duration"))
        except ValueError:
            rep.err(f"{where}: in/out/duration must be seconds (number or 'm:ss.s')")
            continue
        if kind == "video":
            info = probe(path)
            src_dur = info and info.get("duration")
            if src_dur is None:
                rep.warn(f"{where}: could not read the length of {c['src']} (is ffprobe installed?)")
            if t_out is None:
                if dur is not None:
                    t_out = t_in + dur * speed
                elif src_dur is not None:
                    t_out = src_dur
                else:
                    rep.err(f"{where}: give 'out' or 'duration' (length unknown)")
                    continue
            if t_out <= t_in:
                rep.err(f"{where}: out ({t_out}) must be after in ({t_in})")
                continue
            if src_dur is not None and t_out > src_dur + 0.05:
                rep.err(f"{where}: out {t_out:.2f}s is past the end of {c['src']} ({src_dur:.2f}s)")
                t_out = src_dur
            length = (t_out - t_in) / speed
        else:
            if dur is None:
                rep.warn(f"{where}: no 'duration' for a still/color, using 3 s")
                dur = 3.0
            if dur <= 0:
                rep.err(f"{where}: duration must be > 0")
                continue
            length = dur
        n = max(1, F(length))
        fit = c.get("fit", "cover")
        if fit not in ("cover", "contain", "blur"):
            rep.err(f"{where}: fit must be cover, contain or blur")
            fit = "cover"
        crop, src_w, src_h = None, 0, 0
        if path is not None:
            pinfo = probe(path) or {}
            src_w, src_h = int(pinfo.get("width") or 0), int(pinfo.get("height") or 0)
        if c.get("crop") is not None:
            cr = c["crop"]
            if not isinstance(cr, dict) or set(cr) - set(CROP_SIDES):
                rep.err(f"{where}: crop must be an object with top/bottom/left/right, e.g. {{\"bottom\": 0.15}}")
            elif path is None:
                rep.err(f"{where}: crop needs a video or image 'src'")
            elif not (src_w and src_h):
                rep.err(f"{where}: crop needs the source size, but it could not be read (is ffprobe installed?)")
            else:
                crop = {}
                for side in CROP_SIDES:
                    try:
                        v = num(cr.get(side), 0.0)
                    except ValueError:
                        v = -1
                    if v >= 1:  # pixels -> fraction
                        v = v / (src_w if side in ("left", "right") else src_h)
                    if v < 0 or v >= 0.9:
                        rep.err(f"{where}: crop.{side} must be a fraction 0-0.9 of the picture (or pixels)")
                        v = 0.0
                    crop[side] = round(v, 4)
                if crop["top"] + crop["bottom"] >= 0.9 or crop["left"] + crop["right"] >= 0.9:
                    rep.err(f"{where}: crop removes almost the whole picture")
                    crop = None
                elif not any(crop.values()):
                    crop = None
        zoom = c.get("zoom")
        if zoom not in (None, "in", "out"):
            rep.err(f"{where}: zoom must be 'in', 'out' or null")
            zoom = None
        trans = c.get("transition", "cut")
        if trans not in ("cut", "crossfade"):
            rep.err(f"{where}: transition must be 'cut' or 'crossfade'")
            trans = "cut"
        fade = 0
        if trans == "crossfade" and clips:
            td = num(c.get("transition_duration"), 0.4)
            fade = min(F(td), n // 2, (prev_len or n) // 2)
            if fade < F(td):
                rep.warn(f"{where}: crossfade shortened to {fade / fps:.2f}s to fit the clips")
        start = cursor - fade
        if n < F(0.5):
            rep.warn(f"{where}: very short shot ({n / fps:.2f}s)")
        clips.append({
            "kind": kind, "path": path, "color": c.get("color", "#000000"),
            "from": start, "dur": n, "trimBefore": F(t_in) if kind == "video" else 0,
            "speed": speed, "fit": fit, "zoom": zoom, "zoomAmount": float(c.get("zoom_amount", 0.06)),
            "volume": float(c.get("volume", 0.0)), "fadeIn": fade,
            "audioFadeIn": 0, "audioFadeOut": 0, "audio_fade": num(c.get("audio_fade"), 0.06),
            "crop": crop, "srcWidth": src_w, "srcHeight": src_h,
            "label": os.path.basename(path) if path else f"color {c.get('color')}",
            "src_in": t_in if kind == "video" else None,
        })
        cursor = start + n
        prev_len = n
    clips_end = cursor
    # Original-sound fades: follow the crossfades; at hard cuts a tiny ramp (audio_fade, default 0.06 s) avoids clicks.
    for i, c in enumerate(clips):
        ramp = max(2, F(c.pop("audio_fade") or 0)) if c["volume"] > 0 else 0
        nxt = clips[i + 1] if i + 1 < len(clips) else None
        c["audioFadeIn"] = c["fadeIn"] if c["fadeIn"] else (ramp if i > 0 else 0)
        c["audioFadeOut"] = nxt["fadeIn"] if nxt and nxt["fadeIn"] else ramp

    # ---------- narration (back to back unless 'start' is given) ----------
    audio = []
    narr_ranges = []
    ncur = 0
    for i, a in enumerate(as_list(edit.get("narration")), 1):
        where = f"narration[{i}]"
        if not isinstance(a, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(a, NARR_KEYS, where, rep)
        path, _ = find(a.get("src"), where, {"audio", "video"})
        if not path:
            continue
        info = probe(path)
        fdur = info and info.get("duration")
        t_in = num(a.get("in"), 0.0)
        t_out = num(a.get("out"), fdur)
        if t_out is None:
            rep.err(f"{where}: could not read the length of {a['src']}; give 'out'")
            continue
        start = F(num(a.get("start"))) if a.get("start") is not None else ncur + F(num(a.get("gap"), 0.0))
        n = max(1, F(t_out - t_in))
        audio.append({"role": "narration", "path": path, "from": start, "dur": n, "trimBefore": F(t_in),
                      "volume": float(a.get("volume", 1.0)), "loop": False, "fadeIn": 0, "fadeOut": 0,
                      "duck": [], "duckFactor": 1.0, "duckRamp": 1, "label": os.path.basename(path)})
        narr_ranges.append([start, start + n])
        ncur = start + n
    narr_end = max([b for _, b in narr_ranges], default=0)

    # ---------- captions ----------
    captions = []
    for i, c in enumerate(as_list(edit.get("captions")), 1):
        where = f"captions[{i}]"
        if not isinstance(c, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(c, CAP_KEYS, where, rep)
        text = str(c.get("text", "")).strip()
        if not text:
            rep.err(f"{where}: empty text")
            continue
        try:
            s, e = num(c.get("start")), num(c.get("end"))
        except ValueError:
            rep.err(f"{where}: start/end must be seconds")
            continue
        if s is None or e is None or e <= s:
            rep.err(f"{where}: needs start < end (got {c.get('start')}, {c.get('end')})")
            continue
        cs = c.get("style", cap_style)
        if cs not in ("shorts", "standard"):
            rep.err(f"{where}: style must be shorts or standard")
            cs = cap_style
        pos = c.get("position", "lower" if cs == "shorts" else "bottom")
        if pos not in POSITIONS:
            rep.err(f"{where}: position must be one of {sorted(POSITIONS)}")
            pos = "bottom"
        hl = [str(h) for h in as_list(c.get("highlight"))]
        for h in hl:
            if h.lower() not in text.lower():
                rep.warn(f"{where}: highlight '{h}' is not in the text")
        lg = lang_of(text)
        dur_s = e - s
        chars = count_chars(text)
        if dur_s < 0.6:
            rep.warn(f"{where}: on screen only {dur_s:.2f}s ('{text[:20]}')")
        if dur_s > 0 and chars / dur_s > CPS[lg]:
            rep.warn(f"{where}: {chars / dur_s:.1f} chars/s is fast to read (limit about {CPS[lg]:.0f} for {lg}); "
                     f"shorten the text or keep it on screen longer ('{text[:20]}')")
        lim = LINE_MAX[cs][lg]
        lines = text.split("\n")
        for ln in lines:
            if len(ln) > lim:
                rep.warn(f"{where}: line '{ln[:20]}' has {len(ln)} chars, over the usual {lim} for {cs} captions; "
                         f"shorten it or break it with \\n at a phrase boundary (the renderer may wrap it badly)")
        if len(lines) > 2:
            rep.warn(f"{where}: {len(lines)} lines; keep captions to 1-2 lines")
        captions.append({"text": text, "from": F(s), "dur": max(1, F(e) - F(s)), "style": cs, "position": pos,
                         "highlight": hl, "start_s": s, "end_s": e})
    captions.sort(key=lambda x: x["from"])
    for a, b in zip(captions, captions[1:]):
        if b["from"] < a["from"] + a["dur"] and a["position"] == b["position"]:
            rep.err(f"captions overlap at {fmt_t(b['start_s'])}: '{a['text'][:15]}' and '{b['text'][:15]}'")
    cap_end = max([c["from"] + c["dur"] for c in captions], default=0)

    # ---------- titles ----------
    titles = []
    for i, t in enumerate(as_list(edit.get("titles")), 1):
        where = f"titles[{i}]"
        if not isinstance(t, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(t, TITLE_KEYS, where, rep)
        kind = t.get("kind", "title")
        if kind not in ("title", "lower_third"):
            rep.err(f"{where}: kind must be 'title' or 'lower_third'")
            kind = "title"
        try:
            s, e = num(t.get("start")), num(t.get("end"))
        except ValueError:
            rep.err(f"{where}: start/end must be seconds")
            continue
        if s is None or e is None or e <= s:
            rep.err(f"{where}: needs start < end")
            continue
        if not str(t.get("text", "")).strip():
            rep.err(f"{where}: empty text")
            continue
        pos = t.get("position", "center" if kind == "title" else "bottom")
        if pos not in POSITIONS:
            rep.err(f"{where}: position must be one of {sorted(POSITIONS)}")
            pos = "center"
        titles.append({"kind": kind, "text": str(t["text"]), "sub": str(t.get("sub", "")), "from": F(s),
                       "dur": max(1, F(e) - F(s)), "position": pos,
                       "dim": bool(t.get("dim", pos == "center"))})
    title_end = max([t["from"] + t["dur"] for t in titles], default=0)

    # ---------- total length ----------
    tail = F(num(edit.get("tail"), 0.4)) if narr_ranges else 0
    auto_total = max(clips_end, narr_end + tail if narr_ranges else 0, cap_end, title_end, 1)
    if edit.get("duration") is not None:
        total = F(num(edit["duration"]))
        if total < auto_total:
            rep.warn(f"duration {total / fps:.2f}s cuts off content that runs to {auto_total / fps:.2f}s")
    else:
        total = auto_total
    if clips_end < total:
        rep.err(f"no picture from {fmt_t(clips_end / fps)} to {fmt_t(total / fps)} (black screen). "
                f"Add a clip or lengthen the last one")
    if narr_ranges and clips_end > narr_end + F(2.0) and edit.get("duration") is None:
        rep.warn(f"picture runs {(clips_end - narr_end) / fps:.1f}s after the narration ends")
    for c in captions:
        if c["from"] + c["dur"] > total:
            rep.err(f"caption '{c['text'][:15]}' ends after the video ends")
    for t in titles:
        if t["from"] + t["dur"] > total:
            rep.warn(f"title '{t['text'][:15]}' is cut at the end of the video")
    for a in audio:
        if a["from"] + a["dur"] > total:
            rep.warn(f"narration {a['label']} is cut at the end of the video")
    for x, y in zip(sorted(narr_ranges), sorted(narr_ranges)[1:]):
        if y[0] < x[1]:
            rep.err(f"narration files overlap at {fmt_t(y[0] / fps)}")
    if narr_ranges and not captions:
        rep.info("narration but no captions: add captions, or run transcribe_captions.py")

    # ---------- music ----------
    for i, m in enumerate(as_list(edit.get("music")), 1):
        where = f"music[{i}]"
        if not isinstance(m, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(m, MUSIC_KEYS, where, rep)
        path, _ = find(m.get("src"), where, {"audio", "video"})
        if not path:
            continue
        info = probe(path)
        fdur = info and info.get("duration")
        start = F(num(m.get("start"), 0.0))
        loop = bool(m.get("loop", True))
        t_in = num(m.get("in"), 0.0)
        n = total - start
        if m.get("duration") is not None:
            n = min(n, F(num(m["duration"])))
        if not loop and fdur is not None:
            n = min(n, F(fdur - t_in))
        if n <= 0:
            rep.warn(f"{where}: starts after the video ends, skipped")
            continue
        duck_db = float(m.get("duck_db", 10.0))
        audio.append({"role": "music", "path": path, "from": start, "dur": n, "trimBefore": F(t_in),
                      "volume": float(m.get("volume", 0.25)), "loop": loop,
                      "fadeIn": F(num(m.get("fade_in"), 0.0)), "fadeOut": F(num(m.get("fade_out"), 1.0)),
                      "duck": [list(r) for r in narr_ranges] if duck_db > 0 else [],
                      "duckFactor": 10 ** (-duck_db / 20.0), "duckRamp": F(0.25), "label": os.path.basename(path)})

    # ---------- sfx ----------
    for i, s in enumerate(as_list(edit.get("sfx")), 1):
        where = f"sfx[{i}]"
        if not isinstance(s, dict):
            rep.err(f"{where}: must be an object")
            continue
        unknown_keys(s, SFX_KEYS, where, rep)
        path, _ = find(s.get("src"), where, {"audio"})
        if not path:
            continue
        at = num(s.get("at"))
        if at is None:
            rep.err(f"{where}: 'at' (seconds) is missing")
            continue
        info = probe(path)
        fdur = (info and info.get("duration")) or 1.0
        start = F(at)
        if start >= total:
            rep.warn(f"{where}: at {at}s is after the video ends, skipped")
            continue
        audio.append({"role": "sfx", "path": path, "from": start, "dur": min(max(1, F(fdur)), total - start),
                      "trimBefore": 0, "volume": float(s.get("volume", 0.7)), "loop": False, "fadeIn": 0,
                      "fadeOut": 0, "duck": [], "duckFactor": 1.0, "duckRamp": 1, "label": os.path.basename(path)})

    # ---------- whole-video checks ----------
    secs = total / fps
    if edit.get("target_length") is not None:
        tgt = num(edit["target_length"])
        if tgt and abs(secs - tgt) / tgt > 0.1:
            rep.warn(f"total {secs:.1f}s is more than 10% off the target {tgt:.0f}s")
    if height > width and secs > 180:
        rep.warn(f"vertical video is {secs:.0f}s; YouTube Shorts allow up to 3 minutes")
    if not ffprobe_bin():
        rep.err("ffprobe not found: install ffmpeg (it includes ffprobe) and make sure it is on PATH")

    resolved = {
        "width": width, "height": height, "fps": fps, "durationInFrames": total,
        "background": edit.get("background", "#000000"), "style": style,
        "clips": clips, "audio": audio, "captions": captions, "titles": titles,
        "media": media,
    }
    return resolved, rep


def summary(res, rep):
    fps = res["fps"]
    lines = [f"Format {res['width']}x{res['height']} @ {fps} fps, total {fmt_t(res['durationInFrames'] / fps)} "
             f"({res['durationInFrames'] / fps:.2f}s, {res['durationInFrames']} frames)", "", "Picture track:"]
    for i, c in enumerate(res["clips"], 1):
        extra = []
        if c["src_in"] is not None:
            extra.append(f"source from {c['src_in']:.2f}s")
        if c["fadeIn"]:
            extra.append(f"crossfade {c['fadeIn'] / fps:.2f}s")
        if c["zoom"]:
            extra.append(f"zoom {c['zoom']}")
        if c["crop"]:
            extra.append("crop " + " ".join(f"{k} {v:.0%}" for k, v in c["crop"].items() if v))
        if c["volume"] > 0:
            extra.append(f"sound {c['volume']:.2f}")
        lines.append(f"  {i:>2}. {fmt_t(c['from'] / fps)}-{fmt_t((c['from'] + c['dur']) / fps)}  {c['label']}"
                     + (f"  ({', '.join(extra)})" if extra else ""))
    if res["audio"]:
        lines.append("Audio:")
        for a in res["audio"]:
            lines.append(f"  {a['role']:<9} {fmt_t(a['from'] / fps)}-{fmt_t((a['from'] + a['dur']) / fps)}  {a['label']}"
                         f"  vol {a['volume']:.2f}" + ("  (ducks under narration)" if a["duck"] else ""))
    lines.append(f"Captions: {len(res['captions'])}   Titles: {len(res['titles'])}")
    lines.append("")
    for m in rep.errors:
        lines.append(f"ERROR   {m}")
    for m in rep.warnings:
        lines.append(f"WARNING {m}")
    for m in rep.infos:
        lines.append(f"NOTE    {m}")
    lines.append(f"\n{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    return "\n".join(lines)


def load_edit(target):
    path = os.path.join(target, "edit.json") if os.path.isdir(target) else target
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f), os.path.dirname(os.path.abspath(path))


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default=".", help="work folder with edit.json, or the edit.json path")
    ap.add_argument("--json", help="write the resolved timeline to this file")
    args = ap.parse_args(argv)
    try:
        edit, workdir = load_edit(args.target)
    except FileNotFoundError:
        print(f"edit.json not found in {args.target}")
        return 2
    except json.JSONDecodeError as ex:
        print(f"edit.json is not valid JSON: {ex}")
        return 2
    res, rep = resolve(edit, workdir)
    if res is None:
        print("\n".join(rep.errors))
        return 1
    print(summary(res, rep))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in res.items() if k != "media"}, f, ensure_ascii=False, indent=2)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
