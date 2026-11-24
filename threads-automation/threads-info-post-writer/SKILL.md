---
name: threads-info-post-writer
description: Write one Threads info post (basic version) - check amount, eligibility and dates on the official site, write post 1/2 and 2/2 (how to apply), and add it to the queue. Includes the Coupang Partners disclosure rules. 스레드 정보 글 쓰기(기본판).
---

# Threads Info Post Writer (basic)

Makes one post for an info account. Example topic: government support programs. The same steps work for home, saving or living-alone tips.

## Steps
1. **Pick a topic** that is not already in the queue or posted. Skip programs whose application period is over.
2. **Check the official source.** Open the official page (from `config.json` `official_domains`) and read the amount, who can apply, the period and where to apply.
   - Do not use numbers from blogs, cafes or news summaries.
   - If a unit is unclear (per day or total, per month or per year), leave the number out.
   - Record the date you checked.
3. **Write**:
   - `a` = post 1/2: the first line is the title, then who / how much / until when. Ends with " 1/2".
   - `b` = post 2/2: how to apply, and "공식 누리집 기준 YYYY.MM.DD 확인" at the end. Ends with " 2/2".
   - Casual Korean (반말, 음슴체). Do not end sentences with "~요". Under 500 characters each. No personal experience.
4. **Check by reading it once**: no "~요" endings, numbers match the source, no made-up experience, no hype.
5. **Add to the queue** (`data/queue.json`) with status "대기":
```json
{"id":"g12","title":"program name","status":"대기","verified":true,
 "source":["https://<official page>"],"checked_on":"YYYY-MM-DD","verify_before_post":"",
 "a":"...1/2","b":"...2/2"}
```
   If the facts may change before posting, put the official page in `verify_before_post`; the runner checks it again right before posting.

## Coupang Partners posts (only if the user uses it)
- `[광고]` at the start of 1/2. The link only in 2/2, once.
- At the top of 2/2, the full disclosure: "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다." (`config.json` `coupang.disclosure`).
- Pass on reviews you actually read ("후기에 ~했다더라"). No claims of effect or "lowest price".
- Do not reuse Coupang's images.

## Links
Info posts have no link by default. If one is needed, put it once at the end of 2/2 and say in one line what it is.

## Output
The queue items added (id, title, official page, check date), and topics dropped because they could not be confirmed.

---
만든이: sphereai.work (https://sphereai.work)
