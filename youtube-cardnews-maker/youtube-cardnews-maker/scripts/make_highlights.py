# -*- coding: utf-8 -*-
"""Step 7: cut highlight clips (9:16) with Korean subtitles from <work>/cards.json.

Usage:
  python make_highlights.py work/my-video
  python make_highlights.py work/my-video --show-original --brand "My Channel" --accent "#ffcf3f"

cards.json -> "highlights": [
  {"start": 312.0, "end": 326.5, "title": "short Korean clip title",
   "subs": [{"start": 312.0, "end": 316.2, "ko": "한글 자막", "orig": "original line (optional)"}]}
]
All times are absolute seconds in the source video. For Korean-language videos put the original
speech in "ko". For foreign videos the agent translates each line into natural Korean ("ko").
Wrap a key word in **double asterisks** to color it with the accent.

Writes highlights/highlight_01.mp4, highlight_01.ko.srt and _preview_01.png (3 frames).
Layout: clean dark 1080x1920 frame, HIGHLIGHT pill + title + source on top, the video in a
rounded window with a thin progress bar, Korean subtitles under it. Text is drawn with HTML
(same fonts as the cards) and laid over the video with ffmpeg. Needs ffmpeg + playwright (free).
"""
import argparse
import base64
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
             Path("/usr/share/fonts/truetype/noto"), Path("/usr/share/fonts/opentype/noto")]
FONT_NAMES = ["NotoSansKR-VF.ttf", "Pretendard-Variable.ttf", "PretendardVariable.ttf", "NotoSansKR-Regular.otf",
              "malgunbd.ttf", "malgun.ttf", "NanumGothic.ttf"]
FONT_STACK = "'CardFont','Pretendard','Malgun Gothic','Apple SD Gothic Neo','Noto Sans CJK KR','Noto Sans KR',sans-serif"
BG = "#0e0f12"
W, H = 1080, 1920
VX, VY, VW, VH = 40, 600, 1000, 562  # video window (16:9)
SUB_Y = VY + VH + 46


def font_css(user_font):
    cands = ([Path(user_font)] if user_font else []) + [d / n for d in FONT_DIRS for n in FONT_NAMES]
    for p in cands:
        if p.exists() and p.suffix.lower() in (".ttf", ".otf"):
            data = base64.b64encode(p.read_bytes()).decode("ascii")
            return ("@font-face{font-family:'CardFont';src:url(data:font/ttf;base64," + data +
                    ") format('truetype');font-weight:100 900;}")
    print("[warn] no Korean font file found; relying on system fonts", file=sys.stderr)
    return ""


def rich(text, accent):
    t = html.escape(" ".join(str(text).split()))
    return re.sub(r"\*\*(.+?)\*\*", rf'<span style="color:{accent}">\1</span>', t)


def plain(text):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", " ".join(str(text).split()))


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def page_html(css, body):
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{css}*{{margin:0;padding:0;box-sizing:border-box}}"
            f"html,body{{width:{W}px;background:transparent;font-family:{FONT_STACK};word-break:keep-all;-webkit-font-smoothing:antialiased}}"
            f"</style></head><body>{body}</body></html>")


def frame_html(css, idx, title, channel, brand, accent):
    """Full-frame overlay: dark background with a rounded transparent window where the video shows."""
    brand_html = (f'<div style="position:absolute;left:0;right:0;top:1760px;text-align:center;font-size:40px;font-weight:800;color:#fff">'
                  f'{html.escape(brand)}</div>') if brand else ""
    body = f"""<div style="position:relative;width:{W}px;height:{H}px;overflow:hidden">
<div style="position:absolute;left:{VX}px;top:{VY}px;width:{VW}px;height:{VH}px;border-radius:34px;box-shadow:0 0 0 2400px {BG}"></div>
<div style="position:absolute;left:-200px;right:-200px;top:-420px;height:900px;background:radial-gradient(closest-side,{accent}33,transparent)"></div>
<div style="position:absolute;left:{VX}px;top:{VY}px;width:{VW}px;height:{VH}px;border-radius:34px;box-shadow:inset 0 0 0 2px rgba(255,255,255,.10)"></div>
<div style="position:absolute;left:80px;right:80px;top:0;height:{VY - 50}px;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;text-align:center">
 <div style="font-size:28px;font-weight:900;letter-spacing:.16em;color:#111;background:{accent};padding:10px 22px;border-radius:999px;margin-bottom:30px">HIGHLIGHT {idx:02d}</div>
 <div style="font-size:74px;font-weight:900;line-height:1.18;letter-spacing:-.035em;color:#fff">{rich(title, accent)}</div>
 <div style="margin-top:26px;font-size:30px;font-weight:600;color:rgba(255,255,255,.55)">출처 · {html.escape(channel)}</div>
</div>{brand_html}</div>"""
    return page_html(css, body)


def sub_html(css, ko, orig, accent):
    o = (f'<div style="font-size:28px;font-weight:500;color:rgba(255,255,255,.55);margin-bottom:16px">{html.escape(plain(orig))}</div>'
         if orig else "")
    body = f"""<div style="width:{W}px;height:420px;padding:0 70px;text-align:center">{o}
<div style="font-size:{60 if len(plain(ko)) <= 30 else 50}px;font-weight:800;line-height:1.32;letter-spacing:-.02em;color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.5)">{rich(ko, accent)}</div></div>"""
    return page_html(css, body)


