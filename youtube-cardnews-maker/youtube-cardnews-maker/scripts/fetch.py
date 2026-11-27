# -*- coding: utf-8 -*-
"""Step 1: fetch a YouTube video's metadata, transcript and a 720p copy of the video.

Usage:
  python fetch.py "https://www.youtube.com/watch?v=VIDEO_ID" --out work/my-video
  python fetch.py URL --out work/x --no-video      # transcript only (no cards with video frames)
  python fetch.py URL --out work/x --stt           # skip captions, use local speech recognition

Writes into --out:
  meta.json         video_id, title, channel, duration, url, language, transcript_source
  transcript.json   [{"start": 12.3, "end": 15.0, "text": "..."}]  (seconds)
  transcript.txt    "[mm:ss] text" lines for reading
  video.mp4         720p-or-lower copy (unless --no-video)

Free tools only: yt-dlp, youtube-transcript-api, ffmpeg, optional faster-whisper. No API keys.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_LANGS = ["ko", "en"]
NOISE_RE = re.compile(r"^[\(\[（][^\)\]）]{0,30}[\)\]）]$")  # (Laughter) [Music] [박수] ...


def video_id_of(url: str) -> str:
    for pat in (r"(?:v=|/videos/|embed/|youtu\.be/|/v/|/e/|shorts/|live/)([0-9A-Za-z_-]{11})", r"^([0-9A-Za-z_-]{11})$"):
        m = re.search(pat, url)
        if m:
            return m.group(1)
    sys.exit(f"Could not find a video id in: {url}")


def get_meta(url: str) -> dict:
    import yt_dlp
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "video_id": info.get("id"),
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader", ""),
        "duration": info.get("duration") or 0,
        "url": f"https://www.youtube.com/watch?v={info.get('id')}",
        "language": info.get("language") or "",
    }


def to_segments(snippets) -> list:
    segs = []
    for s in snippets:
        text, start = (s.text, s.start) if hasattr(s, "text") else (s["text"], s["start"])
        dur = getattr(s, "duration", None) if hasattr(s, "text") else s.get("duration")
        text = " ".join(str(text).split())
        if text and not NOISE_RE.match(text):
            segs.append({"start": round(float(start), 2), "dur": float(dur or 0), "text": text})
    for i, s in enumerate(segs):  # end = next start (captions overlap), capped by own duration + 1s
        nxt = segs[i + 1]["start"] if i + 1 < len(segs) else s["start"] + (s["dur"] or 3)
        s["end"] = round(max(s["start"] + 0.3, min(nxt, s["start"] + (s["dur"] or 4) + 1.0)), 2)
        s.pop("dur", None)
    return segs


def get_transcript(video_id: str, prefer: str = "ko"):
    from youtube_transcript_api import YouTubeTranscriptApi
    try:
        tl = YouTubeTranscriptApi().list(video_id)
    except Exception as e:  # captions disabled / unavailable / blocked
        print(f"[warn] no caption list: {e}", file=sys.stderr)
        return None
    order = list(dict.fromkeys([prefer] + DEFAULT_LANGS))
    for finder, label in ((tl.find_manually_created_transcript, "manual"), (tl.find_generated_transcript, "auto")):
        try:
            t = finder(order)
            return to_segments(t.fetch()), f"{label} captions ({t.language_code})", t.language_code
        except Exception:
            continue
    for t in tl:  # any language at all
        try:
            return to_segments(t.fetch()), f"{'auto' if t.is_generated else 'manual'} captions ({t.language_code})", t.language_code
        except Exception:
            continue
    return None


def run(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", cwd=cwd)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise RuntimeError(f"command failed: {cmd[0]}")


def stt(url: str, out: Path, model_size: str):
    """Local speech recognition (free). Needs: pip install faster-whisper"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("No captions found and faster-whisper is not installed. Run: pip install faster-whisper")
    import yt_dlp
    raw = out / "audio_raw"
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "format": "bestaudio/best", "outtmpl": str(raw) + ".%(ext)s"}) as ydl:
        ydl.download([url])
    src = next(out.glob("audio_raw.*"))
    run(["ffmpeg", "-y", "-i", src.name, "-ac", "1", "-ar", "16000", "audio.wav"], cwd=str(out))
    src.unlink(missing_ok=True)
    try:
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
    raw_segs, info = model.transcribe(str(out / "audio.wav"), vad_filter=True)
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in raw_segs if s.text.strip()]
    (out / "audio.wav").unlink(missing_ok=True)
    return segs, "speech recognition (faster-whisper)", info.language


