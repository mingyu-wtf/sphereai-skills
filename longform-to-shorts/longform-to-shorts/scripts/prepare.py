# -*- coding: utf-8 -*-
"""Step 1: bring in the long video and transcribe it word by word (free, local).

Usage:
  python prepare.py <video file or YouTube URL> --out work/<name> [--model small|medium|large-v3] [--lang auto|en|ko|ja ...]

Writes into the work folder:
  video.mp4        the source (copied, or downloaded at up to 1080p)
  meta.json        duration, size, fps, title
  transcript.json  segments with word timestamps  [{start, end, text, words:[{start,end,word}]}]
  transcript.txt   one line per segment: [mm:ss|seconds] text   (read this to pick moments)

Needs: pip install faster-whisper yt-dlp ; ffmpeg on PATH. Uses the GPU automatically when CUDA is available.
No API key, nothing is uploaded.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd[:3])} ...\n{r.stderr[-800:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_type",
               "-of", "json", str(path)])
    j = json.loads(out)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in j["streams"])
    num, den = (v.get("r_frame_rate", "30/1").split("/") + ["1"])[:2]
    return {"duration": float(j["format"]["duration"]), "width": v.get("width"), "height": v.get("height"),
            "fps": round(float(num) / float(den or 1), 3), "has_audio": a}


def fetch(src, out: Path):
    dst = out / "video.mp4"
    title = ""
    if src.startswith(("http://", "https://")):
        if shutil.which("yt-dlp") is None:
            try:
                import yt_dlp  # noqa: F401
            except ImportError:
                sys.exit("yt-dlp is not installed: pip install yt-dlp")
        cmd = [sys.executable, "-m", "yt_dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]", "--merge-output-format", "mp4",
               "-o", str(dst), "--print", "title", "--no-simulate", src]
        lines = run(cmd).strip().splitlines()
        title = lines[-1] if lines else ""
    else:
        p = Path(src)
        if not p.exists():
            sys.exit(f"file not found: {src}")
        if p.suffix.lower() == ".mp4":
            shutil.copy(p, dst)
        else:
            run(["ffmpeg", "-y", "-v", "error", "-i", str(p), "-c:v", "libx264", "-crf", "18", "-c:a", "aac", str(dst)])
        title = p.stem
    return dst, title


def _add_cuda_dlls():
    """On Windows, let ctranslate2 find CUDA libraries installed with pip (nvidia-cublas-cu12, nvidia-cudnn-cu12)."""
    import os
    if os.name != "nt":
        return
    try:
        import nvidia
    except ImportError:
        return
    root = Path(list(nvidia.__path__)[0])
    for b in root.glob("*/bin"):
        try:
            os.add_dll_directory(str(b))
        except OSError:
            pass
        os.environ["PATH"] = str(b) + os.pathsep + os.environ.get("PATH", "")


def _run_whisper(model_size, device, ctype, wav, lang):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device=device, compute_type=ctype)
    segs, info = model.transcribe(str(wav), language=None if lang == "auto" else lang, word_timestamps=True,
                                  vad_filter=True, vad_parameters={"min_silence_duration_ms": 400})
    rows = []
    for s in segs:  # decoding happens here, so GPU library errors show up inside this loop
        words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word} for w in (s.words or [])]
        rows.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "words": words})
        print(chr(13) + "  transcribed %7.1fs (%s)" % (s.end, device), end="", file=sys.stderr)
    print(file=sys.stderr)
    return rows, info.language


def transcribe(video: Path, out: Path, model_size: str, lang: str):
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        sys.exit("faster-whisper is not installed: pip install faster-whisper")
    _add_cuda_dlls()
    wav = out / "audio16k.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    rows = lang_found = None
    for device, ctype in (("cuda", "float16"), ("cpu", "int8")):
        try:
            rows, lang_found = _run_whisper(model_size, device, ctype, wav, lang)
            break
        except Exception as e:  # noqa: BLE001  (no GPU or missing CUDA libraries -> CPU)
            print(f"\n[info] {device} failed ({str(e)[:90]}); trying the next option", file=sys.stderr)
    if rows is None:
        sys.exit("Transcription failed on both GPU and CPU.")
    wav.unlink(missing_ok=True)
    return rows, lang_found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="small", help="faster-whisper model: small (fast), medium, large-v3 (best)")
    ap.add_argument("--lang", default="auto", help="speech language code, or auto")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if "#" in a.out:
        sys.exit("Use a work folder path without '#' (ffmpeg treats it specially).")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    video, title = fetch(a.src, out)
    meta = probe(video)
    if not meta["has_audio"]:
        sys.exit("The video has no audio track - this skill picks moments from speech.")
    meta["title"] = title
    meta["source"] = a.src
    rows, lang = transcribe(video, out, a.model, a.lang)
    meta["language"] = lang
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "transcript.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"[{int(r['start'] // 60):02d}:{int(r['start'] % 60):02d}|{r['start']:.1f}] {r['text']}" for r in rows]
    (out / "transcript.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"video      {video}  ({meta['width']}x{meta['height']}, {meta['duration']:.0f}s)")
    print(f"language   {lang}")
    print(f"transcript {out / 'transcript.txt'}  ({len(rows)} lines)")


if __name__ == "__main__":
    main()
