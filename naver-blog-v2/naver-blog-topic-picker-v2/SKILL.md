---
name: naver-blog-topic-picker-v2
description: Pick today's Naver blog topic in order: home feed today, fresh news, search words, then a new format for your own popular post. Checks overlap. Free. 네이버 블로그 주제 고르기(v2).
---

# Naver Blog Topic Picker (v2)

Use this to choose **what to write next**. v2 adds the home feed check: first look at what people are being shown today, then fall back to news and search words.

## Order (stop at the first one that gives a good topic)
1. **Home feed today** - run `naver-homefeed-trend` (reading profile, view only). If a card in the blog's subject is high on screen or shows up on several days, take **its question**, not its text.
2. **Fresh news (last 48 hours)** - search the web for the subject plus "news", agency names, or "today". Keep only items with a first-hand source (agency, journal, official data) and a name/number/date people would search.
3. **Search words** - run `python references/autocomplete_expand.py "<seed>"` (on Windows set `PYTHONIOENCODING=utf-8`). It prints the phrases Naver suggests; there are no volume numbers, do not invent any.
4. **Own popular post, new format** - take one of the user's most-read posts of the last 14 days and plan the same subject in a different format: "10 questions", "7 numbers", "myths and facts", "timeline", "A vs B", "how to explain it to a child". Title, opening and subheadings must not repeat the old post; link the old post at the end.

## Checks for every candidate
- **Fact check possible?** If the key facts cannot be confirmed in a first-hand source, drop it. No invented numbers or quotes.
- **Overlap**: compare with the user's own post titles (last 30 days and anything on the same event). Same event = pick another.
- **Do not copy** the feed post or the news article. Write a new answer from the sources.

## Title
- Put the search words first (name + number or date), the curiosity after. About 40-55 characters.
- When the topic came from the home feed, borrow its **pattern** (short twist, question, number) but not its words.

## Output
The source of the topic (feed / news / search words / own post), the reader's question, 1-3 first-hand sources to use, overlapping posts if any, the main keyword, and a proposed title. Ask the user to approve the topic before writing.

---
만든이: sphereai.work (https://sphereai.work)
