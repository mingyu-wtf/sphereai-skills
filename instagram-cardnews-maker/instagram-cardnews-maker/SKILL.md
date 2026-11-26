---
name: instagram-cardnews-maker
description: Make Instagram carousel card news (1080x1350) from a topic, an article, notes or a product - a warm cream review/info design by default (navy title blocks, orange number badges, product cards with price and review count, comparison table), or photo-background styles or your own design picked from Pinterest references, 10 card types, plus caption, 3-5 hashtags, first comment and alt text. Free, no API key. 주제, 글, 메모, 상품으로 인스타 카드뉴스와 캡션, 해시태그까지.
---

# Instagram Card-News Maker

The user gives a topic, a link, pasted text, their own notes, or a product. You (the agent) research or read it, plan a carousel that people save and share, write `cards.json`, render the cards and write the caption. Everything is free local tooling: Python, a headless browser for rendering, and ffmpeg (only for the review sheet). No paid API, no login, no automatic upload.

> If the source is a YouTube video and the user wants clips from it, the sibling skill **youtube-cardnews-maker** fits better. This skill is for everything else.

## Setup (once)
```
pip install playwright
```
- Rendering uses an installed Chrome/Edge. If neither exists: `playwright install chromium`.
- `ffmpeg` on PATH is optional (only for `_preview.png`). Windows: `winget install ffmpeg`.
- A Korean font is found automatically (Pretendard, Noto Sans KR, Malgun Gothic, Nanum). Otherwise pass `--font path/to/font.ttf`.
- For the intended look of `cream`, install the free font **Paperlogy** (Medium, Bold, ExtraBold). The script picks it up from the system fonts, or pass `--font-dir <folder with Paperlogy-5Medium.ttf, -7Bold.ttf, -8ExtraBold.ttf>`.

Run scripts from this skill's `scripts/` folder. Work in `work/<short-topic-name>/` (no `#` in the path).

## Steps

1. **Ask only what you cannot decide yourself** (one message):
   - topic or material (link, pasted text, notes, product page)
   - who it is for (e.g. 사회초년생, 자취생, 초보 부모) - this decides the words and examples
   - account handle to print on the cards (optional)
   - **design**: `cream` (default - cream background, navy title blocks, orange accents, rounded photos; made for product reviews and info posts), photo-background styles (`bold`, `dark`, `pastel`, `photo`), or "my own design" -> follow `references/design_from_reference.md` once (Pinterest references -> the user picks -> `design.css`). If the account already has a `design.css`, reuse it.
   - their own photos (optional) - put them in `work/<name>/img/`
   Defaults if the user does not care: `cream`, 1080x1350, 7-8 cards.

2. **Gather facts.** Read the material fully. For a bare topic, look it up and open the pages you rely on; prefer official or primary sources for numbers, prices, dates and rules. Write down each source (name + URL) for `sources`. Do not use a number you could not confirm.

3. **Plan the carousel** before writing (show the user a one-line-per-card outline if the topic is sensitive or they asked to review):
   - cover = a specific promise or problem, with a number when possible
   - card 2 = why it matters / the common mistake (keeps people swiping)
   - middle = one message per card, most useful first, 2-3 different card types for rhythm
   - closing = one-line takeaway + save/share/follow
   See `references/cards-format.md` for the card types, fields and limits.

4. **Write `work/<name>/cards.json`** (format in `references/cards-format.md`): cards, `caption`, `hashtags` (3-5), `first_comment`, `sources`, and one `alt` sentence per card. Korean, short spoken sentences, no emoji on cards, `**key word**` for one or two words per title.

