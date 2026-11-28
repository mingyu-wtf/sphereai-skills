"""Turn receipts.jsonl into a tidy Excel workbook, or report progress.

    python build_xlsx.py <work_folder> --status          # which pages are still unread
    python build_xlsx.py <work_folder> [--lang ko|en] [--out receipts.xlsx]

receipts.jsonl: one JSON object per receipt (see references/schema.md).
"""
import argparse, csv, json, os, sys
from collections import defaultdict

H = {
    "ko": dict(list="영수증 목록", items="품목", summary="요약", check="확인 필요",
               cols=["번호", "날짜", "시간", "가게", "사업자번호", "분류", "결제", "카드 끝4자리", "공급가", "부가세", "합계", "통화", "품목 수", "신뢰도", "메모", "원본 파일", "페이지"],
               icols=["번호", "날짜", "가게", "품목", "수량", "단가", "금액"],
               total="합계", by_month="월별", by_cat="분류별", by_pay="결제수단별", month="월", count="건수", amount="금액",
               ccols=["번호", "날짜", "가게", "합계", "이유", "페이지"],
               reasons=dict(low="신뢰도 낮음", no_date="날짜 없음", no_total="합계 없음", item_sum="품목 합계와 총액이 다름", dup="같은 날짜, 가게, 금액이 또 있음(중복 의심)", vat="공급가 + 부가세가 합계와 다름"),
               unknown="(미분류)", pay={"card": "카드", "cash": "현금", "transfer": "계좌이체", "other": "기타"}, cat_h="분류", pay_h="결제수단"),
    "en": dict(list="Receipts", items="Line items", summary="Summary", check="To check",
               cols=["No", "Date", "Time", "Store", "Business no", "Category", "Payment", "Card last 4", "Net", "Tax", "Total", "Currency", "Items", "Confidence", "Note", "Source file", "Page"],
               icols=["No", "Date", "Store", "Item", "Qty", "Unit price", "Amount"],
               total="Total", by_month="By month", by_cat="By category", by_pay="By payment", month="Month", count="Count", amount="Amount",
               ccols=["No", "Date", "Store", "Total", "Reason", "Page"],
               reasons=dict(low="Low confidence", no_date="No date", no_total="No total", item_sum="Items do not add up to total", dup="Same date, store and total appears again (possible duplicate)", vat="Net + tax does not equal total"),
               unknown="(none)", pay={}, cat_h="Category", pay_h="Payment"),
}


def load(work):
    man = []
    mp = os.path.join(work, "manifest.csv")
    if os.path.exists(mp):
        man = list(csv.DictReader(open(mp, encoding="utf-8-sig")))
    recs = []
    jp = os.path.join(work, "receipts.jsonl")
    if os.path.exists(jp):
        for i, ln in enumerate(open(jp, encoding="utf-8"), 1):
            ln = ln.strip()
            if not ln:
                continue
            try:
                recs.append(json.loads(ln))
            except json.JSONDecodeError as e:
                print(f"receipts.jsonl line {i} is not valid JSON: {e}"); sys.exit(1)
    return man, recs


def num(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).replace(",", "").replace("원", "").strip()
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return None


def status(work):
    man, recs = load(work)
    done = {str(r.get("page_id")) for r in recs}
    todo = [m["page_id"] for m in man if m["page_id"] not in done]
    print(f"pages: {len(man)}  read: {len(man) - len(todo)}  left: {len(todo)}  receipts so far: {sum(1 for r in recs if not r.get('skip'))}")
    if todo:
        print("next pages:", " ".join(todo[:10]))


