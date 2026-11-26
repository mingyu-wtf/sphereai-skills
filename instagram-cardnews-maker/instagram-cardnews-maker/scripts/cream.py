# -*- coding: utf-8 -*-
"""'cream' style: warm cream cards, navy block titles with an orange accent, orange number badges,
rounded photos, big prices, check lists, comparison table, navy call-to-action button.
Used by render_cards.py when style == "cream" (the default). Sizes are for a 1080-wide card."""
import html
import re

T = {"bg": "#FFF6EA", "ink": "#1B2A4A", "pt": "#FF7A1A", "pt2": "#FFB070", "sub": "#6B7387", "card": "#ffffff",
     "line": "#F0DFC9", "good": "#1E9E6A", "bad": "#D9534F", "ph1": "#f3e6d3", "ph2": "#efdfc8", "phx": "#a8957a"}


def esc(t):
    return html.escape(str(t or "").strip())


def rich(t, cls="pt"):
    """**word** -> orange accent word, new line kept."""
    s = esc(t)
    s = re.sub(r"\*\*(.+?)\*\*", rf'<span class="{cls}">\1</span>', s)
    return s.replace("\n", "<br>")


def block_title(t):
    """Cover title: every line becomes a navy block; **word** turns light orange inside it."""
    lines = [x for x in str(t or "").split("\n") if x.strip()]
    return "<br>".join(f'<span class="blk">{rich(x, "pt2")}</span>' for x in lines)


