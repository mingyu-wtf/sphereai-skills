---
name: naver-ai-briefing-writing
description: Write a Naver blog post with a clear structure that search and the Naver AI briefing can quote - summary, question headings, FAQ, sources. 네이버 AI 브리핑에 인용되기 쉬운 블로그 글 구조.
---

# AI-Briefing-Friendly Writing

Use this to **write one post** with a clear structure, so each part can be read on its own. It does **not** guarantee a ranking or home-feed placement; Naver decides that.

## Post structure
1. **Title**: the main keyword first (see `naver-blog-topic-picker`).
2. **Summary**: 2-3 complete sentences at the very top that make sense on their own.
3. **Sections**: each section has a heading written as a question people search, and the answer in its first sentence, then a plain explanation.
4. **FAQ**: 2-3 short questions with short answers.
5. **Sources**: the name of each source, and a URL only if you opened it. Never invent a URL.
6. **Related posts**: links to your own public posts.

## Rules
- Write for readers, not for the algorithm. The keyword appears naturally.
- Check every number and date against a source. If unsure, write "about" or "reported".
- Say clearly near the top if the post has paid or affiliate links.
- No fake personal experience, no invented quotes, no copied text.
- AI-made images must have the AI mark switched on in the editor (see `naver-editor-assembly`).

## Before publishing
- [ ] The keyword is in the title and the summary.
- [ ] Each section answers its heading in the first sentence.
- [ ] Numbers and dates were checked; sources are real.
- [ ] 10 or more tags, written without hyphens (a hyphen can break tag input).

## Output
The full post as ordered blocks plus 10 or more tags, ready for `naver-editor-assembly`. Ask the user to read the facts first.

---
만든이: sphereai.work (https://sphereai.work)
