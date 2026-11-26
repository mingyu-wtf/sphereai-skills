# -*- coding: utf-8 -*-
"""Render Instagram carousel cards (card news) from <work>/cards.json.

Usage:
  python render_cards.py work/my-topic
  python render_cards.py work/my-topic --style dark --accent "#7cf0b5" --size 1080x1080

Reads : cards.json (written by the agent), images referenced by cards (optional)
Writes: cards/card_01.png ..., cards/_preview.png (all cards on one sheet), caption.txt
Markup: **word** colors a word with the accent; a new line in text is kept.
Needs : pip install playwright, plus Chrome/Edge (or `playwright install chromium`). ffmpeg only for the preview sheet.
No API key and no login are used.
"""
import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from pathlib import Path

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental"),
             Path("/usr/share/fonts/truetype/noto"), Path("/usr/share/fonts/opentype/noto")]
FONT_NAMES = ["Pretendard-Variable.ttf", "PretendardVariable.ttf", "NotoSansKR-VF.ttf", "NotoSansKR-Regular.otf",
              "malgunbd.ttf", "malgun.ttf", "NanumGothic.ttf", "AppleSDGothicNeo.ttc"]
FONT_STACK = "'CardFont','Pretendard','Malgun Gothic','Apple SD Gothic Neo','Noto Sans CJK KR','Noto Sans KR',sans-serif"

# bg, panel (boxes), text, sub, muted, accent, marker text color (text drawn on top of the accent)
STYLES = {
    "bold":   {"bg": "#ffffff", "panel": "#f2f2f0", "text": "#111111", "sub": "#3d3d3d", "muted": "#8b8b8b", "accent": "#ffe14d", "on": "#111111", "line": "#111111"},
    "dark":   {"bg": "#111317", "panel": "#1c1f25", "text": "#f6f7f9", "sub": "#c7ccd4", "muted": "#7b818b", "accent": "#ffcf3f", "on": "#111111", "line": "#f6f7f9", "mark": "text"},
    "pastel": {"bg": "#f5efe6", "panel": "#ebe2d4", "text": "#1f1c18", "sub": "#4a443c", "muted": "#958c80", "accent": "#ff6b4a", "on": "#ffffff", "line": "#1f1c18"},
    "photo":  {"bg": "#fbfaf7", "panel": "#efede8", "text": "#15161a", "sub": "#3f434a", "muted": "#8a8d93", "accent": "#3d6bff", "on": "#ffffff", "line": "#15161a", "mark": "text"},
}

LIMITS = {  # (title, body) hard caps in characters, markers excluded - mirrored in check.py
    "cover": (26, 40), "text": (22, 120), "list": (22, 100), "stat": (22, 80),
    "compare": (22, 0), "checklist": (22, 0), "quote": (0, 90), "closing": (22, 70),
    "product": (30, 0), "table": (14, 0),
}


PAPERLOGY = {500: "Paperlogy-5Medium.ttf", 700: "Paperlogy-7Bold.ttf", 800: "Paperlogy-8ExtraBold.ttf", 900: "Paperlogy-9Black.ttf"}


def paperlogy_css(extra_dir=""):
    """Paperlogy (free Korean font, one file per weight) - used when installed or given with --font-dir."""
    import os
    dirs = ([Path(extra_dir)] if extra_dir else []) + FONT_DIRS + [Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
                                                                 Path.home() / "Library/Fonts", Path.home() / ".fonts"]
    out = ""
    for wgt, name in PAPERLOGY.items():
        f = next((d / name for d in dirs if (d / name).exists()), None)
        if f:
            out += ("@font-face{font-family:'CardFont';font-weight:%d;src:url(data:font/ttf;base64,%s) format('truetype');}"
                    % (wgt, base64.b64encode(f.read_bytes()).decode("ascii")))
    return out