def css(tok, accent, s, font_css):
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    k = dict(tok, pt=accent or tok["pt"])
    return f"""<style>{font_css}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{px(1080)};overflow:hidden}}
body{{background:{k['bg']};color:{k['ink']};font-family:'CardFont','Paperlogy','Pretendard','Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',sans-serif;
position:relative;word-break:keep-all;overflow-wrap:anywhere;-webkit-font-smoothing:antialiased}}
.c{{position:absolute;inset:0;padding:{px(72)}}}
.tag{{display:inline-block;background:{k['ink']};color:#fff;font-weight:700;font-size:{px(30)};padding:{px(10)} {px(26)};border-radius:{px(40)}}}
.brand{{position:absolute;left:{px(72)};bottom:{px(56)};font-size:{px(28)};font-weight:700;color:{k['sub']}}}
.page{{position:absolute;right:{px(72)};bottom:{px(56)};font-size:{px(28)};font-weight:700;color:{k['sub']}}}
.pt{{color:{k['pt']}}}.pt2{{color:{k['pt2']}}}
.ph{{border-radius:{px(36)};overflow:hidden;background:repeating-linear-gradient(45deg,{k['ph1']},{k['ph1']} {px(14)},{k['ph2']} {px(14)},{k['ph2']} {px(28)});
display:flex;align-items:center;justify-content:center;color:{k['phx']};font-weight:700;font-size:{px(34)};text-align:center}}
.ph img{{width:100%;height:100%;object-fit:cover;display:block}}
.ph.fit{{position:relative}}.ph.fit i{{position:absolute;inset:-{px(40)};background-size:cover;background-position:center;filter:blur({px(28)}) saturate(.9) brightness(1.04);opacity:.85}}
.blk{{background:{k['ink']};color:#fff;padding:0 {px(18)};display:inline-block;margin-bottom:{px(12)};border-radius:{px(6)}}}
h1{{font-size:{px(112)};line-height:1.3;font-weight:800;margin-top:{px(44)};letter-spacing:-.03em}}
h2{{font-size:{px(84)};font-weight:800;margin-top:{px(34)};letter-spacing:-.025em;line-height:1.2}}
.s{{font-size:{px(40)};font-weight:500;color:{k['sub']};margin-top:{px(28)};line-height:1.45}}
.no{{position:absolute;right:{px(72)};top:{px(64)};width:{px(120)};height:{px(120)};border-radius:50%;background:{k['pt']};color:#fff;font-size:{px(70)};font-weight:800;display:flex;align-items:center;justify-content:center}}
.nm{{font-size:{px(56)};font-weight:800;line-height:1.3;margin-top:{px(22)};width:{px(760)};letter-spacing:-.025em}}
.pw{{display:flex;justify-content:space-between;align-items:flex-end;margin-top:{px(22)}}}
.pr{{font-size:{px(88)};font-weight:800;letter-spacing:-.035em;line-height:1}}
.pr small{{font-size:{px(44)};font-weight:700}}
.rt{{font-size:{px(40)};font-weight:700;color:{k['sub']};margin-bottom:{px(6)}}}.rt b{{color:{k['ink']}}}
.ck{{margin-top:{px(18)};display:flex;flex-direction:column;gap:{px(10)}}}
.ck div{{font-size:{px(34)};font-weight:700;display:flex;gap:{px(14)};align-items:center;line-height:1.35}}
.ck i{{font-style:normal;display:inline-flex;width:{px(38)};height:{px(38)};border-radius:{px(10)};color:#fff;align-items:center;justify-content:center;font-size:{px(24)};flex:none}}
.ck .g i{{background:{k['good']}}}.ck .b i{{background:{k['bad']}}}
.ck.lg div{{font-size:{px(46)}}}.ck.lg i{{width:{px(52)};height:{px(52)};font-size:{px(32)};border-radius:{px(14)}}}
.fn{{font-size:{px(24)};color:{k['sub']};font-weight:500;margin-top:{px(14)}}}
.bub{{background:#fff;border:{px(2)} solid {k['line']};border-radius:{px(30)} {px(30)} {px(30)} {px(6)};padding:{px(16)} {px(26)};margin-top:{px(18)}}}
.bub .st{{color:{k['pt']};font-size:{px(26)};letter-spacing:.08em;font-weight:700}}
.bub .tx{{font-size:{px(30)};font-weight:700;line-height:1.4;margin-top:{px(6)}}}
table{{width:100%;border-collapse:separate;border-spacing:0 {px(14)};margin-top:{px(20)};font-size:{px(36)}}}
th{{font-size:{px(28)};color:{k['sub']};font-weight:700;text-align:left;padding:0 {px(20)}}}
td{{background:#fff;padding:{px(30)} {px(20)};font-weight:700}}
td:first-child{{border-radius:{px(24)} 0 0 {px(24)}}}td:last-child{{border-radius:0 {px(24)} {px(24)} 0}}
td .n{{display:inline-block;width:{px(48)};height:{px(48)};border-radius:50%;background:{k['pt']};color:#fff;text-align:center;line-height:{px(48)};margin-right:{px(12)};font-size:{px(28)}}}
.go{{margin-top:{px(28)};font-size:{px(46)};font-weight:800;text-align:center;background:{k['ink']};color:#fff;border-radius:{px(30)};padding:{px(36)}}}
.ad{{position:absolute;left:{px(72)};right:{px(72)};bottom:{px(110)};font-size:{px(24)};color:{k['sub']};text-align:center;font-weight:500;line-height:1.45}}
.body{{font-size:{px(44)};font-weight:500;line-height:1.6;color:{k['sub']};margin-top:{px(30)}}}
.body .pt{{font-weight:800}}
.box{{background:#fff;border:{px(2)} solid {k['line']};border-radius:{px(30)};padding:{px(36)} {px(40)};margin-top:{px(34)}}}
.big{{font-size:{px(210)};font-weight:800;letter-spacing:-.05em;line-height:1;color:{k['pt']};margin-top:{px(60)}}}
.lb{{font-size:{px(38)};font-weight:700;color:{k['sub']};margin-top:{px(16)}}}
.qm{{font-size:{px(220)};font-weight:800;line-height:.7;color:{k['pt']};margin-top:{px(120)};height:{px(120)}}}
.q{{font-size:{px(64)};font-weight:800;line-height:1.42;letter-spacing:-.025em}}
.by{{margin-top:{px(36)};font-size:{px(34)};font-weight:700;color:{k['sub']}}}
.cols{{display:flex;gap:{px(20)};margin-top:{px(40)}}}
.col{{flex:1;background:#fff;border:{px(2)} solid {k['line']};border-radius:{px(28)};padding:{px(30)}}}
.col.on{{background:{k['ink']};color:#fff;border-color:{k['ink']}}}
.col .k{{font-size:{px(40)};font-weight:800;margin-bottom:{px(16)}}}
.col.on .k{{color:{k['pt2']}}}
.col li{{list-style:none;font-size:{px(34)};font-weight:700;line-height:1.4;padding:{px(14)} 0;border-top:{px(2)} solid {k['line']}}}
.col.on li{{border-top-color:rgba(255,255,255,.18)}}
.btns{{display:flex;gap:{px(16)};margin-top:{px(24)}}}
.btns span{{font-size:{px(32)};font-weight:800;padding:{px(14)} {px(28)};border-radius:999px;border:{px(3)} solid {k['ink']}}}
.btns span.on{{background:{k['ink']};color:#fff}}
</style>"""


