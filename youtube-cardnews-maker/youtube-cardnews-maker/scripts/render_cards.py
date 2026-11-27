# -*- coding: utf-8 -*-
"""Step 4: render card-news PNGs from <work>/cards.json (written by the agent).

Usage:
  python render_cards.py work/my-video
  python render_cards.py work/my-video --theme light --accent "#ff5a36" --brand "My Channel"
  python render_cards.py work/my-video --size 1080x1080 --bg gradient --font path/to/KoreanFont.ttf

Reads : cards.json, meta.json, video.mp4 (optional, frames become card images)
Writes: cards/card_01.png ..., cards/_preview.png (all cards in one sheet), description.txt
Markup: wrap words in **double asterisks** in a title or body to color them with the accent.
Needs : ffmpeg, playwright (pip install playwright) and Chrome/Edge, or `playwright install chromium`.
No API key and no browser login are used.
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

THEMES = {
    "dark": {"panel": "#111318", "text": "#f5f6f8", "sub": "#c9ced6", "muted": "#7d838d", "accent": "#ffcf3f", "dot": "#3a3f48"},
    "light": {"panel": "#f7f5f0", "text": "#15161a", "sub": "#3f434a", "muted": "#8a8d93", "accent": "#ff5a36", "dot": "#d9d5cc"},
}


def font_css(user_font):
    cands = ([Path(user_font)] if user_font else []) + [d / n for d in FONT_DIRS for n in FONT_NAMES]
    for p in cands:
        if p.exists() and p.suffix.lower() in (".ttf", ".otf"):
            data = base64.b64encode(p.read_bytes()).decode("ascii")
            return ("@font-face{font-family:'CardFont';src:url(data:font/ttf;base64," + data +
                    ") format('truetype');font-weight:100 900;}")
    print("[warn] no Korean font file found; relying on system fonts", file=sys.stderr)
    return ""


def rich(text):
    """Escape, then turn **word** into an accent span and newlines into <br>."""
    t = html.escape(text.strip())
    t = re.sub(r"\*\*(.+?)\*\*", r'<span class="hl">\1</span>', t)
    return t.replace("\n", "<br>")


def label_for(role):
    if role == "background":
        return "INTRO"
    if role.startswith("point"):
        n = role.split("_")[-1]
        return f"POINT {int(n):02d}" if n.isdigit() else "POINT"
    return "WRAP-UP" if role == "closing" else ""


def card_html(card, i, total, css, w, h, img_b64, meta, brand, th, accent):
    role = card["role"]
    s = w / 1080  # scale everything from a 1080-wide design
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    channel = html.escape(meta.get("channel", ""))
    img = f"url(data:image/jpeg;base64,{img_b64})" if img_b64 else ""
    dots = "".join(f'<i class="{"on" if k == i else ""}"></i>' for k in range(total))
    base = f"""<style>{css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
body{{font-family:{FONT_STACK};background:{th['panel']};color:{th['text']};position:relative;word-break:keep-all;-webkit-font-smoothing:antialiased}}
.hl{{color:{accent}}}
.dots{{position:absolute;left:{px(72)};bottom:{px(62)};display:flex;gap:{px(10)};align-items:center}}
.dots i{{width:{px(12)};height:{px(12)};border-radius:50%;background:{th['dot']}}}
.dots i.on{{background:{accent};width:{px(38)};border-radius:{px(6)}}}
.foot{{position:absolute;right:{px(72)};bottom:{px(54)};font-size:{px(26)};color:{th['muted']};font-weight:700;letter-spacing:.04em}}
</style>"""

    if role == "cover":
        bg = (f"linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 40%,rgba(0,0,0,.6) 64%,rgba(0,0,0,.94) 100%),{img} center/cover"
              if img else f"radial-gradient(120% 90% at 20% 10%,{accent}40 0%,{th['panel']} 62%)")
        brand_html = f'<div class="brand">{html.escape(brand)}</div>' if brand else ""
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
body{{background:{bg};color:#fff}}
.frame{{position:absolute;inset:{px(28)};border:{px(2)} solid rgba(255,255,255,.28);border-radius:{px(34)}}}
.top{{position:absolute;left:{px(72)};right:{px(72)};top:{px(70)};display:flex;justify-content:space-between;align-items:center}}
.kick{{font-size:{px(28)};font-weight:900;letter-spacing:.12em;color:#111;background:{accent};padding:{px(10)} {px(22)};border-radius:{px(10)}}}
.brand{{font-size:{px(28)};font-weight:800;padding:{px(10)} {px(24)};border-radius:999px;background:rgba(0,0,0,.42);color:#fff}}
.wrap{{position:absolute;left:{px(72)};right:{px(72)};bottom:{px(160)}}}
h1{{font-size:{px(100)};font-weight:900;line-height:1.14;letter-spacing:-.04em;text-shadow:0 4px 34px rgba(0,0,0,.5)}}
h1 .hl{{color:#111;background:{accent};padding:0 {px(10)};border-radius:{px(10)};box-decoration-break:clone;-webkit-box-decoration-break:clone;text-shadow:none}}
.line{{width:{px(90)};height:{px(8)};background:{accent};border-radius:{px(4)};margin:{px(36)} 0 {px(28)}}}
p{{font-size:{px(42)};font-weight:700;line-height:1.45;color:rgba(255,255,255,.92)}}
.src{{position:absolute;left:{px(72)};bottom:{px(66)};font-size:{px(26)};color:rgba(255,255,255,.78);font-weight:700}}
.swipe{{position:absolute;right:{px(72)};bottom:{px(56)};font-size:{px(28)};font-weight:900;color:#111;background:#fff;padding:{px(10)} {px(24)};border-radius:999px}}
</style></head><body><div class="frame"></div><div class="top"><div class="kick">한눈에 요약</div>{brand_html}</div>
<div class="wrap"><h1>{rich(card['title'])}</h1><div class="line"></div><p>{rich(card['body'])}</p></div>
<div class="src">출처 · {channel}</div><div class="swipe">넘겨 보기 →</div></body></html>"""

    tall = h / w > 1.15
    img_h = int(h * (0.43 if tall else 0.34))
    num = role.split("_")[-1] if role.startswith("point") else ""
    big_num = f'<div class="num">{int(num):02d}</div>' if num.isdigit() else ""
    media = (f'<div class="media" style="background:{img} center/cover"></div>' if img
             else f'<div class="media" style="background:radial-gradient(110% 120% at 85% 0%,{accent}55 0%,{th["panel"]} 72%)"></div>')
    cta = (f'<div class="cta">▶ 원본 영상 보기 · {channel}</div>' if role == "closing" and channel else "")
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.media{{position:absolute;left:{px(48)};right:{px(48)};top:{px(48)};height:{img_h}px;border-radius:{px(30)};box-shadow:0 {px(18)} {px(44)} rgba(0,0,0,.35)}}
.num{{position:absolute;right:{px(56)};top:{img_h + int(58 * s)}px;font-size:{px(210)};font-weight:900;line-height:1;letter-spacing:-.06em;color:{accent};opacity:.13}}
.wrap{{position:absolute;left:{px(72)};right:{px(72)};top:{img_h + int(48 * s)}px;bottom:{px(118)};display:flex;flex-direction:column;justify-content:center;overflow:hidden}}
.lab{{align-self:flex-start;font-size:{px(26)};font-weight:900;letter-spacing:.14em;color:#111;background:{accent};padding:{px(8)} {px(18)};border-radius:{px(8)};margin-bottom:{px(26)}}}
h1{{font-size:{px(74)};font-weight:900;line-height:1.22;letter-spacing:-.035em;margin-bottom:{px(26)}}}
h1 .hl{{color:{th['text']};background:linear-gradient(180deg,transparent 58%,{accent}88 58%)}}
.bar{{width:{px(64)};height:{px(6)};border-radius:{px(3)};background:{accent};margin-bottom:{px(26)}}}
p{{font-size:{px(42)};font-weight:500;line-height:1.62;color:{th['sub']}}}
p .hl{{color:{accent};font-weight:800}}
.cta{{align-self:flex-start;margin-top:{px(36)};font-size:{px(32)};font-weight:900;color:#111;background:{accent};padding:{px(16)} {px(30)};border-radius:999px}}
</style></head><body>{media}{big_num}<div class="wrap"><div class="lab">{label_for(role)}</div><h1>{rich(card['title'])}</h1><div class="bar"></div><p>{rich(card['body'])}</p>{cta}</div>
<div class="dots">{dots}</div><div class="foot">{i + 1} / {total}</div></body></html>"""


def grab_frames(work: Path, cards, duration):
    """One frame per card from video.mp4 (card['time'] seconds if given, else evenly spaced)."""
    if not (work / "video.mp4").exists() or shutil.which("ffmpeg") is None or duration <= 0:
        return [None] * len(cards)
    (work / "frames").mkdir(exist_ok=True)
    out = []
    for i, c in enumerate(cards):
        t = c.get("time")
        if not isinstance(t, (int, float)) or not 0 <= t <= duration:
            t = duration * (i + 0.5) / len(cards)
        name = f"frames/frame_{i + 1:02d}.jpg"
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", "video.mp4", "-frames:v", "1", "-q:v", "2", name],
                           cwd=str(work), capture_output=True, encoding="utf-8", errors="replace")
        out.append(work / name if r.returncode == 0 and (work / name).exists() else None)
    return out


def launch(p):
    last = None
    for kw in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            last = e
    sys.exit(f"No browser could be started ({last}). Install Chrome or run: playwright install chromium")


def contact_sheet(work: Path, n: int, w: int, h: int):
    """All cards side by side at small size, for a one-glance review."""
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    tw = 360
    th_ = int(h * tw / w)
    inputs, chains = [], []
    for k in range(cols * rows):
        src = f"cards/card_{k + 1:02d}.png" if k < n else None
        if src:
            inputs += ["-i", src]
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c=black:s={tw}x{th_}:d=1"]
        chains.append(f"[{k}:v]scale={tw}:{th_}[v{k}]")
    layout = "|".join(f"{(k % cols) * tw}_{(k // cols) * th_}" for k in range(cols * rows))
    fc = ";".join(chains) + ";" + "".join(f"[v{k}]" for k in range(cols * rows)) + f"xstack=inputs={cols * rows}:layout={layout}"
    if cols * rows == 1:
        fc = chains[0].replace("[v0]", "")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-frames:v", "1", "cards/_preview.png"],
                   cwd=str(work), capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--size", default="1080x1350")
    ap.add_argument("--bg", choices=["video", "gradient"], default="video")
    ap.add_argument("--theme", choices=list(THEMES), default="dark")
    ap.add_argument("--accent", default="", help="accent color, e.g. #ffcf3f")
    ap.add_argument("--brand", default="", help="small label at the top of the cover (optional)")
    ap.add_argument("--font", default="", help="Korean .ttf/.otf file (optional)")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    work = Path(a.work)
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    meta = json.loads((work / "meta.json").read_text(encoding="utf-8")) if (work / "meta.json").exists() else {}
    cards = data["cards"]
    roles = [c["role"] for c in cards]
    if "cover" not in roles or "closing" not in roles:
        sys.exit(f"cards.json needs a cover and a closing card (got {roles})")
    w, h = (int(x) for x in a.size.lower().split("x"))
    th = THEMES[a.theme]
    accent = a.accent or th["accent"]

    frames = grab_frames(work, cards, float(meta.get("duration", 0))) if a.bg == "video" else [None] * len(cards)
    css = font_css(a.font)
    out = work / "cards"
    out.mkdir(exist_ok=True)
    for old in out.glob("card_*.png"):
        old.unlink()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": w, "height": h})
        for i, c in enumerate(cards):
            fb = base64.b64encode(frames[i].read_bytes()).decode("ascii") if frames[i] else ""
            page.set_content(card_html(c, i, len(cards), css, w, h, fb, meta, a.brand, th, accent))
            page.evaluate("document.fonts.ready")
            # flag text that runs off the card
            over = page.evaluate("""() => { const w = document.querySelector('.wrap'); if (!w) return false;
                const r = w.getBoundingClientRect(); return w.scrollHeight > w.clientHeight + 2 || r.bottom > innerHeight - 40; }""")
            if over:
                print(f"[warn] card {i + 1} ({c['role']}): text is too long for the card - shorten it", file=sys.stderr)
            page.screenshot(path=str(out / f"card_{i + 1:02d}.png"))
        browser.close()
    contact_sheet(work, len(cards), w, h)

    lines = [data.get("description", "").strip(), "",
             f"출처: {meta.get('channel', '')} - {meta.get('title', '')}", meta.get("url", ""), "",
             "[추천 첫 댓글]", data.get("first_comment", "").strip()]
    (work / "description.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(cards)} cards -> {out}")
    print(f"review sheet -> {out / '_preview.png'}")
    print(f"caption      -> {work / 'description.txt'}")


if __name__ == "__main__":
    main()
