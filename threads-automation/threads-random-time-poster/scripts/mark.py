"""스레드 운영 기록 도우미 (Claude가 작업을 끝낸 뒤 호출한다).

  python scripts/mark.py slot <slot> <done|failed|skipped> [메모]
  python scripts/mark.py queue <id> <게시됨|보류|대기> [글 URL 또는 보류 사유]
  python scripts/mark.py engage '<json 한 건>'     # 소통 기록 1건 추가(실제로 붙은 걸 확인한 뒤에만)
  python scripts/mark.py count                     # 오늘 소통 건수와 남은 한도
  python scripts/mark.py targets                   # 오늘 목표(점진 증가 항목 포함)
  python scripts/mark.py stop "<이유>"             # 제한·경고가 떴을 때: 오늘 소통 중단 + 점진 목표를 시작값으로 되돌림
  python scripts/mark.py addqueue '<json 한 건>'   # 대기열에 새 글 추가(id 중복이면 무시)
  python scripts/mark.py alert "<한 줄>"           # logs/alerts.md 에 한 줄

engage 기록 type 약속:
  {"type":"스하리","kind":"정보 글|일상|감사","url":..,"reply":..,"liked":true}
  {"type":"내글댓글답","url":..,"reply":..}
  {"type":"선팔","handle":..,"followers":N,"source":..,"greet":..}
  {"type":"인용","url":..,"comment":..}
"""
import json, os, sys, datetime as dt
from pathlib import Path


def find_config():
    cands = [os.environ.get("THREADS_OPS_CONFIG"), Path.cwd() / "config.json", Path(__file__).resolve().parents[1] / "config.json"]
    for c in cands:
        if c and Path(c).is_file():
            return Path(c).resolve()
    sys.exit("config.json을 찾지 못했다.")


CFG_PATH = find_config()
BASE = CFG_PATH.parent
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
L = CFG.get("limits", {})


def p(key):
    return BASE / CFG["paths"][key]


def rj(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def wj(path, d):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def alert(msg, now):
    f = p("alerts")
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a", encoding="utf-8") as fh:
        fh.write("- %s %s\n" % (now.strftime("%Y-%m-%d %H:%M"), msg))


def state_path():
    return p("engage_log").parent / "ramp_state.json"


def today_rows(now):
    d = rj(p("engage_log"), {"done": []})
    today = now.strftime("%Y-%m-%d")
    return [x for x in d.get("done", []) if x.get("date") == today]


def counts(now):
    rows = today_rows(now)
    replies = [x for x in rows if x.get("type") not in ("선팔", "인용")]
    return {
        "today_replies": len(replies),
        "today_thanks": len([x for x in rows if str(x.get("kind", "")).startswith("감사")]),
        "today_daily_hi": len([x for x in rows if x.get("type") == "스하리" and x.get("kind") == "일상"]),
        "today_my_comment_replies": len([x for x in rows if x.get("type") == "내글댓글답"]),
        "today_follows": len([x for x in rows if x.get("type") == "선팔"]),
        "today_quotes": len([x for x in rows if x.get("type") == "인용"]),
    }


def targets(now):
    st = rj(state_path(), {})
    today = now.date()
    stopped = st.get("stopped", {}).get("date") == today.isoformat()
    out = {"stopped_today": stopped}
    for name, r in L.get("ramps", {}).items():
        sd = st.get("ramp_start", {}).get(name, r.get("start_date"))
        try:
            days = (today - dt.date.fromisoformat(sd)).days
        except Exception:
            days = 0
        out[name] = 0 if stopped else max(r["start"], min(r["start"] + r.get("step", 1) * max(days, 0), r["max"]))
    c = counts(now)
    out["replies_left"] = 0 if stopped else max(L.get("replies_per_day", 30) - c["today_replies"], 0)
    out["thanks_left"] = 0 if stopped else max(L.get("thanks_per_day", 6) - c["today_thanks"], 0)
    out["follows_left"] = 0 if stopped else max(L.get("follows_per_day", 15) - c["today_follows"], 0)
    out["daily_hi_left"] = max(out.get("daily_hi", 0) - c["today_daily_hi"], 0)
    out["quote_left"] = max(out.get("quote", 0) - c["today_quotes"], 0)
    out.update(c)
    return out


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    now = dt.datetime.now()
    cmd = a[0]
    if cmd == "slot":
        f = p("plan_dir") / ("plan_%s.json" % now.strftime("%Y%m%d"))
        plan = rj(f)
        if not plan:
            sys.exit("오늘 계획 파일이 없다: %s" % f)
        for it in plan["items"]:
            if it["slot"] == a[1]:
                it["status"] = a[2]
                it["finished"] = now.strftime("%H:%M")
                if len(a) > 3:
                    it["note"] = a[3]
        wj(f, plan)
        if a[2] == "failed":
            alert("%s 실패: %s" % (a[1], a[3] if len(a) > 3 else ""), now)
    elif cmd == "queue":
        q = rj(p("queue"), {"items": []})
        for it in q["items"]:
            if it["id"] == a[1]:
                it["status"] = a[2]
                if a[2] == "게시됨":
                    it["posted_at"] = now.strftime("%Y-%m-%d %H:%M")
                    if len(a) > 3:
                        it["url"] = a[3]
                elif len(a) > 3:
                    it["hold_reason"] = a[3]
        wj(p("queue"), q)
    elif cmd == "engage":
        d = rj(p("engage_log"), {"done": []})
        row = json.loads(a[1])
        row.setdefault("date", now.strftime("%Y-%m-%d"))
        row.setdefault("time", now.strftime("%H:%M"))
        d.setdefault("done", []).append(row)
        wj(p("engage_log"), d)
        print("기록함:", row.get("type"), row.get("kind", ""))
    elif cmd == "count":
        print(json.dumps(counts(now), ensure_ascii=False))
    elif cmd == "targets":
        print(json.dumps(targets(now), ensure_ascii=False))
    elif cmd == "stop":
        reason = a[1] if len(a) > 1 else "제한·경고"
        st = rj(state_path(), {})
        st["stopped"] = {"date": now.date().isoformat(), "reason": reason}
        tomorrow = (now.date() + dt.timedelta(days=1)).isoformat()
        st["ramp_start"] = {name: tomorrow for name in L.get("ramps", {})}
        wj(state_path(), st)
        alert("소통 중단(오늘): %s. 점진 목표는 내일 시작값으로 되돌림" % reason, now)
        print("오늘 소통 중단, 내일부터 시작값으로")
    elif cmd == "addqueue":
        q = rj(p("queue"), {"items": []})
        row = json.loads(a[1])
        if any(x["id"] == row["id"] for x in q["items"]):
            print("duplicate", row["id"])
            return
        row.setdefault("status", "대기")
        q["items"].append(row)
        wj(p("queue"), q)
        print("added", row["id"])
    elif cmd == "alert":
        alert(a[1], now)
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
