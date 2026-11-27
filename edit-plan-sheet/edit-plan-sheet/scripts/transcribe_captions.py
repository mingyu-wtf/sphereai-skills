#!/usr/bin/env python3
"""Optional: make caption timings from a narration file with faster-whisper (free, runs locally).

Usage:
    python transcribe_captions.py narration.mp3 --lang ko
    python transcribe_captions.py narration.mp3 --lang ko --script script.txt --into edit.json
    python transcribe_captions.py narration.mp3 --lang ja --max-chars 12 --offset 1.5 --out captions.json

--script  The exact narration text. Strongly recommended: the captions then use YOUR text
          (no speech-recognition typos in names and numbers) and only the timing comes from the audio.
--into    Replace the "captions" list of that edit.json (other keys are kept).
--offset  Seconds to add, if the narration does not start at 0 in the edit.

If faster-whisper is not installed this script says so and exits with code 3; the rest of the
skill works without it (write caption times by hand, or use one audio file per sentence).
Install: pip install faster-whisper   (the first run downloads the model, ~460 MB for "small")
"""
import argparse
import json
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

DEFAULT_MAX = {"ko": 14, "ja": 12, "zh": 12}
SENT_END = r"(?<=[.!?\u3002\uff01\uff1f])\s*|\n+"


def norm(s):
    return re.sub(r"[\s\.,!?\u3001\u3002\uff01\uff1f\u2026'\"()\[\]\-~:;]", "", s)


def chunk_sentence(sent, max_chars):
    """Split one sentence into caption-sized pieces at commas, then spaces, then (no spaces) by length."""
    sent = sent.strip()
    if len(sent) <= max_chars:
        return [sent] if sent else []
    parts = [p.strip() for p in re.split(r"(?<=[,\u3001\uff0c])\s*", sent) if p.strip()]
    if len(parts) > 1:
        out = []
        for p in parts:
            out.extend(chunk_sentence(p, max_chars))
        return out
    words = sent.split(" ")
    if len(words) > 1:
        out, cur = [], ""
        for w in words:
            nxt = (cur + " " + w).strip()
            if len(nxt) > max_chars and cur:
                out.append(cur)
                cur = w
            else:
                cur = nxt
        if cur:
            out.append(cur)
        # Do not leave a tiny last piece on its own.
        if len(out) > 1 and len(out[-1]) <= 3:
            last = out.pop()
            out[-1] = out[-1] + " " + last
        return out
    return [sent[i:i + max_chars] for i in range(0, len(sent), max_chars)]


def chunk_text(text, max_chars):
    out = []
    for sent in re.split(SENT_END, text):
        if sent and sent.strip():
            out.extend(chunk_sentence(sent, max_chars))
    return out


def add_nvidia_dll_dirs():
    """Windows: make the CUDA DLLs from `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` findable.

    Python 3.8+ no longer searches PATH for DLLs, so without this faster-whisper falls back to the CPU
    even when those packages are installed. Harmless on other systems or when they are missing.
    """
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return
    import site
    roots = []
    try:
        roots += site.getsitepackages()
    except Exception:
        pass
    try:
        roots.append(site.getusersitepackages())
    except Exception:
        pass
    for root in roots:
        base = os.path.join(root, "nvidia")
        if not os.path.isdir(base):
            continue
        for pkg in os.listdir(base):
            d = os.path.join(base, pkg, "bin")
            if os.path.isdir(d):
                try:
                    os.add_dll_directory(d)
                    os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                except OSError:
                    pass


def load_words(audio, lang, model_name, device="auto"):
    add_nvidia_dll_dirs()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper is not installed. Skip this step, or run: pip install faster-whisper")
        sys.exit(3)
    def run(device, compute):
        model = WhisperModel(model_name, device=device, compute_type=compute)
        segments, _ = model.transcribe(audio, language=lang, word_timestamps=True, vad_filter=True)
        out = []
        for seg in segments:  # transcription happens lazily, inside this loop
            for w in seg.words or []:
                if w.word.strip():
                    out.append((w.word, float(w.start), float(w.end)))
        return out

    try:
        words = run(device, "auto")
    except RuntimeError as ex:
        # A GPU is present but the CUDA libraries are missing or broken: fall back to the CPU.
        if device == "cpu" or not re.search(r"cuda|cublas|cudnn|dll|\.so", str(ex), re.I):
            raise
        print(f"GPU transcription failed ({ex}); retrying on CPU...")
        words = run("cpu", "int8")
    if not words:
        sys.exit("No speech found in the audio.")
    return words


