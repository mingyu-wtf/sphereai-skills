#!/usr/bin/env python3
"""Analyse one video so an agent can pick highlights from it.

Usage:
    python analyze.py VIDEO_OR_URL WORKDIR
    python analyze.py talk.mp4 work --lang ko --model medium
    python analyze.py "https://www.youtube.com/watch?v=..." work      # needs yt-dlp
    python analyze.py gameplay.mp4 work --no-transcript               # no speech: scenes + sound only

Writes into WORKDIR:
    source.<ext>          the video (a hard link or copy of the file, or the download)
    meta.json             length, size, fps, audio, how much speech, scene count, language
    transcript.json/.txt  speech with word times (faster-whisper; skipped if not installed or --no-transcript)
    scenes.json           shots between scene changes (ffmpeg scene score), with sound level and speech per shot
    audio_energy.json     loudness per second (dBFS), loud moments, sudden jumps, silences
    frames/               one small frame per shot (more for long shots), named by time
    contact_sheet_01.jpg  frames tiled with their numbers and times, for the agent to look at
    overview.txt          one line per shot: time, loudness, what is said; read this first
    (transcript.txt lines are "[start - end in seconds] (m:ss) text": use those seconds in highlight.json)

Needs Python 3.8+, ffmpeg + ffprobe on PATH. Optional: faster-whisper (speech), Pillow (labelled
contact sheets; without it the sheets have no labels and contact_sheets.json maps cells to times),
yt-dlp (URLs). On Windows with an NVIDIA GPU, `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12`
lets faster-whisper use the GPU; otherwise it runs on the CPU automatically.
"""
import argparse
import array
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace", line_buffering=True)
    except Exception:
        pass

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".avi"}
ENERGY_RATE = 8000  # Hz, enough for loudness


def tool(name):
    exe = shutil.which(name)
    if not exe:
        sys.exit(f"'{name}' not found. Install ffmpeg (it includes ffprobe) and make sure it is on PATH.")
    return exe


def fmt_t(sec):
    m, s = divmod(max(0.0, sec), 60)
    return f"{int(m)}:{s:04.1f}"


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- input
def get_source(src, workdir):
    if re.match(r"https?://", src):
        log(f"Downloading {src} ...")
        out_tpl = os.path.join(workdir, "source.%(ext)s")
        fmt = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/bv*[height<=1080]+ba/b"
        try:
            import yt_dlp  # noqa: F401
            cmd = [sys.executable, "-m", "yt_dlp"]
        except ImportError:
            exe = shutil.which("yt-dlp")
            if not exe:
                sys.exit("This is a URL but yt-dlp is not installed: pip install yt-dlp (or download the file yourself).")
            cmd = [exe]
        r = subprocess.run(cmd + ["-f", fmt, "--merge-output-format", "mp4", "--no-playlist", "-o", out_tpl, src])
        if r.returncode != 0:
            sys.exit("Download failed. Download the video yourself and pass the file instead.")
        for f in os.listdir(workdir):
            if f.startswith("source.") and os.path.splitext(f)[1].lower() in VIDEO_EXT:
                return os.path.join(workdir, f)
        sys.exit("Download finished but no video file was found.")
    if not os.path.isfile(src):
        sys.exit(f"File not found: {src}")
    ext = os.path.splitext(src)[1].lower() or ".mp4"
    dst = os.path.join(workdir, "source" + ext)
    if os.path.abspath(src) == os.path.abspath(dst):
        return dst
    if os.path.exists(dst):
        if os.path.getsize(dst) == os.path.getsize(src):
            return dst
        os.remove(dst)
    try:
        os.link(src, dst)  # instant, no extra space (same drive)
    except OSError:
        log("Copying the video into the work folder ...")
        shutil.copy2(src, dst)
    return dst


