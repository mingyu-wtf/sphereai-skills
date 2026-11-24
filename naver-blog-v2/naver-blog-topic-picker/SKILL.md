---
name: naver-blog-topic-picker
description: Pick a Naver blog topic from what people search. Look up a seed word in Naver autocomplete, choose a main keyword, and check it against your own posts. Free, no login. 네이버 블로그 주제 고르기(기본).
---

# Naver Blog Topic Picker (basic)

Use this to choose **what to write next** from what people really search. Free, no login, Python only.

## Steps
1. Ask the user for one seed word (a subject they know).
2. Run `python references/autocomplete_expand.py "<seed>"`. It prints the phrases Naver suggests for that word. On Windows set `PYTHONIOENCODING=utf-8`. The list has no search-volume numbers; do not invent any.
3. Pick one phrase as the **main keyword** for the post.
4. Check the user's own post titles for the same phrase. If a post already covers it, pick a different phrase.
5. Write a title that starts with the main keyword.

## Output
The suggested phrases, the chosen main keyword, any overlapping post, and a proposed title. Ask the user to approve the topic before writing.

---
만든이: sphereai.work (https://sphereai.work)
