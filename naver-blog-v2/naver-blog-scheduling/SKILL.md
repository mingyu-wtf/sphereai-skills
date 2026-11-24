---
name: naver-blog-scheduling
description: Schedule a Naver post safely with Aside: category, 10+ tags, date and hour, read-back check, and a separate confirm after the user says yes. Needs Aside. 네이버 블로그 예약 발행.
---

# Naver Blog Scheduling (needs Aside)

Use this after `naver-editor-assembly` to set category, tags and a reservation time, and to publish or schedule **only after the user approves**. Scheduling or publishing is public and hard to take back, so the confirm step is always separate.

## Requirements
- Aside with a logged-in Naver profile, the editor tab with the finished post, and the helpers from `naver-editor-assembly` already loaded (`P`, `BLOG_ID`, `sleep`).
- Load `references/schedule_helpers.js` the same way (`(0,eval)(source)`).

## Steps
1. **Agree the slot first.** Ask the user for the date, hour and category, or propose the next free slot of their rhythm (see `naver-blog-strategy`). Use one fixed hour pattern (for example 09, 15 and 21) and never two posts in the same slot.
2. `await openPublishDialog()` opens the publish window.
3. `await setCategory("<category name>")` and read the returned category text.
4. `await addTags([...10 or more tags...])` (hyphens are removed because they can block tag input).
5. `const v = await setSchedule(2026, 12, 24, "15", "00")` sets the reservation and **reads back what the dialog shows**. Require `v.ok === true`: right date, hour, minute, "reservation" selected, at least 10 tags.
6. Take a screenshot of the dialog and show the user: title, category, date, hour, number of tags.
7. **Wait for the user's explicit yes** to that exact date, hour and category.
8. Only then run `await confirmPublish()`. If `v.ok` was false, fix the value and read it back again; never confirm a mismatch, and do not move to the next post, because the half-filled editor would be lost.
9. Check the result: the editor's "scheduled N posts" count went up by exactly 1 (`reservedCount()`), then open the blog's post list to confirm the title.

## Do not skip
- To test without publishing: do steps 2-6, then `await closePublishDialog()`. This changes nothing; the scheduled count stays the same.
- Never open a scheduled post through its edit URL; confirming there publishes it at once. Use the "scheduled posts" list.
- Check the scheduled count before and after. If a call timed out in the middle of confirming, read the count first, because the schedule may already have been set (a second attempt would duplicate it).
- If the date is in another month, the helper clicks the calendar's next-month arrow; typing the date directly does not work.
- Disclose paid or affiliate links in the post before scheduling.

## Output
A short report: title, category, date and hour, tag count, the scheduled count before and after, and the next free slot.

---
만든이: sphereai.work (https://sphereai.work)
