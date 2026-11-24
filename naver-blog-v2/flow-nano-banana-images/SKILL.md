---
name: flow-nano-banana-images
description: Make blog images free with Google Flow and Nano Banana on a free plan: 0-credit check, submit, download. Requires Aside. 구글 Flow 무료 나노바나나 블로그 이미지.
---

# Flow + Nano Banana Blog Images (free plan)

Use this to generate the images for a blog post in Google Flow with Nano Banana, **without spending credits**.

## Requirements
- **Aside** (browser automation tool) with a browser profile already logged in to the user's Google account. Never type or store a password; if Flow shows a login screen, ask the user to log in themselves.
- A Google account whose Flow plan shows **"0 credits will be used"** for image generation. Free plan limits can differ by account and can change; check on your own account first.

## Aside REPL basics
- Get the tab with `const t = await openTab('https://flow.google.com'); globalThis.P = t;` then use `P.evaluate(...)`, `P.locator(...)`, `P.mouse.click(x, y)`. Use `globalThis.name = ...` for values you reuse; a top-level `const` with the same name in a second call raises an error, so use a new variable name per call.
- `P.screenshot` sometimes times out; retry once or read the page text with `P.evaluate(() => document.body.innerText)`.
- The Flow screen may be in Korean (buttons such as "새 프로젝트", "이미지") and the model may be listed as "Nano Banana 2.1" or "Nano Banana Pro". Pick the Nano Banana entry that shows 0 credits.

## Safety check before every batch (do not skip)
1. Open `https://flow.google.com`, then **New project** (a new project per post keeps images separate).
2. Click the model chip next to the prompt box (it may read like "Video · 720p · 4s"). The popup opens on the Video tab, so click the **Image** tab first. Choose aspect ratio **1:1**, model **Nano Banana**, count **x1**.
3. The popup must say that generation uses **0 credits**. If it shows any credit cost, an upgrade prompt, or a paid plan, **stop** and tell the user. Never click upgrade or buy buttons.
4. Do not use the "agent" mode; use the plain image prompt box.

## Prompt
Write the prompt in English: describe the subject and the scene in one or two sentences, and end with `No people, no text, no logos, no watermark.` Do not ask for real people's faces or brand logos.

## Submit (what works)
1. Click the prompt box (a `textbox` div), type or paste the prompt.
2. **Click the send arrow with a real mouse click at its screen position.** A plain DOM `.click()` on the arrow button did not submit on a free account; `page.mouse.click(x, y)` did. Take a screenshot to find the arrow (bottom right of the prompt box).
3. Wait about 25-45 seconds per image (the second tile can appear 10 seconds after the first). A tile shows a percentage while it renders.
4. Submit a few at a time (3-4), then wait for all tiles to finish. Newest tiles appear at the top of the list, so map results to prompts in reverse submit order, and **look at each picture**.
5. If a tile fails, retry it.

## Download
**Download inside the page, not with a script outside it.** The tile image URLs need the logged-in browser session. A plain `requests`/`curl` download returns a login page (an HTML file saved as `.png`), so do not use it.

1. Collect the tile `<img>` URLs with the list scrolled to the top. Newer Flow pages use `flow.google.com/asb/...=s512-rw`; older ones use a signed `flow-content.google` URL (it expires).
2. For `flow.google.com/asb/` URLs, change the size suffix at the end to `=s0` to get the full-size file (`...=s512-rw` becomes `...=s0`). Leave signed `flow-content.google` URLs as they are.
3. Fetch each URL **inside the Flow tab** (same session cookies), turn the bytes into base64, return that to the REPL, and write the file there:

```js
// P = the Flow tab. url = one tile URL from step 2.
const b64 = await P.evaluate(async (u) => {
  const r = await fetch(u, { credentials: 'include' });
  if (!r.ok) return 'ERR ' + r.status;
  const b = new Uint8Array(await r.arrayBuffer());
  let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode(...b.subarray(i, i + 0x8000));
  return btoa(s);
}, url);
if (b64.startsWith('ERR')) throw new Error(b64);
await fs.writeFile('s1.jpg', Buffer.from(b64, 'base64'));   // full-size file is a JPEG
```
   The Aside REPL's `fs` has only async functions (`writeFile`, `readFile`, `copyFile`, ...), no `writeFileSync`, and it only accepts a **relative path**, which is saved inside the Aside session folder (an absolute path fails with "Path escapes Project and session roots"). After saving, copy the files from the session folder into your own image folder from a terminal.

4. Check each saved file: it must start with the bytes `FF D8` (JPEG) or `89 50` (PNG), and be larger than about 50 KB. A file that starts with `<` is a login page; stop and ask the user to log in to Google again.
5. If you need PNG, convert with Pillow (`Image.open(f).convert("RGB").save("s1.png")`).
6. Fetch one image per `evaluate` call or a few at a time; very large base64 strings in one call can make the REPL time out.

## Known limit: visible sparkle mark
On the free plan the downloaded images carry a small sparkle icon in the bottom-right corner. Keep important content away from that corner. `blog-title-card` crops it with a slight zoom. AI-made images must be marked as AI in the blog editor anyway.

## Check
Look at the images before using them. Redo any image that has letters or logos, a person or face, or the wrong subject.

## Output
A folder of image files and a note of which prompt made which file. Report the credit check result ("0 credits shown") to the user.

---
만든이: sphereai.work (https://sphereai.work)
