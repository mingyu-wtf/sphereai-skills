"""스레드 자동 운영 - '지금 할 일(due)'을 JSON으로 출력한다.

작업 스케줄러(cron)가 10분마다 run.ps1 / run.sh 를 통해 부른다.
할 일이 없으면 "[]"만 출력하고 끝난다 -> Claude를 부르지 않으니 토큰이 들지 않는다.
하루 계획(plan)은 그날 처음 호출될 때 무작위 시각으로 만든다(정각에 몰리지 않게).

설정: config.json (찾는 순서: 환경변수 THREADS_OPS_CONFIG -> 현재 폴더 -> 이 스크립트의 상위 폴더)
사용: python scripts/due.py            # 지금 할 일
      python scripts/due.py --show     # 오늘 계획 전체 보기
"""
import json, os, random, sys, datetime as dt
from pathlib import Path


def find_config():
    cands = [os.environ.get("THREADS_OPS_CONFIG"), Path.cwd() / "config.json", Path(__file__).resolve().parents[1] / "config.json"]
    for c in cands:
        if c and Path(c).is_file():
            return Path(c).resolve()
    sys.exit("config.json을 찾지 못했다. scripts/config.example.json을 작업 폴더에 config.json으로 복사해서 고칠 것.")


CFG_PATH = find_config()
BASE = CFG_PATH.parent
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
S = CFG["schedule"]


def p(key):
    return BASE / CFG["paths"][key]


def hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def fmt(mins):
    mins = max(0, min(mins, 23 * 60 + 59))
    return "%02d:%02d" % (mins // 60, mins % 60)


def make_plan(now):
    random.seed()
    lo, hi = S.get("post_jitter_min", [-15, 40])
    gap = S.get("post_min_gap_min", 130)
    posts, prev = [], -999
    for i, b in enumerate(S["post_slots"]):
        base = hm(b)
        t = base
        for _ in range(50):
            t = base + random.randint(lo, hi)
            if t - prev >= gap:
                break
        prev = t
        posts.append({"slot": "post-%d" % (i + 1), "kind": "post", "at": fmt(t), "status": "pending"})
    elo, ehi = S.get("engage_jitter_min", [-10, 25])
    counts = S.get("engage_counts", [])
    engs = []
    for i, b in enumerate(S["engage_slots"]):
        t = hm(b) + random.randint(elo, ehi)
        c = counts[i] if i < len(counts) else 5
        engs.append({"slot": "engage-%d" % (i + 1), "kind": "engage", "at": fmt(t), "count": c, "status": "pending"})
    rlo, rhi = S.get("research_jitter_min", [0, 20])
    research = {"slot": "research", "kind": "research", "at": fmt(hm(S.get("research_at", "08:40")) + random.randint(rlo, rhi)), "status": "pending"}
    items = [research] + engs + posts
    now_m = now.hour * 60 + now.minute
    for it in items:
        if now_m - hm(it["at"]) > S.get("window_min", 120):
            it["status"] = "skipped"
            it["note"] = "계획 생성 시점에 이미 지남"
    items.sort(key=lambda x: hm(x["at"]))
    return {"date": now.strftime("%Y-%m-%d"), "created": now.strftime("%H:%M"), "items": items}


def load_plan(now):
    d = p("plan_dir")
    d.mkdir(parents=True, exist_ok=True)
    f = d / ("plan_%s.json" % now.strftime("%Y%m%d"))
    if not f.exists():
        f.write_text(json.dumps(make_plan(now), ensure_ascii=False, indent=2), encoding="utf-8")
    return f, json.loads(f.read_text(encoding="utf-8"))


def queue_waiting():
    try:
        q = json.loads(p("queue").read_text(encoding="utf-8"))
        return [x for x in q["items"] if x.get("status") == "대기"]
    except Exception:
        return []


def main():
    now = dt.datetime.now()
    if "--show" in sys.argv:
        f, plan = load_plan(now)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    now_m = now.hour * 60 + now.minute
    a, b = S.get("active_hours", ["08:30", "23:30"])
    if now_m < hm(a) or now_m > hm(b):
        print("[]")
        return
    path, plan = load_plan(now)
    win = S.get("window_min", 120)
    due, waiting = [], queue_waiting()
    for it in plan["items"]:
        if it["status"] != "pending":
            continue
        t = hm(it["at"])
        if not (t <= now_m <= t + win):
            if now_m > t + win:
                it["status"] = "skipped"
                it["note"] = "시간 창 지남"
            continue
        d = dict(it)
        if it["kind"] == "post":
            if not waiting:
                continue          # 대기열이 비면 research가 채울 때까지 기다린다
            d["queue_id"] = waiting[0]["id"]
        if it["kind"] == "research":
            qmin = S.get("queue_min", 6)
            if len(waiting) >= qmin:
                it["status"] = "skipped"
                it["note"] = "대기열 충분(%d개)" % len(waiting)
                continue
            d["need"] = qmin - len(waiting) + S.get("research_extra", 5)
        due.append(d)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    due = due[: S.get("max_due_per_run", 2)]   # 한 번에 너무 많이 하지 않는다(작업 제한 시간)
    print(json.dumps({"plan_file": str(path), "now": now.strftime("%Y-%m-%d %H:%M"), "due": due}, ensure_ascii=False) if due else "[]")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
