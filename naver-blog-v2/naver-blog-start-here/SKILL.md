---
name: naver-blog-start-here
description: Beginner map for running a Naver blog with free AI tools: which skill to use at each step and what you need installed. Start here. 네이버 블로그 자동화 시작 안내.
---

# Naver Blog: Start Here

This skill is the map. It does not do work itself; it tells the user which skill to use next and checks that they have what that step needs. Everything in this set is meant to run for free.

## The path
| Step | What you want | Skill | Needs |
|---|---|---|---|
| 1 | Decide what to write | `naver-blog-topic-picker` | Python only |
| 2 | Plan categories, rhythm, links | `naver-blog-strategy` | nothing |
| 3 | Write the post | `naver-ai-briefing-writing` | nothing |
| 4 | Make the images | `flow-nano-banana-images` | Aside + Google account (free plan, 0 credits) |
| 5 | Make the title card | `blog-title-card` | Python + Chrome |
| 6 | Put it into the editor | `naver-editor-assembly` | Aside + Naver login |
| 7 | Schedule or publish | `naver-blog-scheduling` | Aside + Naver login |
| 8 | See what worked | `naver-blog-measurement` | Aside + Naver login |

Steps 1-3 and 5 work without any browser automation. Steps 4, 6, 7 and 8 drive a real browser through **Aside** and need an already logged-in profile.

## First-time check (5 minutes)
1. Ask: do you have a Naver blog? Which categories? How many posts a week can you keep?
2. Ask: is Aside installed and is a browser profile logged in to Naver and to Google? If not, steps 1-3 and 5 can still be done by hand-off: the skill produces files and text, and the user pastes them.
3. Ask: does your Google Flow plan show "0 credits" for image generation? If it shows a cost, stop before step 4 and talk it over.
4. Suggest the first small run: one post, one topic, scheduled for a far date or left as an unpublished editor tab.

## Rules for the whole set
- Free only: never click upgrade or buy buttons; never enter passwords for the user.
- Be honest: no promise of ranking, home-feed placement or income. Check facts and name sources.
- Publishing is public: always read the settings back and wait for the user's yes before confirming.
- Disclose paid or affiliate links in the post.

## Output
A short plan for the user's first post: which skills in which order, what to prepare, and the next question to answer.

---
만든이: sphereai.work (https://sphereai.work)