def font_css(user_font, font_dir=""):
    if not user_font:
        pl = paperlogy_css(font_dir)
        if pl:
            return pl
    cands = ([Path(user_font)] if user_font else []) + [d / n for d in FONT_DIRS for n in FONT_NAMES]
    for p in cands:
        if p.exists() and p.suffix.lower() in (".ttf", ".otf"):
            data = base64.b64encode(p.read_bytes()).decode("ascii")
            return ("@font-face{font-family:'CardFont';src:url(data:font/ttf;base64," + data +
                    ") format('truetype');font-weight:100 900;}")
    print("[warn] no Korean font file found; relying on system fonts", file=sys.stderr)
    return ""


def rich(text):
    t = html.escape(str(text or "").strip())
    t = re.sub(r"\*\*(.+?)\*\*", r'<span class="hl">\1</span>', t)
    return t.replace("\n", "<br>")


def img_url(work: Path, rel):
    if not rel:
        return ""
    p = (work / rel) if not Path(rel).is_absolute() else Path(rel)
    if not p.exists():
        print(f"[warn] image not found: {rel}", file=sys.stderr)
        return ""
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"url(data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')})"


def image_size(work: Path, rel):
    """(w, h) of a card image, or None. Uses Pillow when installed, else reads PNG/JPEG headers."""
    if not rel:
        return None
    p = (work / rel) if not Path(rel).is_absolute() else Path(rel)
    if not p.exists():
        return None
    try:
        from PIL import Image
        with Image.open(p) as im:
            return im.size
    except Exception:  # noqa: BLE001
        pass
    b = p.read_bytes()
    if b[:8] == bytes.fromhex("89504e470d0a1a0a"):
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    i = 2
    while i < len(b) - 9 and b[:2] == bytes.fromhex("ffd8"):
        if b[i] != 0xFF:
            break
        m, ln = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
        if m in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
        i += 2 + ln
    return None


def chrome(st, accent, i, total, handle, s, dark_over=False):
    """Shared top bar (handle + page count), progress bar and swipe hint."""
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    col = "#ffffff" if dark_over else st["muted"]
    track = "rgba(255,255,255,.25)" if dark_over else st["panel"]
    swipe = "" if i == total - 1 else f'<div class="sw" style="color:{"#fff" if dark_over else st["text"]}">→</div>'
    hd = f'<div class="hd" style="color:{col}">{html.escape(handle)}</div>' if handle else ""
    return f"""{hd}<div class="pg" style="color:{col}">{i + 1}/{total}</div>{swipe}
<div class="pr" style="background:{track}"><i style="width:{(i + 1) / total * 100:.2f}%;background:{accent}"></i></div>
<style>.hd{{position:absolute;left:{px(72)};top:{px(58)};font-size:{px(28)};font-weight:800;letter-spacing:-.01em}}
.pg{{position:absolute;right:{px(72)};top:{px(58)};font-size:{px(28)};font-weight:800}}
.sw{{position:absolute;right:{px(66)};bottom:{px(64)};font-size:{px(56)};font-weight:900;line-height:1}}
.pr{{position:absolute;left:{px(72)};right:{px(150)};bottom:{px(86)};height:{px(6)};border-radius:{px(3)};overflow:hidden}}
.pr i{{display:block;height:100%;border-radius:{px(3)}}}</style>"""


def card_html(c, i, total, work, css, w, h, st, accent, handle, sources, mode="full", scrim=0.62, extra_css=""):
    """mode full: the card's image fills the background and the text sits on a dark scrim on top of it."""
    full = mode == "full" and bool(c.get("image")) and c.get("type") != "cover"
    out = _card_html(c, i, total, work, css, w, h, st, accent, handle, sources, full)
    if full:
        out = out.replace("</head>", overlay_css(img_url(work, c.get("image")), st, accent, w / 1080, scrim) + "</head>", 1)
    if extra_css:
        out = out.replace("</head>", "<style>" + extra_css + "</style></head>", 1)
    return out


