---
name: threads-coupang-start-here
description: Start here for running one Threads info account automatically (basic free version) - pick one topic, set up the work folder, the order of the 5 skills, and the safety rules that keep the account from being restricted. 스레드 정보 계정 자동 운영 시작 안내(기본판).
---

# Threads Info Account: Start Here (basic)

This skill is the map. It does not do work itself; it tells the user which skill to use next and checks what each step needs.

The account runs on **one topic** (example: government support programs people can actually apply for). Every day it posts a few items and does a few short engagement rounds at random times. Posts use official sources only. Everything runs on the user's own PC with a logged-in browser driven by an automation tool.

## Step 0: pick one topic (before anything else)
Ask the user once:
- Which subject do you know well or follow every day? (money and support programs, home life, living alone, parenting, work, pets ...)
- Will you add Coupang Partners links later? (yes / no / not sure)

Suggest 2-3 topics that fit the answers, one line each, plus where facts can be checked (official sites). The user picks **one**. Write it into `config.json` (`concept`, `keywords.research`, `official_domains`). Do not write posts before the user picks.

## The order
| Step | What | Skill | Needs |
|---|---|---|---|
| 0 | Pick one topic | this skill | nothing |
| 1 | Look at popular posts on that topic | `threads-viral-post-research` | browser automation tool |
| 2 | Check official sources, write post 1/2 and 2/2, add to the queue | `threads-info-post-writer` | web search / page open |
| 3 | Install the random-time runner and register the scheduler | `threads-random-time-poster` | Python, Claude Code (`claude -p`), browser automation tool |
| 4 | Engagement rounds (reply to comments on my posts, replies, follows) | `threads-engagement-routine` | browser automation tool |
| 5 | Nightly report | `threads-daily-report` | browser automation tool |

Any tool that drives a logged-in browser works: Claude in Chrome, Playwright MCP, or similar. Screen steps are in `threads-random-time-poster/references/browser_steps.md`.

## First check (10 minutes)
1. The Threads account exists and is **logged in** in the browser profile the tool uses. The user logs in; the skill never types a password.
2. One topic is chosen (step 0).
3. If Coupang Partners will be used: the user has joined and registered this Threads account as an activity channel, and has read the terms.
4. The PC can stay on during the day (the runner only works while the PC and browser are on).
5. `python --version` and `claude --version` work in a terminal.

## Work folder (once)
```
threads-ops/
  config.json          from threads-random-time-poster/scripts/config.example.json
  prompt.md            from threads-random-time-poster/references/prompt_template.md
  report_prompt.md     from threads-daily-report/references/nightly_prompt_template.md
  references/browser_steps.md
  scripts/             due.py mark.py run.ps1 run.sh report_history.py
  data/queue.json      posts waiting to be published
  plan/                today's random-time plan (made automatically)
  logs/
```

## Daily amounts (basic, conservative)
Start small and keep it there. The defaults in `config.example.json` are already on the safe side; do not raise them in the first weeks.
- Posts: 1-2 a day.
- Replies to other people's posts: up to 10 a day.
- Follows: up to 5 a day.
- 20-40 seconds between people, one reply per person per day.
- Nothing before 08:30 or after 23:30.

## Safety rules (always)
1. **Stop on any warning.** If Threads shows a restriction or "too fast" warning, stop for the day (`python scripts/mark.py stop "<message>"`). Next day, start again with smaller numbers. Never post missed items in a burst.
2. **No begging.** No "follow back", "like please", no links in replies.
3. **Skip conflict.** No politics, gender or generation fights, adult, gambling.
4. **Official sources only.** Amounts, eligibility and dates come from the official site, checked on a date you record. If a unit is unclear, leave the number out.
5. **No made-up experience.** Never write "I applied" or "I used it" unless the owner really did.
6. **Coupang disclosure.** `[광고]` on post 1/2, the link only once in 2/2, and at the top of 2/2: "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
7. **No double posts.** Only post queue items whose status is "대기", check the profile after posting, retry once at most.
8. **Logins are human.** If logged out, record a failure and stop.
9. **If someone asks "are you AI / a bot?"**, do not answer; hand it to the owner. Never deny falsely. The owner checks the Threads terms on automation and is responsible for them.

## Writing style (short)
- Posts (1/2, 2/2): casual Korean (반말, 음슴체). Do not end post sentences with "~요". The first line is the title.
- Replies: short, casual. If the other person uses 존댓말, reply in short 존댓말.
- No hype, no guarantees, no "do it now or miss out".

## First run
1. `threads-viral-post-research` on 2 keywords of the chosen topic.
2. `threads-info-post-writer`: add 2 posts to the queue.
3. Install `threads-random-time-poster`, then `python scripts/due.py --show` to see today's plan.
4. Run the first two days **by hand in a chat session**, one round at a time. Turn on the scheduler only after that.
5. At night, `threads-daily-report`.

## Output
The topic options and the chosen topic, the readiness check, the config numbers to start with, and the first-run order.

---
만든이: sphereai.work (https://sphereai.work)
