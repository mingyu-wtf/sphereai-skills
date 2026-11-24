---
name: naver-blog-measurement
description: Read your own Naver blog stats read-only with Aside - views, popular posts, traffic sources, search words - and pick the next 3 posts. Requires Aside and a Naver login. 네이버 블로그 통계 읽기.
---

# Naver Blog Measurement (needs Aside, read-only)

Use this to see how the blog is doing after you publish. It only reads statistics; it changes nothing on the blog.

## Requirements
- **Aside** with a browser profile logged in to the blog owner's Naver account. If the statistics call returns 401, ask the user to log in again; never enter a password.
- Open a tab on `https://blog.stat.naver.com/` so requests are same-origin.

## Steps
1. Set `globalThis.P = page` (the statistics tab) and run `references/stats_helpers.js` with `(0,eval)(source)`.
2. `const s = await dayStats("YYYY-MM-DD")` returns, for that date: the last 15 days of views, the top posts of the day, the traffic sources, and about 20 search words. **Use yesterday or earlier**; today is still being counted.
3. `await queryTotals("YYYY-MM-DD", 7, 15)` adds up search words over a week.
4. Put the numbers in a small table (date, views, top posts, traffic sources, top search words) and show it to the user.
5. **Pick 3 posts to write next**: choose 3 search words that bring visitors and have no post of their own yet.

## Honest limits
- Search-word statistics are for the whole blog, not per post.
- Very small counts (1-3) are noise.
- The statistics address is not an official public API and may change; if a field disappears, say so instead of guessing.
- Never share the raw output publicly: it contains your blog address.

## Output
A short note with the table and the 3 suggested posts.

---
만든이: sphereai.work (https://sphereai.work)