def overlay_css(img, st, accent, s, scrim):
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    a1, a2 = max(0.0, scrim - 0.12), min(0.95, scrim + 0.18)
    return f"""<style>
body{{background:linear-gradient(180deg,rgba(0,0,0,{a1:.2f}) 0%,rgba(0,0,0,{scrim:.2f}) 45%,rgba(0,0,0,{a2:.2f}) 100%),{img} center/cover!important;color:#fff!important}}
h1,h2,.q,.ct,.ch{{color:#fff!important;text-shadow:0 {px(3)} {px(24)} rgba(0,0,0,.45)}}
p,.lb,.by,.src{{color:rgba(255,255,255,.88)!important}}
.hl{{background:{accent}!important;color:{st['on']}!important;padding:0 {px(8)};border-radius:{px(6)};box-decoration-break:clone;-webkit-box-decoration-break:clone;text-shadow:none}}
.num{{-webkit-text-stroke:0!important;color:{accent}!important}}
.v{{color:{accent}!important;text-shadow:0 {px(3)} {px(30)} rgba(0,0,0,.4)}}.v span{{background:none!important}}
.qm{{color:{accent}!important}}
.col,.box{{background:rgba(255,255,255,.14)!important;-webkit-backdrop-filter:blur({px(12)});backdrop-filter:blur({px(12)});color:#fff}}
.col.on{{background:{accent}!important;color:{st['on']}!important}}
li{{border-color:rgba(255,255,255,.22)!important}}
.b{{border-color:#fff!important;color:#fff}}.b.on{{color:{st['on']}!important;border-color:{accent}!important}}
.deco,.rule{{display:none}}
</style>"""


def _card_html(c, i, total, work, css, w, h, st, accent, handle, sources, full=False):
    s = w / 1080
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    t = c.get("type", "text")
    base = f"""<style>{css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
body{{font-family:{FONT_STACK};background:{st['bg']};color:{st['text']};position:relative;word-break:keep-all;overflow-wrap:anywhere;-webkit-font-smoothing:antialiased}}
.hl{{{"color:" + accent if st.get("mark") == "text" else "background:linear-gradient(180deg,transparent 56%," + accent + " 56%);padding:0 " + px(4)}}}
.wrap{{position:absolute;left:{px(72)};right:{px(72)};top:{px(140)};bottom:{px(140)};display:flex;flex-direction:column;justify-content:center;overflow:hidden}}
.kick{{align-self:flex-start;font-size:{px(30)};font-weight:900;color:{st['on']};background:{accent};padding:{px(10)} {px(22)};border-radius:{px(10)};margin-bottom:{px(34)}}}
h1{{font-size:{px(84)};font-weight:900;line-height:1.2;letter-spacing:-.04em}}
h2{{font-size:{px(70)};font-weight:900;line-height:1.24;letter-spacing:-.035em;margin-bottom:{px(34)}}}
p{{font-size:{px(44)};font-weight:500;line-height:1.6;color:{st['sub']}}}
p .hl{{color:{accent if st.get("mark") == "text" else st['text']};font-weight:800}}
.media{{width:100%;border-radius:{px(28)};background-size:cover;background-position:center;margin-bottom:{px(40)};flex:none}}
</style>"""
    img = img_url(work, c.get("image"))
    bar = chrome(st, accent, i, total, handle, s, full)

    if t == "cover":
        kick = f'<div class="kick">{rich(c["kicker"])}</div>' if c.get("kicker") else ""
        sub = f'<p class="cs">{rich(c.get("sub", ""))}</p>' if c.get("sub") else ""
        if img:
            return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
