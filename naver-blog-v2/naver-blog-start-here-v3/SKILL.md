---
name: naver-blog-start-here-v3
description: Beginner map for running a Naver blog with free AI tools, v3 - send trip photos and one line and get a fact-checked visit post, or start from what the home feed shows today; which skill to use at each step and what you need. 네이버 블로그 자동화 시작 안내(v3).
---

# Naver Blog: Start Here

This skill is the map. It does not do work itself; it tells the user which skill to use next and checks that they have what that step needs. Everything in this set is meant to run for free.

## The path
| Step | What you want | Skill | Needs |
|---|---|---|---|
| 1a | See what the home feed shows today (v2) | `naver-homefeed-trend` | Aside + a second, view-only Naver account |
| 1b | Decide what to write (feed, then news, then search words) | `naver-blog-topic-picker-v2` | Python; Aside for step 1a |
| 2 | Plan categories, rhythm, links | `naver-blog-strategy` | nothing |
| 3 | Write the post | `naver-ai-briefing-writing` | nothing |
| 3b | Write a visit post from your own photos + one line (v3) | `naver-blog-photo-post` | photos, place link; Aside for fact checks |
| 4 | Make the images | `flow-nano-banana-images` | Aside + Google account (free plan, 0 credits) |
| 5 | Make the title card | `blog-title-card` | Python + Chrome |
| 6 | Put it into the editor | `naver-editor-assembly` | Aside + Naver login |
| 7 | Schedule or publish | `naver-blog-scheduling` | Aside + Naver login |
| 8 | See what worked | `naver-blog-measurement` | Aside + Naver login |

Steps 1b-3 and 5 work without any browser automation (1b then skips the feed check). Steps 1a, 4, 6, 7 and 8 drive a real browser through **Aside** and need an already logged-in profile.

**What is new in v3:** step 3b. After a trip, the user sends the photos, the place (Naver Map link or name + address) and one line like "너무 좋았어". The skill checks hours, prices and parking on Naver Place, reads visitor reviews and search words, sorts and captions the photos, and writes the whole post. Facts come from sources, feelings come only from the user. With photos, steps 1-5 can be skipped: go 3b, then 6 and 7.

**New in v2:** step 1a. A second browser profile, logged in to a different Naver account the user owns, reads the home feed (지식, 추천 tabs) **without touching anything**, so topic picking starts from what people are being shown today. The writing profile and the reading profile are never mixed.

## First-time check (5 minutes)
1. Ask: do you have a Naver blog? Which categories? How many posts a week can you keep?
2. Ask: is Aside installed and is a browser profile logged in to Naver and to Google? For step 1a, is there a second profile with a different Naver account to use for reading only? If not, skip 1a. Without Aside at all, steps 1b-3 and 5 can still be done by hand-off: the skill produces files and text, and the user pastes them.
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
