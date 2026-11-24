---
name: naver-blog-photo-post
description: Turn trip photos plus one line ("it was great") into a full, fact-checked Naver blog post - finds the place, checks hours, prices and parking on Naver Place, reads visitor reviews and search words, sorts the photos and writes captions, then hands off to editor assembly. 사진만 보내면 블로그 글 자동 작성(블로그 자동화 v3).
---

# Photos to Blog Post

The user comes back from a trip, sends the photos and one short line such as "너무 좋았어". This skill does the rest of the writing work: it finds out what the place is, checks the facts, reads what other visitors said, picks the search words people actually use, and writes a post around the user's own photos. It does not invent experiences the user did not have.

## What the user sends
- Photos (phone photos are fine, any order). A folder, or attachments in the chat.
- The place: a Naver Map share link (naver.me/...), or the shop name and address. If none is given, ask once. Do not guess the place from the photos alone.
- Their own impression, even one line ("너무 좋았어", "커피가 부드러웠어", "화장실이 호텔 같았어").
- Optional: which blog category to post in.

## Steps
1. **Fix the place.** Open the map link or search the name + address. Write down the official name, address and Place URL. If two places match, ask.
2. **Check facts on Naver Place** (Aside, read only): opening hours, regular days off, menu and prices, parking, toilets, seating, reservation links. Note the date you checked. Anything you could not confirm stays out of the post.
3. **Read other visitors.** 10-15 Place reviews and blog reviews. Sum up what people liked and what they found disappointing, in your own words, without copying sentences.
4. **Search words.** Note the autocomplete and related searches for the place name and area (for example "강화도 카페", "OO 주차", "OO 메뉴 가격"). Use them in the title and subheadings where they fit naturally.
5. **Sort the photos.** Look at every photo and give it a scene name in visiting order (entrance, sign, inside, menu, food, view, toilet...). Drop blurry and duplicate shots. Blur faces of other people, and never post receipts, card numbers or phone screens as they are - move prices from a receipt into a table instead. Read `references/photo-rules.md`.
6. **Write.** Follow `references/post-shape.md`: a one-line summary box at the top, intro that starts from the user's impression, subheadings that answer what readers search for (hours, price, parking, how to get there), one caption line under each photo, a small table for prices, "good / not so good" from reviews, a short FAQ, a map. The user's feelings come only from what the user said - quote or paraphrase it, never add new ones.
7. **Self-check** before showing the draft:
   - every number (time, price, distance) has a source and a check date
   - no sentence claims an experience the user did not mention
   - no face, receipt or personal info visible in photos
   - sentence endings match the blog's voice (default: polite 합니다체; follow the user's own blog if they have one)
8. **Show the draft** with the photo order. After the user says yes, hand off to `naver-editor-assembly` and `naver-blog-scheduling`. Publishing waits for the user's yes.

## When the user adds more later
"Write the review part more carefully" means: reread the reviews and the user's words, expand only that section, and update the post in the editor's edit screen rather than posting again.

## Output
- `post.md` (or the builder file the assembly skill uses) with photo file names in order
- `photos/` renamed in visiting order (01_gate.jpg, 02_sign.jpg ...)
- `facts.md`: every fact with its source URL and check date
- a short note listing what could not be confirmed

---
만든이: sphereai.work (https://sphereai.work)