body{{background:linear-gradient(180deg,rgba(0,0,0,.42) 0%,rgba(0,0,0,0) 26%,rgba(0,0,0,0) 42%,rgba(0,0,0,.7) 70%,rgba(0,0,0,.92) 100%),{img} center/cover;color:#fff}}
.wrap{{top:auto;bottom:{px(150)};justify-content:flex-end}}
h1{{font-size:{px(96)};text-shadow:0 {px(4)} {px(30)} rgba(0,0,0,.45)}}
h1 .hl{{background:{accent};color:{st['on']};padding:0 {px(10)};border-radius:{px(8)};box-decoration-break:clone;-webkit-box-decoration-break:clone;text-shadow:none}}
.cs{{color:rgba(255,255,255,.9);font-weight:700;margin-top:{px(30)}}}
</style></head><body>{chrome(st, accent, i, total, handle, s, True)}<div class="wrap">{kick}<h1>{rich(c.get('title'))}</h1>{sub}</div></body></html>"""
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
h1{{font-size:{px(104)};line-height:1.16}}
.cs{{margin-top:{px(40)};font-weight:700}}
.deco{{position:absolute;right:{px(-140)};bottom:{px(-140)};width:{px(560)};height:{px(560)};border-radius:50%;background:{accent};opacity:.9}}
.rule{{width:{px(120)};height:{px(12)};background:{st['line']};margin-top:{px(44)}}}
</style></head><body><div class="deco"></div>{bar}<div class="wrap">{kick}<h1>{rich(c.get('title'))}</h1><div class="rule"></div>{sub}</div></body></html>"""

    if t in ("text", "list"):
        num = c.get("num")
        big = (f'<div class="num">{int(num):02d}</div>' if str(num).isdigit() else "") if t == "list" else ""
        media = f'<div class="media" style="height:{int(h * .3)}px;background-image:{img}"></div>' if img and not full else ""
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.num{{font-size:{px(150)};font-weight:900;line-height:.9;letter-spacing:-.06em;color:{accent};-webkit-text-stroke:{px(3)} {st['line']};margin-bottom:{px(26)}}}
</style></head><body>{bar}<div class="wrap">{media}{big}<h2>{rich(c.get('title'))}</h2><p>{rich(c.get('body'))}</p></div></body></html>"""

    if t == "stat":
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.v{{font-size:{px(220)};font-weight:900;line-height:1.08;letter-spacing:-.06em;margin-bottom:{px(30)};color:{accent if st.get("mark") == "text" else st['text']}}}
.v span{{{"" if st.get("mark") == "text" else "background:linear-gradient(180deg,transparent 66%," + accent + " 66%)"}}}
.lb{{font-size:{px(40)};font-weight:800;color:{st['muted']};margin-bottom:{px(50)}}}
</style></head><body>{bar}<div class="wrap"><div class="v"><span>{html.escape(str(c.get('value', '')))}</span></div>
<div class="lb">{rich(c.get('label', ''))}</div><h2>{rich(c.get('title'))}</h2><p>{rich(c.get('body'))}</p></div></body></html>"""

    if t == "compare":
        def col(side, on):
            items = "".join(f"<li>{rich(x)}</li>" for x in side.get("items", []))
            return f'<div class="col{" on" if on else ""}"><div class="ch">{rich(side.get("head", ""))}</div><ul>{items}</ul></div>'
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.cols{{display:flex;gap:{px(24)}}}
.col{{flex:1;background:{st['panel']};border-radius:{px(26)};padding:{px(36)} {px(30)}}}
.col.on{{background:{accent};color:{st['on']}}}
.ch{{font-size:{px(44)};font-weight:900;margin-bottom:{px(24)};letter-spacing:-.03em}}
ul{{list-style:none}}
li{{font-size:{px(36)};font-weight:600;line-height:1.45;padding:{px(14)} 0;border-top:{px(2)} solid rgba(127,127,127,.25)}}
.col.on li{{border-top-color:rgba(0,0,0,.15)}}
</style></head><body>{bar}<div class="wrap"><h2>{rich(c.get('title'))}</h2>
<div class="cols">{col(c.get('left', {}), False)}{col(c.get('right', {}), True)}</div></div></body></html>"""

    if t == "checklist":
        items = "".join(f'<li><b></b><span>{rich(x)}</span></li>' for x in c.get("items", []))
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
ul{{list-style:none}}
li{{display:flex;gap:{px(26)};align-items:flex-start;font-size:{px(42)};font-weight:700;line-height:1.4;padding:{px(22)} 0;border-bottom:{px(2)} solid {st['panel']}}}
li b{{flex:none;width:{px(52)};height:{px(52)};border-radius:{px(14)};background:{accent};position:relative;margin-top:{px(2)}}}
li b:after{{content:"";position:absolute;left:{px(17)};top:{px(7)};width:{px(14)};height:{px(26)};border:solid {st['on']};border-width:0 {px(6)} {px(6)} 0;transform:rotate(45deg)}}
</style></head><body>{bar}<div class="wrap"><h2>{rich(c.get('title'))}</h2><ul>{items}</ul></div></body></html>"""

    if t == "quote":
        by = f'<div class="by">— {rich(c.get("by"))}</div>' if c.get("by") else ""
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.qm{{font-size:{px(240)};font-weight:900;line-height:.7;color:{accent};height:{px(130)}}}
.q{{font-size:{px(64)};font-weight:800;line-height:1.42;letter-spacing:-.03em}}
.by{{margin-top:{px(40)};font-size:{px(36)};font-weight:700;color:{st['muted']}}}
</style></head><body>{bar}<div class="wrap"><div class="qm">“</div><div class="q">{rich(c.get('quote'))}</div>{by}</div></body></html>"""

    if t == "closing":
        cta = c.get("cta") or "저장해 두고 필요할 때 꺼내 보기"
        src = ""
        if sources:
            names = " · ".join(html.escape(x.get("name", "")) for x in sources if x.get("name"))
            src = f'<div class="src">출처 · {names}</div>' if names else ""
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>{base}<style>
.box{{background:{st['panel']};border-radius:{px(30)};padding:{px(44)} {px(40)};margin-top:{px(46)}}}
.row{{display:flex;gap:{px(18)};margin-top:{px(26)}}}
.b{{font-size:{px(32)};font-weight:900;padding:{px(14)} {px(26)};border-radius:999px;border:{px(3)} solid {st['line']}}}
.b.on{{background:{accent};color:{st['on']};border-color:{accent}}}
.ct{{font-size:{px(40)};font-weight:800;line-height:1.4}}
.src{{position:absolute;left:{px(72)};right:{px(72)};bottom:{px(110)};font-size:{px(24)};color:{st['muted']};font-weight:600}}
</style></head><body>{bar}<div class="wrap"><h2>{rich(c.get('title'))}</h2><p>{rich(c.get('body'))}</p>
<div class="box"><div class="ct">{rich(cta)}</div><div class="row"><span class="b on">저장</span><span class="b">공유</span><span class="b">팔로우</span></div></div></div>{src}</body></html>"""

    sys.exit(f"card {i + 1}: unknown type '{t}' (cover/text/list/stat/compare/checklist/quote/closing)")


def launch(p):
    last = None
    for kw in ({"channel": "chrome"}, {"channel": "msedge"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    sys.exit(f"No browser could be started ({last}). Install Chrome or run: playwright install chromium")


def contact_sheet(work: Path, n: int, w: int, h: int):
    if shutil.which("ffmpeg") is None:
        print("[info] ffmpeg not found - skipping _preview.png (open the cards one by one)")
        return
    cols = min(n, 5)
    rows = (n + cols - 1) // cols
    tw, th_ = 360, int(h * 360 / w)
    inputs, chains = [], []
    for k in range(cols * rows):
        if k < n:
            inputs += ["-i", f"cards/card_{k + 1:02d}.png"]
        else:
            inputs += ["-f", "lavfi", "-i", f"color=c=white:s={tw}x{th_}:d=1"]
        chains.append(f"[{k}:v]scale={tw}:{th_}[v{k}]")
    if cols * rows == 1:
        fc = f"[0:v]scale={tw}:{th_}"
    else:
        layout = "|".join(f"{(k % cols) * tw}_{(k // cols) * th_}" for k in range(cols * rows))
        fc = ";".join(chains) + ";" + "".join(f"[v{k}]" for k in range(cols * rows)) + f"xstack=inputs={cols * rows}:layout={layout}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-frames:v", "1", "cards/_preview.png"],
                   cwd=str(work), capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("--style", choices=["cream"] + list(STYLES), default="")
    ap.add_argument("--accent", default="")
    ap.add_argument("--size", default="")
    ap.add_argument("--handle", default="", help="account shown on every card, e.g. @<your-account>")
    ap.add_argument("--font", default="")
    ap.add_argument("--font-dir", default="", help="folder with Paperlogy-5Medium/7Bold/8ExtraBold.ttf (optional)")
    ap.add_argument("--image-mode", choices=["full", "inset"], default="", help="full: image behind the text (default), inset: image as a box above the text")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    work = Path(a.work)
    data = json.loads((work / "cards.json").read_text(encoding="utf-8"))
    cards = data["cards"]
    style = a.style or data.get("style") or "cream"
    st = STYLES.get(style, STYLES["bold"])
    accent = a.accent or data.get("accent") or st["accent"]
    handle = a.handle or data.get("handle", "")
    w, h = (int(x) for x in (a.size or data.get("size") or "1080x1350").lower().split("x"))
    css = font_css(a.font, a.font_dir)
    mode = a.image_mode or data.get("image_mode") or "full"
    extra_css = ""
    if data.get("design_css"):  # account design made from a chosen reference (references/design_from_reference.md)
        dp = work / data["design_css"]
        extra_css = dp.read_text(encoding="utf-8") if dp.exists() else ""
        if not extra_css:
            print(f"[warn] design_css not found: {data['design_css']}", file=sys.stderr)
    out = work / "cards"
    out.mkdir(exist_ok=True)
    for old in out.glob("card_*.png"):
        old.unlink()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page(viewport={"width": w, "height": h})
        for i, c in enumerate(cards):
            if style == "cream":
                import cream
                u = img_url(work, c.get("image"))
                c = dict(c, _size=image_size(work, c.get("image")))
                src = u[4:-1] if u.startswith("url(") else ""
                doc = ("<!DOCTYPE html><html><head><meta charset='utf-8'>" + cream.css(cream.T, a.accent or data.get("accent"), w / 1080, css) +
                       (f"<style>html,body{{height:{h}px}}</style>") + (f"<style>{extra_css}</style>" if extra_css else "") + "</head><body>" +
                       cream.card(c, i, len(cards), handle, src, w / 1080, data.get("sources", [])) + "</body></html>")
                page.set_content(doc)
            else:
                page.set_content(card_html(c, i, len(cards), work, css, w, h, st, accent, handle, data.get("sources", []),
                                           mode, float(data.get("scrim", 0.62)), extra_css))
            page.evaluate("document.fonts.ready")
            over = page.evaluate("""() => { const w = document.querySelector('.wrap');
                if (w) return w.scrollHeight > w.clientHeight + 2;
                const c = document.querySelector('.c'); if (!c) return false;
                const foot = document.querySelector('.brand, .page'); const lim = (foot ? foot.getBoundingClientRect().top : innerHeight) - 8;
                return [...c.children].filter(e => !e.matches('.brand,.page,.ad,.no') && getComputedStyle(e).position !== 'absolute')
                    .some(e => e.getBoundingClientRect().bottom > lim); }""")
            if over:
                print(f"[warn] card {i + 1} ({c.get('type')}): content does not fit - shorten it", file=sys.stderr)
            page.screenshot(path=str(out / f"card_{i + 1:02d}.png"))
        browser.close()
    contact_sheet(work, len(cards), w, h)

    tags = " ".join("#" + t.lstrip("#") for t in data.get("hashtags", []))
    alts = [f"{k + 1}. {c.get('alt', '')}" for k, c in enumerate(cards) if c.get("alt")]
    src = [f"- {x.get('name', '')} {x.get('url', '')}".rstrip() for x in data.get("sources", [])]
    lines = [data.get("caption", "").strip(), "", tags, "", "[첫 댓글]", data.get("first_comment", "").strip()]
    if alts:
        lines += ["", "[대체 텍스트(접근성) - 사진마다 '대체 텍스트 작성'에 붙여 넣기]", *alts]
    if src:
        lines += ["", "[출처]", *src]
    (work / "caption.txt").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"{len(cards)} cards -> {out}")
    print(f"review sheet -> {out / '_preview.png'}")
    print(f"caption      -> {work / 'caption.txt'}")


if __name__ == "__main__":
    main()