def download_video(url: str, out: Path):
    import yt_dlp
    base = {"quiet": True, "no_warnings": True, "noprogress": True,
            "format": "bv*[height<=720]+ba/b[height<=720]/b", "merge_output_format": "mp4",
            "outtmpl": str(out / "video_raw") + ".%(ext)s"}
    last = None
    for extra in ({"extractor_args": {"youtube": {"player_client": ["android", "web"]}}}, {}):
        try:
            with yt_dlp.YoutubeDL({**base, **extra}) as ydl:
                ydl.download([url])
            break
        except Exception as e:  # first client list can be blocked; retry with defaults
            last = e
    else:
        raise RuntimeError(f"video download failed: {last}")
    cands = sorted(out.glob("video_raw.*"))
    mp4 = next((c for c in cands if c.suffix == ".mp4"), cands[0] if cands else None)
    if mp4 is None:
        raise RuntimeError("video download produced no file")
    target = out / "video.mp4"
    target.unlink(missing_ok=True)
    mp4.rename(target)
    for c in cands:
        if c.exists() and c != target:
            c.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", required=True, help="work folder (created if missing)")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--stt", action="store_true", help="force local speech recognition")
    ap.add_argument("--lang", default="ko", help="caption language to prefer (default ko; use en to get the original English captions)")
    ap.add_argument("--whisper-model", default="medium")
    a = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for exe in ("ffmpeg", "ffprobe"):
        if shutil.which(exe) is None:
            sys.exit(f"{exe} not found. Install ffmpeg first (https://ffmpeg.org/download.html).")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    vid = video_id_of(a.url)

    print("[1/3] metadata...")
    meta = get_meta(a.url)

    print("[2/3] transcript...")
    res = None if a.stt else get_transcript(vid, a.lang)
    if res is None:
        print("  no captions - using local speech recognition")
        res = stt(a.url, out, a.whisper_model)
    segs, source, lang = res
    if not segs:
        sys.exit("Transcript is empty.")
    meta["language"] = (lang or meta["language"] or "").split("-")[0]
    meta["transcript_source"] = source
    meta["needs_translation"] = meta["language"] != "ko"

    (out / "transcript.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "transcript.txt").write_text(
        "\n".join(f"[{int(s['start']) // 60:02d}:{int(s['start']) % 60:02d}|{s['start']:.1f}s] {s['text']}" for s in segs),
        encoding="utf-8")

    if not a.no_video and (out / "video.mp4").exists():
        print("[3/3] video.mp4 already there - skipped")
    elif not a.no_video:
        print("[3/3] video (<=720p)...")
        try:
            download_video(a.url, out)
        except Exception as e:
            print(f"[warn] {e} - cards will use gradient backgrounds and highlights are unavailable", file=sys.stderr)
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== done ===")
    print(f"title       : {meta['title']}")
    print(f"channel     : {meta['channel']}")
    print(f"duration    : {meta['duration']}s")
    print(f"language    : {meta['language']}  (translate to Korean: {meta['needs_translation']})")
    print(f"transcript  : {source}, {len(segs)} lines")
    print(f"video file  : {'yes' if (out / 'video.mp4').exists() else 'no'}")


if __name__ == "__main__":
    main()
