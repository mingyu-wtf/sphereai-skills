"""Merge today's home feed cards into a 14-day log and show what matches your subject.

Usage:
  python merge_homefeed.py cards_today.json homefeed.json "우주,행성,별,은하"

cards_today.json : the JSON printed by hfScan() (a list of cards).
homefeed.json    : the running log (created if missing).
subject words    : comma separated; a card is kept when its title contains any of them.
"""
import datetime
import json
import os
import sys


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    cards_path, log_path, words_arg = sys.argv[1], sys.argv[2], sys.argv[3]
    words = [w.strip() for w in words_arg.split(",") if w.strip()]
    today = datetime.date.today()
    cards = load(cards_path, [])
    log = load(log_path, [])

    matches = [c for c in cards if c.get("title") and any(w in c["title"] for w in words)]
    known = {(e.get("date"), e.get("url")) for e in log}
    for c in matches:
        entry = {"date": today.isoformat(), "pan": c.get("pan"), "rank": c.get("rank"),
                 "title": c.get("title"), "author": c.get("author", ""), "kind": c.get("kind"),
                 "url": c.get("url", "")}
        if (entry["date"], entry["url"]) not in known:
            log.append(entry)

    cutoff = today - datetime.timedelta(days=14)
    log = [e for e in log if datetime.date.fromisoformat(e["date"]) >= cutoff]
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)

    print(f"today: {len(cards)} cards read, {len(matches)} match {words}")
    for c in sorted(matches, key=lambda c: (c.get("pan") or "", c.get("rank") or 999)):
        print(f"  [{c.get('pan')} #{c.get('rank')}] {c.get('title')} - {c.get('author', '')} ({c.get('kind')})")

    # Topics on more than one day: same matching word seen on 2+ dates.
    days_by_word = {}
    for e in log:
        for w in words:
            if w in (e.get("title") or ""):
                days_by_word.setdefault(w, set()).add(e["date"])
    repeated = sorted(((w, len(d)) for w, d in days_by_word.items() if len(d) > 1), key=lambda x: -x[1])
    if repeated:
        print("seen on several days (last 14):", ", ".join(f"{w} {n}d" for w, n in repeated))
    print(f"log: {len(log)} entries in {log_path}")


if __name__ == "__main__":
    main()