def launch(p):
    last = None
    for kw in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            last = e
    sys.exit(f"No browser could be started ({last}). Install Chrome or run: playwright install chromium")


def build(work: Path, idx: int, hl: dict, meta: dict, page, css, brand: str, show_orig: bool, accent: str):
    start, end = float(hl["start"]), float(hl["end"])
    dur = end - start
    if not 3 <= dur <= 90:
        sys.exit(f"highlight {idx}: length {dur:.1f}s is outside 3-90s")
    tmp = work / "_hl_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    out_dir = work / "highlights"
    out_dir.mkdir(exist_ok=True)

    page.set_viewport_size({"width": W, "height": H})
    page.set_content(frame_html(css, idx, hl.get("title") or meta.get("title", ""), meta.get("channel", ""), brand, accent))
    page.evaluate("document.fonts.ready")
    page.screenshot(path=str(tmp / "frame.png"), omit_background=True)

    subs, srt = [], []
    page.set_viewport_size({"width": W, "height": 420})
    for s in hl.get("subs", []):
        ko = " ".join(str(s.get("ko", "")).split())
        if not ko:
            continue
        a, b = max(0.0, float(s["start"]) - start), min(dur, float(s["end"]) - start)
        if b - a < 0.2:
            continue
        if len(plain(ko)) > 40:
            print(f"[warn] highlight {idx} subtitle {len(subs) + 1} is long ({len(plain(ko))} chars); shorten it", file=sys.stderr)
        name = f"sub{len(subs) + 1:03d}.png"
        page.set_content(sub_html(css, ko, s.get("orig") if show_orig else "", accent))
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(tmp / name), omit_background=True)
        subs.append((name, a, b))
        srt.append(f"{len(srt) + 1}\n{srt_time(a)} --> {srt_time(b)}\n{plain(ko)}\n")

    # graph: video in its window + progress bar along its bottom edge, frame overlay, timed subtitle images
    inputs = ["-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", "../video.mp4", "-i", "frame.png"]
    for name, _, _ in subs:
        inputs += ["-i", name]
    g = [f"[0:v]scale={VW}:{VH}:force_original_aspect_ratio=decrease,pad={VW}:{VH}:(ow-iw)/2:(oh-ih)/2:color={BG},setsar=1[vid]",
         f"color=c={accent}:s={VW}x8:d={dur:.2f}[pb]",
         f"[vid][pb]overlay=x='-w+w*t/{dur:.2f}':y=H-8:shortest=1[vidp]",
         f"color=c={BG}:s={W}x{H}:d={dur:.2f}[bg]",
         f"[bg][vidp]overlay={VX}:{VY}:shortest=1[b0]",
         "[b0][1:v]overlay=0:0[b1]"]
    last = "b1"
    for k, (_, a, b) in enumerate(subs):
        g.append(f"[{last}][{k + 2}:v]overlay=0:{SUB_Y}:enable='between(t,{a:.2f},{b:.2f})'[s{k}]")
        last = f"s{k}"
    name = f"highlight_{idx:02d}"
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(g), "-map", f"[{last}]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-movflags", "+faststart", "-t", f"{dur:.2f}", f"../highlights/{name}.mp4"]
    try:
        r = subprocess.run(cmd, cwd=str(tmp), capture_output=True, encoding="utf-8", errors="replace")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        sys.exit(f"ffmpeg failed on highlight {idx}")
    (out_dir / f"{name}.ko.srt").write_text("\n".join(srt), encoding="utf-8")

    for k, t in enumerate(dur * f for f in (0.15, 0.5, 0.85)):  # review sheet: 3 frames
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", f"{name}.mp4", "-frames:v", "1",
                        "-vf", "scale=360:-1", f"_p{k}.png"], cwd=str(out_dir), capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "_p0.png", "-i", "_p1.png", "-i", "_p2.png",
                    "-filter_complex", "hstack=inputs=3", f"_preview_{idx:02d}.png"], cwd=str(out_dir), capture_output=True)
    for k in range(3):
        (out_dir / f"_p{k}.png").unlink(missing_ok=True)
    return out_dir / f"{name}.mp4", len(subs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--brand", default="", help="bottom text (optional)")
    ap.add_argument("--font", default="", help="Korean .ttf/.otf (optional; Windows/macOS/Noto fonts are auto-found)")
    ap.add_argument("--accent", default="#ffcf3f", help="color of the HIGHLIGHT pill, key words and progress bar")
    ap.add_argument("--show-original", action="store_true", help="also show the original-language line above the Korean subtitle")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    work = Path(a.work)
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found")
    if not (work / "video.mp4").exists():
        sys.exit("video.mp4 is missing - run fetch.py without --no-video")
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    meta = json.loads((work / "meta.json").read_text(encoding="utf-8")) if (work / "meta.json").exists() else {}
    hls = data.get("highlights") or []
    if not hls:
        sys.exit('cards.json has no "highlights"')
    spans = sorted((float(h["start"]), float(h["end"])) for h in hls)
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        if s2 < e1:
            print("[warn] highlight ranges overlap", file=sys.stderr)
    css = font_css(a.font)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page()
        for i, h in enumerate(hls, 1):
            path, n = build(work, i, h, meta, page, css, a.brand, a.show_original, a.accent)
            print(f"highlight {i}: {path}  ({n} subtitle lines)  review: {path.parent / f'_preview_{i:02d}.png'}")
        browser.close()


if __name__ == "__main__":
    main()