def captions_from_words(words, max_chars):
    caps, cur = [], []

    def flush():
        if cur:
            caps.append({"text": "".join(w for w, _, _ in cur).strip(), "start": cur[0][1], "end": cur[-1][2]})
            cur.clear()

    for i, (w, s, e) in enumerate(words):
        if cur and (len("".join(x for x, _, _ in cur + [(w, s, e)]).strip()) > max_chars or s - cur[-1][2] > 0.5):
            flush()
        cur.append((w, s, e))
        if re.search(r"[.!?\u3002\uff01\uff1f,\u3001]$", w.strip()):
            flush()
    flush()
    return caps


def captions_from_script(words, script, max_chars):
    """Use the script's text; place each piece in time by its share of characters in the recognised words."""
    chunks = chunk_text(script, max_chars)
    # Character positions of each recognised word.
    spans, pos = [], 0
    for w, s, e in words:
        n = max(1, len(norm(w)))
        spans.append((pos, pos + n, s, e))
        pos += n
    total_w = pos
    total_s = sum(max(1, len(norm(c))) for c in chunks)

    def time_at(charpos, edge):
        for a, b, s, e in spans:
            if charpos < b or (edge == "end" and charpos <= b):
                frac = (charpos - a) / (b - a)
                frac = min(1.0, max(0.0, frac))
                return s + (e - s) * frac
        return spans[-1][3]

    caps, cpos = [], 0
    for c in chunks:
        n = max(1, len(norm(c)))
        a = cpos * total_w / total_s
        b = (cpos + n) * total_w / total_s
        caps.append({"text": c, "start": time_at(a, "start"), "end": time_at(b, "end")})
        cpos += n
    return caps


def tidy(caps, offset):
    # Close tiny gaps so captions do not flicker, and keep each one on screen at least 0.6 s.
    for i, c in enumerate(caps):
        if i + 1 < len(caps):
            nxt = caps[i + 1]["start"]
            if nxt - c["end"] < 0.35:
                c["end"] = nxt
            c["end"] = min(max(c["end"], c["start"] + 0.6), nxt) if nxt > c["start"] else c["end"]
        c["start"] = round(c["start"] + offset, 2)
        c["end"] = round(c["end"] + offset, 2)
    return caps


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--lang", default=None, help="ko, ja, en ... (auto-detect if omitted)")
    ap.add_argument("--script", help="text file with the exact narration")
    ap.add_argument("--max-chars", type=int, help="max characters per caption (default ko 14, ja 12, others 32)")
    ap.add_argument("--model", default="small", help="faster-whisper model: tiny, base, small, medium, large-v3")
    ap.add_argument("--device", default="auto", help="auto, cpu or cuda (auto falls back to cpu if CUDA is broken)")
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--into", help="edit.json whose captions list is replaced")
    ap.add_argument("--out", help="write the captions list to this JSON file")
    args = ap.parse_args(argv)

    max_chars = args.max_chars or DEFAULT_MAX.get(args.lang or "", 32)
    words = load_words(args.audio, args.lang, args.model, args.device)
    if args.script:
        with open(args.script, encoding="utf-8-sig") as f:
            caps = captions_from_script(words, f.read(), max_chars)
    else:
        caps = captions_from_words(words, max_chars)
        print("No --script given: captions use the recognised text. Check names and numbers by hand.")
    caps = tidy(caps, args.offset)

    if args.into:
        with open(args.into, encoding="utf-8-sig") as f:
            edit = json.load(f)
        edit["captions"] = caps
        with open(args.into, "w", encoding="utf-8") as f:
            json.dump(edit, f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(caps)} captions into {args.into}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(caps, f, ensure_ascii=False, indent=2)
    if not args.into and not args.out:
        print(json.dumps(caps, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