def probe(path):
    out = subprocess.run([tool("ffprobe"), "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,width,height,r_frame_rate,avg_frame_rate:stream_tags=rotate",
                          "-of", "json", path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = json.loads(out.stdout or "{}")
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not v:
        sys.exit("No video stream in this file.")

    def rate(s):
        try:
            a, b = s.split("/")
            return float(a) / float(b) if float(b) else 0.0
        except Exception:
            return 0.0
    fps = rate(v.get("avg_frame_rate", "0/0")) or rate(v.get("r_frame_rate", "0/0")) or 30.0
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    if str((v.get("tags") or {}).get("rotate", "0")) in ("90", "270", "-90"):
        w, h = h, w
    return {"duration": float(data.get("format", {}).get("duration") or 0), "width": w, "height": h,
            "fps": round(fps, 3), "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


# ---------------------------------------------------------------- scenes
def detect_cuts(src, threshold):
    """Times where the picture changes a lot (ffmpeg scene score > threshold)."""
    cmd = [tool("ffmpeg"), "-hide_banner", "-nostats", "-i", src, "-an", "-sn",
           "-vf", f"scale=320:-2,select='gt(scene,{threshold})',metadata=print", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    cuts, t = [], None
    for line in p.stderr.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            t = float(m.group(1))
            continue
        m = re.search(r"lavfi\.scene_score=([0-9.]+)", line)
        if m and t is not None:
            cuts.append((t, float(m.group(1))))
            t = None
    return cuts


def make_shots(cuts, duration, min_len=0.4):
    times = [0.0]
    scores = [None]
    for t, s in cuts:
        if t - times[-1] >= min_len and duration - t >= min_len:
            times.append(t)
            scores.append(s)
    times.append(duration)
    return [{"start": round(times[i], 3), "end": round(times[i + 1], 3), "cut_score": scores[i]}
            for i in range(len(times) - 1)]


# ---------------------------------------------------------------- sound
def extract_audio(src, wav, rate):
    subprocess.run([tool("ffmpeg"), "-y", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(rate),
                    "-c:a", "pcm_s16le", wav], check=True)


def loudness_per_second(src, duration):
    p = subprocess.run([tool("ffmpeg"), "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(ENERGY_RATE),
                        "-f", "s16le", "-"], capture_output=True)
    samples = array.array("h")
    samples.frombytes(p.stdout[: len(p.stdout) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    n_sec = int(math.ceil(duration)) or 1
    out = []
    for i in range(n_sec):
        chunk = samples[i * ENERGY_RATE:(i + 1) * ENERGY_RATE]
        if not chunk:
            out.append(-90.0)
            continue
        ms = sum(x * x for x in chunk) / len(chunk)
        out.append(round(10 * math.log10(ms / (32768.0 ** 2)) if ms > 0 else -90.0, 1))
    return out


def ranges(flags, min_len=1):
    res, start = [], None
    for i, f in enumerate(flags + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_len:
                res.append([start, i])
            start = None
    return res


def sound_summary(db):
    vals = sorted(v for v in db if v > -89)
    if not vals:
        return {"median_db": None, "loud": [], "jumps": [], "silences": []}
    med = vals[len(vals) // 2]
    p90 = vals[int(len(vals) * 0.9)]
    loud_cut = max(p90, med + 6)
    loud = [{"start": a, "end": b, "peak_db": max(db[a:b])} for a, b in ranges([v >= loud_cut for v in db])]
    loud.sort(key=lambda x: -x["peak_db"])
    jumps = []
    for i in range(3, len(db)):
        before = sum(db[i - 3:i]) / 3
        if db[i] - before >= 8 and db[i] > med:
            if not jumps or i - jumps[-1]["at"] > 2:
                jumps.append({"at": i, "rise_db": round(db[i] - before, 1), "db": db[i]})
    silences = [{"start": a, "end": b} for a, b in ranges([v < min(-45, med - 20) for v in db], min_len=2)]
    return {"median_db": med, "loud_threshold_db": loud_cut, "loud": loud[:40], "jumps": jumps[:60], "silences": silences}


# ---------------------------------------------------------------- speech
def transcribe(wav, lang, model_name, device):
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    try:
        import transcribe_captions
        transcribe_captions.add_nvidia_dll_dirs()
        from faster_whisper import WhisperModel
    except ImportError:
        log("faster-whisper is not installed: skipping speech (pip install faster-whisper). Scenes and sound still work.")
        return None

    def run(dev, compute):
        model = WhisperModel(model_name, device=dev, compute_type=compute)
        segs, info = model.transcribe(wav, language=lang, word_timestamps=True, vad_filter=True)
        out = []
        for s in segs:  # the work happens inside this loop
            words = [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)} for w in (s.words or []) if w.word.strip()]
            out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(), "words": words})
        try:
            used = model.model.device  # "cuda" or "cpu" when dev is "auto"
        except Exception:
            used = dev
        return out, info.language, used

    try:
        return run(device, "auto")
    except RuntimeError as ex:
        if device == "cpu" or not re.search(r"cuda|cublas|cudnn|dll|\.so", str(ex), re.I):
            raise
        log(f"GPU speech recognition failed ({str(ex)[:120]}); retrying on the CPU (slower)...")
        return run("cpu", "int8")


# ---------------------------------------------------------------- frames
def sample_times(shots, duration, every, max_frames):
    pts = []
    for i, sh in enumerate(shots):
        length = sh["end"] - sh["start"]
        n = max(1, int(length // every))
        for k in range(n):
            pts.append((i, sh["start"] + length * (k + 0.5) / n))
    if len(pts) > max_frames:  # keep one per shot first, then thin the rest evenly
        firsts = {}
        for i, t in pts:
            firsts.setdefault(i, t)
        keep = sorted(firsts.items(), key=lambda x: x[1])
        if len(keep) > max_frames:
            step = len(keep) / max_frames
            keep = [keep[int(k * step)] for k in range(max_frames)]
        else:
            rest = [p for p in pts if p not in keep]
            step = len(rest) / max(1, max_frames - len(keep))
            keep += [rest[int(k * step)] for k in range(max_frames - len(keep)) if int(k * step) < len(rest)]
        pts = sorted(set(keep), key=lambda x: x[1])
    return [(i, min(t, max(0.0, duration - 0.05))) for i, t in pts]


def grab_frames(src, pts, frames_dir, width):
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir, exist_ok=True)
    out = []
    for n, (shot, t) in enumerate(pts, 1):
        name = f"f{n:03d}_{int(t // 60):02d}m{int(t % 60):02d}s.jpg"
        dst = os.path.join(frames_dir, name)
        subprocess.run([tool("ffmpeg"), "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
                        "-vf", f"scale={width}:-2", "-q:v", "4", dst], check=False)
        if os.path.isfile(dst):
            out.append({"n": n, "shot": shot + 1, "t": round(t, 2), "file": f"frames/{name}"})
    return out


def contact_sheets(frames, workdir, cols, rows):
    per = cols * rows
    pages = [frames[i:i + per] for i in range(0, len(frames), per)]
    sheets = []
    for old in os.listdir(workdir):
        if re.match(r"contact_sheet_\d+\.jpg$", old):
            os.remove(os.path.join(workdir, old))
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        Image = None
    for pi, page in enumerate(pages, 1):
        name = f"contact_sheet_{pi:02d}.jpg"
        dst = os.path.join(workdir, name)
        if Image is not None:
            ims = [Image.open(os.path.join(workdir, f["file"])).convert("RGB") for f in page]
            tw, th = ims[0].size
            bar = max(22, th // 7)
            sheet = Image.new("RGB", (cols * tw, rows * (th + bar)), (16, 16, 20))
            draw = ImageDraw.Draw(sheet)
            try:
                font = ImageFont.load_default(size=int(bar * 0.8))
            except TypeError:
                font = ImageFont.load_default()
            for k, (im, f) in enumerate(zip(ims, page)):
                x, y = (k % cols) * tw, (k // cols) * (th + bar)
                sheet.paste(im.resize((tw, th)), (x, y))
                draw.text((x + 6, y + th + 1), f"#{f['n']}  {fmt_t(f['t'])}  shot {f['shot']}", fill=(255, 225, 80), font=font)
            sheet.save(dst, quality=85)
        else:
            lst = os.path.join(workdir, "_sheet_list.txt")
            with open(lst, "w", encoding="utf-8") as fh:
                for f in page:
                    fh.write(f"file '{os.path.join(workdir, f['file']).replace(os.sep, '/')}'\n")
            subprocess.run([tool("ffmpeg"), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                            "-vf", f"tile={cols}x{rows}", "-frames:v", "1", "-q:v", "4", dst], check=False)
            os.remove(lst)
        sheets.append({"file": name, "cells": [{"row": k // cols + 1, "col": k % cols + 1, "n": f["n"], "t": f["t"]}
                                               for k, f in enumerate(page)]})
    return sheets


# ---------------------------------------------------------------- main
def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="video file or URL")
    ap.add_argument("workdir", help="work folder (created if needed)")
    ap.add_argument("--lang", help="speech language: ko, en, ja ... (auto-detect if omitted)")
    ap.add_argument("--model", default="small", help="faster-whisper model: tiny, base, small (default), medium, large-v3")
    ap.add_argument("--device", default="auto", help="auto, cuda or cpu")
    ap.add_argument("--no-transcript", action="store_true", help="skip speech recognition")
    ap.add_argument("--scene-threshold", type=float, default=0.3, help="scene change sensitivity, lower = more cuts (default 0.3)")
    ap.add_argument("--frame-every", type=float, default=8.0, help="extra frame every N seconds inside long shots (default 8)")
    ap.add_argument("--max-frames", type=int, default=180, help="cap on frames for the contact sheets (default 180)")
    ap.add_argument("--thumb", type=int, default=320, help="frame width in pixels (default 320)")
    args = ap.parse_args(argv)

    t0 = time.time()
    workdir = os.path.abspath(args.workdir)
    os.makedirs(workdir, exist_ok=True)
    src = get_source(args.source, workdir)
    info = probe(src)
    dur = info["duration"]
    log(f"Video: {os.path.basename(src)}  {info['width']}x{info['height']}  {info['fps']} fps  {fmt_t(dur)}  "
        f"audio: {'yes' if info['has_audio'] else 'no'}")

    log("Finding scene changes ...")
    t = time.time()
    shots = make_shots(detect_cuts(src, args.scene_threshold), dur)
    log(f"  {len(shots)} shots ({time.time() - t:.0f}s)")

    db, sound = [], {"median_db": None, "loud": [], "jumps": [], "silences": []}
    if info["has_audio"]:
        log("Measuring loudness ...")
        db = loudness_per_second(src, dur)
        sound = sound_summary(db)

    transcript, lang, device_used = None, args.lang, None
    if info["has_audio"] and not args.no_transcript:
        wav = os.path.join(workdir, "audio_16k.wav")
        extract_audio(src, wav, 16000)
        log(f"Recognising speech (faster-whisper {args.model}) ...")
        t = time.time()
        r = transcribe(wav, args.lang, args.model, args.device)
        if r:
            transcript, lang, device_used = r
            log(f"  {len(transcript)} segments, language {lang}, on {device_used} ({time.time() - t:.0f}s)")

    # speech coverage
    words = [w for s in (transcript or []) for w in s["words"]]
    spoken = [False] * (int(math.ceil(dur)) or 1)
    for w in words:
        for k in range(int(w["s"]), min(len(spoken), int(math.ceil(w["e"])))):
            spoken[k] = True
    speech_ratio = round(sum(spoken) / len(spoken), 3) if words else 0.0
    speech = "none" if not words else "mostly" if speech_ratio >= 0.5 else "some" if speech_ratio >= 0.15 else "little"

    # per-shot facts
    for i, sh in enumerate(shots, 1):
        sh["n"] = i
        sh["length"] = round(sh["end"] - sh["start"], 2)
        secs = db[int(sh["start"]):max(int(sh["start"]) + 1, int(math.ceil(sh["end"])))] if db else []
        sh["mean_db"] = round(sum(secs) / len(secs), 1) if secs else None
        sh["peak_db"] = max(secs) if secs else None
        sh["text"] = "".join(w["w"] for w in words if sh["start"] <= (w["s"] + w["e"]) / 2 < sh["end"]).strip()

    pts = sample_times(shots, dur, args.frame_every, args.max_frames)
    log(f"Saving {len(pts)} frames ...")
    frames = grab_frames(src, pts, os.path.join(workdir, "frames"), args.thumb)
    for sh in shots:
        sh["frames"] = [f["n"] for f in frames if f["shot"] == sh["n"]]
    vertical = info["height"] > info["width"]
    sheets = contact_sheets(frames, workdir, 4 if vertical else 5, 4 if vertical else 6)

    # ---- write files
    def dump(name, obj):
        with open(os.path.join(workdir, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)

    meta = {
        "source": os.path.basename(src), "input": args.source, "duration": round(dur, 3),
        "width": info["width"], "height": info["height"], "fps": info["fps"],
        "orientation": "vertical" if vertical else "horizontal" if info["width"] > info["height"] else "square",
        "has_audio": info["has_audio"], "speech": speech, "speech_ratio": speech_ratio, "language": lang,
        "transcribed": transcript is not None, "whisper_model": args.model if transcript is not None else None,
        "whisper_device": device_used, "shots": len(shots), "scene_threshold": args.scene_threshold,
        "median_db": sound.get("median_db"), "frames": len(frames),
        "contact_sheets": [s["file"] for s in sheets],
    }
    dump("meta.json", meta)
    dump("scenes.json", {"threshold": args.scene_threshold, "shots": shots})
    dump("audio_energy.json", {"unit": "dBFS per second (index = second)", "per_second": db, **sound})
    dump("frames.json", frames)
    dump("contact_sheets.json", sheets)
    if transcript is not None:
        dump("transcript.json", {"language": lang, "segments": transcript})
        with open(os.path.join(workdir, "transcript.txt"), "w", encoding="utf-8") as f:
            for s in transcript:
                f.write(f"[{s['start']:.2f} - {s['end']:.2f}] ({fmt_t(s['start'])}) {s['text']}\n")

    loud_secs = {k for r in sound.get("loud", []) for k in range(r["start"], r["end"])}
    jump_secs = {j["at"] for j in sound.get("jumps", [])}
    with open(os.path.join(workdir, "overview.txt"), "w", encoding="utf-8") as f:
        f.write(f"{meta['source']}  {info['width']}x{info['height']}  {info['fps']} fps  {fmt_t(dur)} ({dur:.1f}s)\n")
        f.write(f"speech: {speech} ({speech_ratio:.0%} of seconds)  language: {lang or '-'}  shots: {len(shots)}  "
                f"median loudness: {sound.get('median_db') if sound.get('median_db') is not None else '-'} dBFS\n")
        f.write("columns: shot  start-end (length)  mean/peak dB  [LOUD] [JUMP]  frames  | speech in the shot\n\n")
        for sh in shots:
            marks = []
            rng = range(int(sh["start"]), int(math.ceil(sh["end"])))
            if any(k in loud_secs for k in rng):
                marks.append("LOUD")
            if any(k in jump_secs for k in rng):
                marks.append("JUMP")
            fr = ",".join(f"#{n}" for n in sh["frames"][:6]) + ("..." if len(sh["frames"]) > 6 else "")
            txt = sh["text"]
            if len(txt) > 160:
                txt = txt[:157] + "..."
            f.write(f"{sh['n']:>4}  {fmt_t(sh['start'])}-{fmt_t(sh['end'])} ({sh['length']:.1f}s)  "
                    f"{sh['mean_db'] if sh['mean_db'] is not None else '-'}/{sh['peak_db'] if sh['peak_db'] is not None else '-'} dB"
                    f"  {' '.join(marks):<9} {fr:<16} | {txt}\n")
        if sound.get("loud"):
            f.write("\nLoudest moments (laughs, cheers, impacts, music peaks - look at them):\n")
            for r in sorted(sound["loud"][:15], key=lambda x: x["start"]):
                f.write(f"  {fmt_t(r['start'])}-{fmt_t(r['end'])}  peak {r['peak_db']} dB\n")
        if sound.get("jumps"):
            f.write("\nSudden jumps in sound:\n  " + ", ".join(f"{fmt_t(j['at'])} (+{j['rise_db']} dB)" for j in sound["jumps"][:30]) + "\n")
        if sound.get("silences"):
            f.write("\nSilences (2 s or more):\n  " + ", ".join(f"{fmt_t(s['start'])}-{fmt_t(s['end'])}" for s in sound["silences"][:30]) + "\n")

    log(f"\nDone in {time.time() - t0:.0f}s -> {workdir}")
    log(f"  speech: {speech} ({speech_ratio:.0%})   shots: {len(shots)}   frames: {len(frames)}   sheets: {len(sheets)}")
    log("  Read overview.txt and transcript.txt, then open every contact_sheet_*.jpg before choosing highlights.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
