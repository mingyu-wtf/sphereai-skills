"""스레드 하루 보고 도우미 (읽기·집계 전용).

  python scripts/report_history.py collect
      -> 오늘 로컬 기록 집계: 소통 건수, 오늘 올린 글, 대기열 잔량, 실패·건너뛴 슬롯, 오늘 알림, 어제 측정값
  python scripts/report_history.py save --json '{"followers":120,"views_total":5400,"posts":[{"id":"g3","views":40,"likes":2,"comments":1,"reposts":0}]}'
      -> 오늘 측정값을 기록 파일에 저장(같은 날이면 덮어씀)하고 어제 대비 증감을 출력
측정값은 화면에서 읽은 숫자만 넣는다. 못 읽은 값은 null.
"""
import argparse, json, os, sys, datetime as dt
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def find_config():
    for c in [os.environ.get("THREADS_OPS_CONFIG"), Path.cwd() / "config.json", Path(__file__).resolve().parents[1] / "config.json"]:
        if c and Path(c).is_file():
            return Path(c).resolve()
    sys.exit("config.json을 찾지 못했다.")


CFG_PATH = find_config()
BASE = CFG_PATH.parent
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
L = CFG.get("limits", {})


def p(key, default):
    return BASE / CFG.get("paths", {}).get(key, default)


def rj(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def collect(today):
    ds = today.isoformat()
    rows = [x for x in rj(p("engage_log", "logs/engage.json"), {"done": []}).get("done", []) if x.get("date") == ds]
    c = {
        "replies": len([x for x in rows if x.get("type") not in ("선팔", "인용")]),
        "thanks": len([x for x in rows if str(x.get("kind", "")).startswith("감사")]),
        "daily_hi": len([x for x in rows if x.get("type") == "스하리" and x.get("kind") == "일상"]),
        "my_comment_replies": len([x for x in rows if x.get("type") == "내글댓글답"]),
        "follows": len([x for x in rows if x.get("type") == "선팔"]),
        "quotes": len([x for x in rows if x.get("type") == "인용"]),
    }
    q = rj(p("queue", "data/queue.json"), {"items": []})["items"]
    posted = [{"id": x["id"], "title": x.get("title"), "posted_at": x.get("posted_at"), "url": x.get("url")}
              for x in q if x.get("status") == "게시됨" and str(x.get("posted_at", "")).startswith(ds)]
    plan = rj(p("plan_dir", "plan") / ("plan_%s.json" % today.strftime("%Y%m%d")), {"items": []})
    bad_slots = [{"slot": x["slot"], "status": x["status"], "note": x.get("note", "")} for x in plan["items"] if x["status"] in ("failed", "skipped")]
    alerts_f = p("alerts", "logs/alerts.md")
    alerts = [l.strip() for l in alerts_f.read_text(encoding="utf-8").splitlines() if ds in l] if alerts_f.exists() else []
    hist = rj(p("report_history", "logs/report_history.json"), {"days": []})["days"]
    prev = next((h for h in reversed(hist) if h["date"] < ds), None)
    return {
        "date": ds,
        "counts": c,
        "limits": {"replies": L.get("replies_per_day"), "thanks": L.get("thanks_per_day"), "follows": L.get("follows_per_day")},
        "posted_today": posted,
        "queue_waiting": len([x for x in q if x.get("status") == "대기"]),
        "queue_hold": [{"id": x["id"], "reason": x.get("hold_reason", "")} for x in q if x.get("status") == "보류"],
        "failed_or_skipped_slots": bad_slots,
        "alerts_today": alerts,
        "yesterday": prev,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["collect", "save"])
    ap.add_argument("--json")
    a = ap.parse_args()
    today = dt.date.today()
    if a.cmd == "collect":
        print(json.dumps(collect(today), ensure_ascii=False, indent=2))
        return
    m = json.loads(a.json or "{}")
    hp = p("report_history", "logs/report_history.json")
    hist = rj(hp, {"days": []})
    row = {"date": today.isoformat(), "followers": m.get("followers"), "views_total": m.get("views_total"),
           "posts": m.get("posts", []), "counts": collect(today)["counts"]}
    hist["days"] = [h for h in hist["days"] if h["date"] != row["date"]] + [row]
    hist["days"].sort(key=lambda h: h["date"])
    hp.parent.mkdir(parents=True, exist_ok=True)
    hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
    prev = next((h for h in reversed(hist["days"]) if h["date"] < row["date"]), None)

    def diff(k):
        if not prev or prev.get(k) is None or row.get(k) is None:
            return None
        return row[k] - prev[k]

    print(json.dumps({"saved": row["date"], "followers": row["followers"], "followers_diff": diff("followers"),
                      "views_total": row["views_total"], "views_diff": diff("views_total")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