def build(work, lang, out):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    t = H[lang]
    man, recs = load(work)
    src = {m["page_id"]: m["source"] for m in man}
    rows = [r for r in recs if not r.get("skip")]
    rows.sort(key=lambda r: (r.get("date") or "9999", r.get("time") or "", str(r.get("page_id"))))
    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="1F2937"); head_font = Font(color="FFFFFF", bold=True)
    warn_fill = PatternFill("solid", fgColor="FFF2CC")

    def header(ws, cols, widths):
        ws.append(cols)
        for c in ws[1]:
            c.fill = head_fill; c.font = head_font; c.alignment = Alignment(horizontal="center")
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A2"

    # 1. receipts
    ws = wb.active; ws.title = t["list"]
    header(ws, t["cols"], [6, 12, 7, 24, 14, 12, 9, 10, 11, 10, 12, 6, 7, 8, 28, 30, 8])
    checks = []
    seen = defaultdict(list)
    for i, r in enumerate(rows, 1):
        items = r.get("items") or []
        total, vat, net = num(r.get("total")), num(r.get("vat")), num(r.get("supply"))
        ws.append([i, r.get("date"), r.get("time"), r.get("store"), r.get("business_no"), r.get("category") or t["unknown"],
                   t["pay"].get(r.get("payment"), r.get("payment")), r.get("card_last4"), net, vat, total, r.get("currency") or ("KRW" if lang == "ko" else ""),
                   len(items), r.get("confidence"), r.get("note"), src.get(str(r.get("page_id")), ""), str(r.get("page_id"))])
        pc = ws.cell(row=ws.max_row, column=17)
        pc.hyperlink = f"pages/{r.get('page_id')}.jpg"; pc.font = Font(color="2563EB", underline="single")
        why = []
        if r.get("confidence") == "low": why.append(t["reasons"]["low"])
        if not r.get("date"): why.append(t["reasons"]["no_date"])
        if total is None: why.append(t["reasons"]["no_total"])
        amts = [num(x.get("amount")) for x in items]
        if total is not None and amts and all(a is not None for a in amts) and abs(sum(amts) - total) > 1:
            why.append(t["reasons"]["item_sum"])
        if total and vat and net is not None and abs(net + vat - total) > 2:
            why.append(t["reasons"]["vat"])
        key = (r.get("date"), (r.get("store") or "").strip(), total)
        if r.get("date") and total is not None:
            seen[key].append(i)
        if why:
            checks.append([i, r.get("date"), r.get("store"), total, ", ".join(why), str(r.get("page_id"))])
            for c in ws[ws.max_row]:
                c.fill = warn_fill
    for key, ids in seen.items():
        if len(ids) > 1:
            for i in ids:
                r = rows[i - 1]
                checks.append([i, r.get("date"), r.get("store"), num(r.get("total")), t["reasons"]["dup"] + f" ({', '.join(map(str, ids))})", str(r.get("page_id"))])
    last = ws.max_row
    ws.append([t["total"]] + [None] * 7 + [f"=SUM(I2:I{last})", f"=SUM(J2:J{last})", f"=SUM(K2:K{last})"])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    for col in "IJK":
        for c in ws[col][1:]:
            c.number_format = "#,##0"
    ws.auto_filter.ref = f"A1:Q{last}"

    # 2. line items
    wi = wb.create_sheet(t["items"])
    header(wi, t["icols"], [6, 12, 22, 30, 6, 11, 11])
    for i, r in enumerate(rows, 1):
        for x in r.get("items") or []:
            wi.append([i, r.get("date"), r.get("store"), x.get("name"), num(x.get("qty")), num(x.get("unit_price")), num(x.get("amount"))])
    for col in "FG":
        for c in wi[col][1:]:
            c.number_format = "#,##0"
    wi.auto_filter.ref = f"A1:G{max(wi.max_row, 1)}"

    # 3. summary (plain numbers so it opens anywhere)
    su = wb.create_sheet(t["summary"])
    su.column_dimensions["A"].width = 18; su.column_dimensions["B"].width = 8; su.column_dimensions["C"].width = 14

    def block(title, keyf, first):
        agg = defaultdict(lambda: [0, 0])
        for r in rows:
            k = keyf(r); v = num(r.get("total")) or 0
            agg[k][0] += 1; agg[k][1] += v
        su.append([title]); su.cell(row=su.max_row, column=1).font = Font(bold=True, size=12)
        su.append([first, t["count"], t["amount"]])
        for c in su[su.max_row]:
            c.fill = head_fill; c.font = head_font
        for k in sorted(agg):
            su.append([k, agg[k][0], agg[k][1]]); su.cell(row=su.max_row, column=3).number_format = "#,##0"
        su.append([t["total"], sum(v[0] for v in agg.values()), sum(v[1] for v in agg.values())])
        su.cell(row=su.max_row, column=3).number_format = "#,##0"
        for c in su[su.max_row]:
            c.font = Font(bold=True)
        su.append([])

    block(t["by_month"], lambda r: (r.get("date") or "????-??")[:7], t["month"])
    block(t["by_cat"], lambda r: r.get("category") or t["unknown"], t["cat_h"])
    block(t["by_pay"], lambda r: t["pay"].get(r.get("payment"), r.get("payment")) or t["unknown"], t["pay_h"])

    # 4. to check
    wc = wb.create_sheet(t["check"])
    header(wc, t["ccols"], [6, 12, 24, 12, 50, 8])
    for c in sorted(checks, key=lambda x: x[0]):
        wc.append(c)
        wc.cell(row=wc.max_row, column=4).number_format = "#,##0"
        pc = wc.cell(row=wc.max_row, column=6); pc.hyperlink = f"pages/{c[5]}.jpg"; pc.font = Font(color="2563EB", underline="single")

    path = os.path.join(work, out)
    wb.save(path)
    done = {str(r.get("page_id")) for r in recs}
    left = sum(1 for m in man if m["page_id"] not in done)
    print(f"saved: {path}")
    print(f"receipts: {len(rows)}  total: {sum(num(r.get('total')) or 0 for r in rows):,}  to check: {len(checks)}  unread pages: {left}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--lang", default="ko", choices=["ko", "en"])
    ap.add_argument("--out", default="receipts.xlsx")
    a = ap.parse_args()
    if a.status:
        status(a.work)
    else:
        build(a.work, a.lang, a.out)


if __name__ == "__main__":
    main()
