# cards.json format and writing rules

```json
{
  "style": "cream",
  "accent": "#ffe14d",
  "handle": "@<your-account>",
  "size": "1080x1350",
  "image_mode": "full",
  "scrim": 0.62,
  "design_css": "",
  "cards": [
    {"type": "cover", "kicker": "저장 필수", "title": "월급날 **10분**이면 끝나는 돈 정리", "sub": "통장 4개로 나누는 법", "image": "img/cover.jpg", "alt": "..."},
    {"type": "text", "title": "왜 통장을 나눠야 할까", "body": "..."},
    {"type": "list", "num": 1, "title": "월급 통장", "body": "...", "image": "img/01.jpg"},
    {"type": "stat", "value": "73%", "label": "...", "title": "...", "body": "..."},
    {"type": "compare", "title": "...", "left": {"head": "그냥 둘 때", "items": ["...", "..."]}, "right": {"head": "나눴을 때", "items": ["...", "..."]}},
    {"type": "checklist", "title": "오늘 할 일 3가지", "items": ["...", "...", "..."]},
    {"type": "quote", "quote": "...", "by": "..."},
    {"type": "closing", "title": "...", "body": "...", "cta": "저장해 두고 월급날 다시 보기"}
  ],
  "caption": "first line = hook\n\n2-4 short lines...\n\n당신은 몇 개로 나눠 써?",
  "hashtags": ["재테크", "월급관리", "통장쪼개기"],
  "first_comment": "optional: link or extra tip",
  "sources": [{"name": "Official site", "url": "https://..."}]
}
```

- `style`: `cream` (default: cream background, navy title blocks, orange number badges and accents, rounded photos - review and info posts), `bold` (white, black text, yellow marker), `dark`, `pastel`, `photo`. `accent` overrides the accent color.
- In `cream`, a cover `title` line break (`
`) starts a new navy block, and `**word**` inside it turns light orange. `focus` (e.g. `"30% 30%"`) moves the crop of a photo.
- `handle`: shown small at the top-left of every card (your account). Leave empty if none.
- `size`: `1080x1350` (4:5, default - takes the most screen space in the feed) or `1080x1080`.
- `image` (every card type): a path inside the work folder. With `image_mode: full` (default) the image fills the card behind a dark fade and the text sits on top; with `inset` it shows as a rounded box above the text (`text`/`list` only). Use a different image per card.
- `scrim`: darkness of the fade over images, 0.45-0.8 (default 0.62). Raise it if text is hard to read.
- `design_css`: path to the account's own design (see `design_from_reference.md`); injected last so it overrides the base style.
- `**word**` colors one or two key words. Markers do not count toward the limits. A new line (`\n`) is kept.
- `alt`: one plain sentence per card describing it; goes into `caption.txt` for Instagram's alt-text field.

## Card types

| type | use for | fields | limits (title / text) |
|---|---|---|---|
| `cover` | the hook - decides whether people swipe | `kicker` (2-6 chars label), `title`, `sub`, `image` | 26 / 40 |
| `text` | context, why it matters, one explanation | `title`, `body`, `image` | 22 / 120 |
| `list` | numbered items (top 5, step 1-2-3) | `num`, `title`, `body`, `image` | 22 / 100 |
| `stat` | one striking number | `value` (short, e.g. `73%`, `3배`), `label`, `title`, `body` | 22 / 80 |
| `compare` | before/after, A vs B, wrong/right | `title`, `left`/`right` with `head` + 2-4 `items` (18 chars each) | 22 / - |
| `checklist` | actions to take, things to check | `title`, 2-6 `items` (26 chars each) | 22 / - |
| `quote` | a line worth sharing | `quote`, `by` | - / 90 |
| `closing` | wrap-up + call to action | `title`, `body`, `cta` | 22 / 70 |
| `product` | one product (review posts) | `num`, `kicker`, `title` (name), `image`, `price`, `unit` (default 원), `reviews` (count), 1-3 `good` / `bad` lines (20 chars), optional one `quotes` line, `note` | 30 / - |
| `table` | side-by-side comparison of 2-5 items | `title`, `columns`, `rows` (one value per column; the first column gets a number badge), `cta` (navy button), `disclosure` | 14 / - |

## Structure that gets saved and shared
1. **Cover**: a specific promise or problem, with a number when possible ("3분", "5가지", "월 10만 원"). Mark the key word. The kicker says what kind of post it is ("저장 필수", "체크리스트", "몰랐던 사실").
2. **Card 2 continues the hook** - the reason to keep swiping (why it matters, the common mistake). Never put the conclusion on card 2.
3. **Middle cards**: one message per card, most useful first. Mix 2-3 card types so the rhythm changes (list -> stat -> compare).
4. **Closing**: one-line takeaway, then the save/share/follow box (drawn automatically) and the `cta` line. The caption asks one easy question.
5. 5-10 cards in total. Fewer, fuller cards beat many thin ones.

## Writing style
- Korean, short sentences, spoken tone, no emoji on cards.
- Only facts you can back up: numbers, dates, prices and rules come from the sources the user gave or official pages you opened. Put them in `sources`. If unsure, leave it out.
- No exaggeration ("무조건", "100%", "기적") - Instagram down-ranks bait, and readers stop trusting it.

## Caption (`caption.txt` is built from these)
- **First line = hook** (about 40-60 chars, it is all people see before "...더 보기"). Do not start with hashtags or the account name.
- Then 2-4 short lines with blank lines between; add what the cards could not hold (a tip, the context).
- End with **one easy question** that anyone can answer in a word ("몇 개로 나눠 써?").
- `hashtags`: **3-5** specific tags (topic + audience), not 30 generic ones.
- `first_comment`: optional - a link, a longer tip, or the sources.

## Photo fit (cream)
- `product` photos are fitted automatically so the product is never cut: same shape as the slot (about 4:3) -> fills it; other shapes -> whole photo with blurred sides. Make product photos 4:3 landscape with the product whole and ~15% margin.
- Other cards fill their slot (`fit: cover`); use `focus` to choose what stays in view, or `fit: contain` to show the whole photo.
