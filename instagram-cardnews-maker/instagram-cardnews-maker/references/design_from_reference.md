# Account design from a reference (Pinterest -> user picks -> design.css)

The four built-in styles (`bold`, `dark`, `pastel`, `photo`) work right away. When the user wants a look of their own - or asks "make it look like the accounts I like" - do this once per account, then reuse the result for every post.

## 1. Collect references
- With the browser automation tool you have, open `https://www.pinterest.com/search/pins/?q=<query>` (no login needed for search results).
- Run 3-4 queries that fit the topic and audience, for example: `instagram carousel design`, `card news design korean`, `카드뉴스 디자인`, `정보 카드뉴스`, `minimal infographic carousel`, `photo carousel text overlay`.
- Screenshot the results into `work/<name>/design_refs/round_<n>/` and pick **6-9 candidates that differ from each other** (white info cards, photo with text overlay, dark premium, pastel, bold typography, magazine). Note each pin URL.

## 2. Let the user choose
- Show the candidates numbered on one sheet, each with a one-line note ("4 - full photo, dark fade, big white title, yellow marker").
- **Do not build anything before the user picks.** If nothing fits, change the queries and collect again.
- Mixes are fine: "layout of 2, colors of 5".

## 3. Turn the pick into `design.css`
- Copy only the **direction**: layout, margins, type scale, weights, color palette, highlight style, corner radius, how text sits on the photo. Never copy the reference's images, illustrations, logos, text or brand names.
- Write `work/<name>/design.css` that overrides the built-in classes (it is injected last into every card):
  - `body` (background, color), `h1` (cover title), `h2` (card titles), `p` (body), `.hl` (highlighted words), `.kick` (cover label), `.num` (list number), `.v` (stat number), `.col` / `.col.on` (compare), `li` (checklist rows), `.box` / `.b` (closing buttons), `.hd` / `.pg` / `.pr` / `.sw` (handle, page count, progress bar, swipe arrow).
  - Sizes are for a 1080-wide card; use `px`.
- Set `"design_css": "design.css"` in `cards.json` (pick the closest built-in `style` as the base), render, and show the first set to the user. Adjust until they say it is right, then keep `design.css` for the account (copy it into each new work folder).
- Write `design.json` next to it: the chosen pin URLs and a short description of the look, so the next run can follow it.

## Text rules stay the same
Same limits, same no-emoji, no-hype and sources rules. Text is always drawn by HTML on top of the image - never ask an image tool to write Korean into the picture (it breaks).
