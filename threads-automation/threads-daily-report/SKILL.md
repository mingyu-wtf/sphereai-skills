---
name: threads-daily-report
description: Threads nightly report, read only - followers, views and per-post reactions, today's activity against the limits, change from yesterday, and problems (failed slots, warnings, low queue). 스레드 하루 보고.
---

# Threads Daily Report

Once a night, see whether the automation ran and what did well. **Read only**: no posting, replying, following or deleting.

## Included
- `scripts/report_history.py` - `collect` (today's local logs) / `save` (store measurements and compare with yesterday).
- `references/nightly_prompt_template.md` - prompt and scheduler example for running it every night.

## Steps
1. `python scripts/report_history.py collect` - today's engagement counts, posts, queue left, failed or skipped slots, alerts, yesterday's values.
2. Read in the browser: my profile (check the account, follower count), views / likes / comments / reposts of today's posts. If a number cannot be read, use null.
3. `python scripts/report_history.py save --json '{"followers":N,"views_total":N,"posts":[...]}'`.
4. Write `logs/reports/report_YYYYMMDD.md`:

```
## YYYY-MM-DD
- Followers N (+N vs yesterday)
- Views N (+N vs yesterday)

| Time | Title | Views | Likes | Comments | Reposts |
|---|---|---|---|---|---|

Best post: (title)
Activity vs limits: posts n/limit, replies n/limit, follows n/limit, comment replies n
Problems: (failed slots, warnings, held posts, queue 3 or fewer)
```

## Rules
- Numbers only as read on screen.
- Do not like or follow while measuring.
- After a day with a warning, do not raise the numbers the next day.
- If the queue has 3 or fewer posts, write more before the next day.

## Output
One report file and a one-line summary (followers +/-, best post, problems yes/no).

---
만든이: sphereai.work (https://sphereai.work)