import math

# photo slot sizes in the cream layout (width x height at 1080 wide) - check.py uses these to warn about mismatched photos
SLOTS = {"product": (936, 690), "product_quote": (936, 600), "cover": (936, 600), "text": (936, 560), "low": (936, 460)}


def auto_fit(size, box_w, box_h, want=None):
    """'cover' when the photo's shape is close to the slot (little is cut), otherwise 'contain' (nothing is cut).
    size = (w, h) of the photo or None if unknown. An explicit 'fit' on the card wins."""
    if want in ("cover", "contain"):
        return want
    if not size:
        return "contain"
    return "cover" if abs(math.log((size[0] / size[1]) / (box_w / box_h))) < 0.16 else "contain"


def ph(work_img, h, s, label="", pos="", fit="cover"):
    """fit cover: fill the box (edges may be cut). fit contain: the whole picture is shown, never cut;
    the leftover space is filled with a soft blurred copy of the same picture."""
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    if work_img and fit == "contain":
        return (f'<div class="ph fit" style="height:{px(h)}"><i style="background-image:url({work_img})"></i>'
                f'<img src="{work_img}" style="object-fit:contain;position:relative;padding:{px(14)}"></div>')
    if work_img:
        return f'<div class="ph" style="height:{px(h)}"><img src="{work_img}" style="{pos}"></div>'
    return f'<div class="ph" style="height:{px(h)}">{esc(label)}</div>'