4-1. **Images.** Each card can take `"image": "img/<file>"`, all different, each matching what that card says.
   - `cream`: the photo sits in a rounded box (cover bottom, product middle, text-only cards fill their empty lower part with it). Products and the cover need one; give one to text-only cards whose lower half would be empty.
   - **Products are never cut off.** On `product` cards the script compares the photo's shape with the slot (about 936x690, 4:3 landscape): close -> it fills the slot; different -> the whole photo is shown and the leftover sides are filled with a soft blurred copy. `check.py` lists product photos whose shape does not match.
   - So make product photos **4:3 landscape with the whole product in frame and about 15% empty margin around it** (say this in every product image prompt). Then they fill the slot and nothing is lost. `"fit": "cover"` / `"contain"` on a card forces one behavior; `"focus": "50% 40%"` moves the crop on cover-filled photos.
   - other styles (`image_mode: full`, default there): the image fills the card behind a dark fade and the text sits on top.
   - Best: the user's own photos (product, place, screenshots they own).
   - Otherwise generate them with the image tool the user has: write one prompt per card into `work/<name>/image_prompts.md` - a real-looking photo of the card's subject, **no text, letters or logos inside the image**, calm area in the middle/bottom where the text will sit, same look across the set (same light, lens, color grade). Generate, save as `img/01.jpg ...`.
   - No image tool? Ask the user for photos, or set `"image_mode": "inset"` / leave `image` empty for plain cards.
   - Tune readability with `"scrim"` (0.45 light fade - 0.8 heavy fade, default 0.62).

5. **Check** - `python scripts/check.py work/<name>`. Fix every `FIX` line and re-run until `0 to fix`. Read the `NOTE` lines and fix the ones that apply.

6. **Render** - `python scripts/render_cards.py work/<name> [--style cream|bold|dark|pastel|photo] [--accent "#ffe14d"] [--handle "@<your-account>"] [--size 1080x1080] [--image-mode full|inset]`
   - `full` (default): image behind the text. `inset`: image as a rounded box above the text. `design_css` in `cards.json` applies the account's own design on top of the base style.
   - Output: `cards/card_01.png ...`, `cards/_preview.png` (all cards on one sheet), `caption.txt` (caption + hashtags + first comment + alt texts + sources).
   - **Open `_preview.png` and every card.** If the script warns that a card does not fit, shorten that card and render again. Check that the cover reads at thumbnail size (look at it in the preview sheet) and that no two neighbouring cards look the same.

7. **Deliver**: list the full paths of the cards, the preview sheet and `caption.txt`. Tell the user how to post: upload the cards in order as one carousel post, paste the caption, add each alt text under "Advanced settings > Write alt text", post the first comment right after publishing. Do not upload anything yourself.

## Product review posts (e.g. affiliate)
- Use `cover` -> one `product` card per item (number badge, name, photo, price, review count, 2 check lines, optional one-line review quote) -> `table` (side-by-side comparison + navy button such as "링크는 첫 댓글에" + `disclosure` line) -> optional `checklist` / `closing`. See `references/example_cream_cards.json`.
- Prices and review counts change: check them right before posting and add a note like "※ 가격, 후기 수는 확인 시점 기준".
- Review quotes must be real reviews you read, passed on as "~라는 후기가 많음"; never invent them. Product photos: the user's own or ones they made, not the shop's images.
- Affiliate disclosure goes on the last card (`disclosure`) and at the start of the caption.

## Images: what is allowed
- The user's own photos, images they generated, or images with a license that allows reuse.
- Never use images found on the web, Pinterest pins or product photos from shops without permission. Pinterest is only for design direction.
- Korean text is always drawn by the script on top of the image, never generated inside it.

## Rules
- **Facts only**: every number, price, date and rule must come from the material or a source you opened; list them in `sources`. Opinion posts can set `"needs_sources": false`.
- **No hype or bait**: no "무조건", "100%", "기적", fake urgency, or "댓글 달면 보내 줄게" style engagement bait. Instagram down-ranks it and readers stop trusting the account.
- **Ads must be labeled**: if the post promotes a product with an affiliate link or payment, start the caption with "광고" or "협찬" (or use Instagram's paid-partnership label) - this is a legal requirement in Korea, not a style choice.
- Credit people you quote. Do not present someone else's content as the user's own.
- Never put API keys, cookies or logins in any file. This skill needs none.

## Troubleshooting
- `No browser could be started` -> install Chrome, or `playwright install chromium`.
- Korean shows as boxes -> pass `--font` with a Korean `.ttf`/`.otf`.
- `content does not fit` -> shorten the title/body or split the card in two.
- No `_preview.png` -> ffmpeg is missing; open the cards one by one instead.

---
만든이: sphereai.work (https://sphereai.work)
