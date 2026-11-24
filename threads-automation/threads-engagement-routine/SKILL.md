---
name: threads-engagement-routine
description: Threads engagement round (basic version) - reply to comments on my posts, follow back, a few short replies and follows within a small daily limit, and stop when Threads shows a warning. 스레드 소통 루틴(기본판).
---

# Threads Engagement Routine (basic)

One engagement round keeps the account active. The runner (`threads-random-time-poster`) calls this as its `engage` round; it can also be run by hand.

## Included
- `scripts/mark.py` - log actions, show today's counts and remaining limits, stop for the day. (Same file as in the runner skill; keep one copy in the work folder's `scripts/`.)

## Daily limits (basic)
| Item | Per day |
|---|---|
| Replies to other people's posts | up to 10 |
| Follows | up to 5 |
| Replies to comments on my posts | all, first in every round |

- `python scripts/mark.py targets` shows what is left today.
- 20-40 seconds between people. One reply per person per day.
- **If any restriction or warning screen appears**, stop right there: `python scripts/mark.py stop "<message>"`. No more engagement that day.

## Round order
1. `mark.py targets`. If stopped or nothing left, skip the round.
2. **Comments on my posts first**: open the activity tab and my last 5 posts, like each unanswered comment and reply in one short line.
3. **Follow back** new followers who are not bots, ads or conflict accounts.
4. **Replies**: search `https://www.threads.com/search?q=<keyword>&serp_type=default&filter=recent` with a keyword from `config.json` `keywords.engage`. Read the whole post, like it, reply.
5. **Follows**: personal accounts that post on the same topic. Look at their recent posts first; skip conflict posts.
6. Refresh and check that each reply is really there, then log it with `mark.py engage '<json>'`.

## Who to skip
Template or link-only accounts, marketing, course or shop accounts, and posts or accounts about politics, gender or generation fights, adult content or gambling.

## Reply basics
- Short and casual. Match the other person: 존댓말 if they use it.
- No links, no "follow back", no "follow me".
- No made-up experience ("I applied too").
- Do not repeat the same sentence.
- If someone asks "are you AI / a bot?", do not reply. Add them to `logs/reply_hold.json` (`hold`) and `mark.py alert` so the owner answers. Never deny falsely.

## Log format (`mark.py engage`)
```
{"type":"스하리","kind":"정보 글","url":"<post url>","reply":"<reply>","liked":true}
{"type":"내글댓글답","url":"...","reply":"..."}
{"type":"선팔","handle":"<handle>","source":"<keyword>"}
```

## Output
One line per round: comment replies n, replies n, follows n, skipped or failed and why.

---
만든이: sphereai.work (https://sphereai.work)