def card(c, i, total, brand, img_src, s, sources):
    """img_src: data URL of the card's image or ''. Returns the inner body HTML."""
    px = lambda v: f"{int(v * s)}px"  # noqa: E731
    t = c.get("type", "text")
    foot = (f'<span class="brand">{esc(brand)}</span>' if brand else "") + f'<span class="page">{i + 1}/{total}</span>'
    tag = f'<span class="tag">{esc(c["kicker"])}</span>' if c.get("kicker") else ""
    pos = f'object-position:{c["focus"]}' if c.get("focus") else ""

    if t == "cover":
        sub = f'<p class="s">{rich(c.get("sub"))}</p>' if c.get("sub") else ""
        photo = (f'<div style="position:absolute;left:{px(72)};right:{px(72)};bottom:{px(130)}">{ph(img_src, 600, s, "", pos, c.get("fit", "cover"))}</div>'
                 if img_src else "")
        return f'<div class="c">{tag}<h1>{block_title(c.get("title"))}</h1>{sub}{photo}{foot}</div>'

    if t == "product":
        num = f'<div class="no">{esc(c.get("num"))}</div>' if c.get("num") else ""
        price = f'<div class="pr">{esc(c.get("price"))}<small>{esc(c.get("unit", "원"))}</small></div>' if c.get("price") else "<div></div>"
        rev = f'<div class="rt">{esc(c.get("reviews_label", "후기"))} <b>{esc(c.get("reviews"))}</b>개</div>' if c.get("reviews") else ""
        checks = "".join(f'<div class="g"><i>✓</i>{rich(x)}</div>' for x in c.get("good", []))
        checks += "".join(f'<div class="b"><i>!</i>{rich(x)}</div>' for x in c.get("bad", []))
        quote = "".join(f'<div class="bub"><div class="st">★★★★★ {esc(c.get("quote_from", "실제 후기 중에서"))}</div><div class="tx">“{rich(q)}”</div></div>'
                        for q in c.get("quotes", [])[:1])
        note = f'<p class="fn">{rich(c.get("note"))}</p>' if c.get("note") else ""
        hgt = 600 if quote else 690
        return (f'<div class="c">{tag}{num}<p class="nm">{rich(c.get("title"))}</p><div style="margin-top:{px(20)}">{ph(img_src, hgt, s, "상품 사진", pos, auto_fit(c.get("_size"), 936, hgt, c.get("fit")))}</div>'
                f'<div class="pw">{price}{rev}</div><div class="ck">{checks}</div>{quote}{note}{foot}</div>')

    if t == "table":
        cols = c.get("columns", ["항목", "값"])
        head = "".join(f"<th>{esc(x)}</th>" for x in cols)
        rows = ""
        for k, r in enumerate(c.get("rows", []), 1):
            cells = "".join((f'<td><span class="n">{k}</span>{rich(v)}</td>' if j == 0 else f"<td>{rich(v)}</td>") for j, v in enumerate(r))
            rows += f"<tr>{cells}</tr>"
        go = f'<div class="go">{rich(c.get("cta"))}</div>' if c.get("cta") else ""
        ad = f'<p class="ad">{esc(c.get("disclosure"))}</p>' if c.get("disclosure") else ""
        return f'<div class="c">{tag}<h2>{rich(c.get("title"))}</h2><table><tr>{head}</tr>{rows}</table>{go}{ad}{foot}</div>'

    if t in ("text", "list"):
        num = f'<div class="no">{esc(c.get("num"))}</div>' if t == "list" and c.get("num") else ""
        photo = f'<div style="margin-top:{px(40)}">{ph(img_src, 560, s, "", pos, c.get("fit", "cover"))}</div>' if img_src else ""
        return f'<div class="c">{tag}{num}<h2 style="width:{px(800)}">{rich(c.get("title"))}</h2>{photo}<p class="body">{rich(c.get("body"))}</p>{foot}</div>'

    low = (f'<div style="position:absolute;left:{px(72)};right:{px(72)};bottom:{px(165 if (c.get("disclosure") or (t == "closing" and sources)) else 130)}">{ph(img_src, int(c.get("photo_h", 460)), s, "", pos, c.get("fit", "cover"))}</div>'
           if img_src else "")  # optional photo filling the empty lower part of text-only cards

    if t == "stat":
        return (f'<div class="c">{tag}<div class="big">{esc(c.get("value"))}</div><div class="lb">{rich(c.get("label"))}</div>'
                f'<h2>{rich(c.get("title"))}</h2><p class="body">{rich(c.get("body"))}</p>{low}{foot}</div>')

    if t == "compare":
        def col(sd, on):
            items = "".join(f"<li>{rich(x)}</li>" for x in sd.get("items", []))
            return f'<div class="col{" on" if on else ""}"><div class="k">{rich(sd.get("head"))}</div><ul>{items}</ul></div>'
        return f'<div class="c">{tag}<h2>{rich(c.get("title"))}</h2><div class="cols">{col(c.get("left", {}), False)}{col(c.get("right", {}), True)}</div>{low}{foot}</div>'

    if t == "checklist":
        items = "".join(f'<div class="g"><i>✓</i>{rich(x)}</div>' for x in c.get("items", []))
        return f'<div class="c">{tag}<h2>{rich(c.get("title"))}</h2><div class="box" style="padding:{px(48)} {px(44)}"><div class="ck lg" style="gap:{px(40)}">{items}</div></div>{low}{foot}</div>'

    if t == "quote":
        by = f'<div class="by">— {rich(c.get("by"))}</div>' if c.get("by") else ""
        return f'<div class="c">{tag}<div class="qm">“</div><div class="q">{rich(c.get("quote"))}</div>{by}{low}{foot}</div>'

    if t == "closing":
        cta = c.get("cta") or "저장해 두고 필요할 때 꺼내 보기"
        names = ", ".join(esc(x.get("name", "")) for x in sources if x.get("name"))
        src = f'<p class="ad">출처 {names}</p>' if names and not c.get("disclosure") else ""
        ad = f'<p class="ad">{esc(c.get("disclosure"))}</p>' if c.get("disclosure") else ""
        return (f'<div class="c">{tag}<h2>{rich(c.get("title"))}</h2><p class="body" style="font-size:{px(50)}">{rich(c.get("body"))}</p>'
                f'<div class="box" style="margin-top:{px(60)}"><div class="q" style="font-size:{px(42)}">{rich(cta)}</div><div class="btns"><span class="on">저장</span><span>공유</span><span>팔로우</span></div></div>'
                f'{low}{src}{ad}{foot}</div>')
    raise SystemExit(f"card {i + 1}: unknown type '{t}'")
