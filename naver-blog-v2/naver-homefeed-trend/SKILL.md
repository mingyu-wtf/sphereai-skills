---
name: naver-homefeed-trend
description: Read today's Naver home feed (지식, 추천 tabs) with a separate view-only profile, keep cards on your subject and turn them into post ideas. Read only, free. 네이버 홈판 오늘의 흐름.
---

# Naver Home Feed Trend (v2)

Use this to see **what is being shown to people on the Naver home feed today**, so that the next post rides a topic that is already getting attention. It reads the mobile home page tab by tab, keeps the cards that match the user's subject, and records them so trends can be compared across days.

## Why a separate profile
The home feed is personalised. If you read it with the account you write posts with, it mostly shows your own interests and neighbours back to you. Use **a second browser profile logged in to a different Naver account** (a family or spare account the user owns) and use it **only for reading**. This gives a less one-sided view. It is still a personalised feed, not an official ranking; say so in the output.

## Hard rules
- View only. Never like, comment, follow, add neighbours, subscribe or write with the reading profile.
- Never log in to any account for the user. If the reading profile is logged out, stop and tell the user.
- Never copy a feed post. Use it only as a signal of what people are curious about, then answer that curiosity with first-hand sources.
- No numbers that the page does not show. The feed does not show view counts; do not invent them.

## Needs
- Aside with two profiles: the writing profile and a reading profile (a different Naver account). The reading profile has its own REPL tool (for example `mcp__aside-<profile>__repl`, or `aside repl --account <profile>` in a terminal).
- `references/homefeed_scan.js` and `references/merge_homefeed.py` (Python 3, no extra packages).

## Steps
1. Ask once: the blog's subject words (for example `우주, 행성, 별, 은하, 블랙홀, 소행성, NASA`) and which tabs to read. Default tabs: `지식` and `추천`. Other tab names on the page: 뉴스, 엔터, 스포츠, 경제, 클립, 패션뷰티, 여행맛집, 카·테크, 리빙푸드, 건강, 게임, 웹툰, 우리동네.
2. In the **reading** profile's REPL, paste the text of `homefeed_scan.js` and run:
   ```js
   const cards = await hfScan({ pans: ['지식', '추천'], scrolls: 6 });
   console.log(JSON.stringify(cards));
   ```
   The script switches the page to a phone-size view, clicks each tab, scrolls, and reads only that tab's cards (every tab is loaded side by side in one page, so it reads each tab's own boxes). Each card: `pan, rank, title, author, url, kind` (blog / clip / influencer / news / cafe). `rank` is the order on screen; lower = shown higher.
3. Save the printed JSON to a file (for example `cards_today.json`) and run
   `python -X utf8 references/merge_homefeed.py cards_today.json homefeed.json "우주,행성,별,은하"` (`-X utf8` keeps Korean readable in a Windows console).
   It keeps only cards that match the subject words, adds today's date, removes repeats, keeps the last 14 days, and prints today's matches plus topics that appeared on more than one day.
4. For the 2-3 best matches (highest on screen, or repeated across days), open them with `hfReactions(url)` in the same reading REPL. It reads the visible like/comment numbers (if shown), the first lines and the subheadings. Look at **how** the title is built (short twist, number, question, "~였습니다") and how the first three lines pull the reader in. Do not press anything on the page.
5. If no card matches the subject today, say so plainly and hand over to `naver-blog-topic-picker-v2` (news and search words instead).

## Output
- Today's matching cards: tab, rank, title, author, kind.
- Topics seen on more than one day (from homefeed.json).
- For the opened cards: title pattern, first-line hook, subheading style, visible reactions.
- 1-3 topic ideas for today, each with: the question readers seem to have, a first-hand source to check (agency, journal, official data), and a draft title that mixes the feed style (short twist) with search words (name + number/date).
- A one-line note that this is one account's personalised feed, not an official ranking.

## Running it on a schedule (optional)
If the user wants this every day, run steps 2-3 at fixed times (for example 05, 10, 15, 20 o'clock) and keep homefeed.json. Comparing days shows which topics stay up and which fade. Each run should still end with a short report to the user.

---
만든이: sphereai.work (https://sphereai.work)
