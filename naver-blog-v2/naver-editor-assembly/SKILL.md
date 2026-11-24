---
name: naver-editor-assembly
description: Assemble a finished post in the Naver editor with Aside: title, pasted HTML, images, captions, AI-image mark, then verify. Stops before publishing. Needs Aside. 네이버 에디터 조립.
---

# Naver Editor Assembly (needs Aside)

Use this when the post text and images are ready (see `naver-ai-briefing-writing`, `flow-nano-banana-images`, `blog-title-card`) and must be put into the Naver blog editor. This skill stops before publishing; use `naver-blog-scheduling` for that.

## Requirements
- **Aside** (browser automation with a REPL) and a browser profile already logged in to the user's Naver account. Never type a password; ask the user to log in.
- The user's blog id (the part after `blog.naver.com/`). Store it in a variable, do not hard-code it.
- Image files must be reachable from the Aside session. Aside only reads files through the session's `uploads` folder, so you need the folder link below before any upload.

## One-time setup: the `uploads` folder link (Windows)
1. Pick one work folder, for example `C:\blog_work`, and put the post's images and the files in `references/` (`editor_helpers.js`, `schedule_helpers.js`) into it.
2. Open a separate PowerShell window and leave it running:
   `powershell -NoProfile -File references\make_uploads_junction.ps1 -Work "C:\blog_work" -Watch`
   It links `uploads` inside the newest 30 Aside session folders to the work folder, and again for each new session (Aside makes a new session folder each time it starts). Use `-Profile <n>` if your Aside profile folder is not `u\0` (the number after `u\`). Add `-All` to link every old session folder too (slow when there are thousands). A session folder that already has an `uploads` link is left as is; the window prints a note if it points somewhere else.
3. Check after the loader below is defined: `(await ldr('uploads/editor_helpers.js')).length` must be above 0. Before the link exists, the loader throws an error (`DOMException` on `.text()`) or returns an empty file, and the editor shows "upload failed". Look at the PowerShell window for a "linked:" line for the current session, wait a few seconds, and try again.
4. On Mac or Linux make the same link by hand: `ln -s <work folder> <session folder>/uploads`.

## Load the helpers
1. Open a new tab at `https://blog.naver.com/PostWriteForm.naver?blogId=<id>` and set `globalThis.P = page; globalThis.BLOG_ID = "<id>"`.
2. Define a small loader that reads a text file through the `uploads` link, then load the helpers with it:
```js
globalThis.ldr = async (rel) => {
  await P.evaluate(() => { if (!document.getElementById('__ldr')) { const i = document.createElement('input'); i.type = 'file'; i.id = '__ldr'; i.style.display = 'none'; document.body.appendChild(i); } });
  await P.locator('#__ldr').setInputFiles(rel);
  return await P.evaluate(async () => await document.getElementById('__ldr').files[0].text());
};
(0,eval)(await ldr('uploads/editor_helpers.js'));
```
   When all work is done, remove the hidden input (`document.getElementById('__ldr').remove()`); if it stays, it can be picked instead of the image upload input.
3. `await openEditor()` opens a blank editor and cancels the "draft in progress" popup.

## Assemble (in this order)
```
await setTitle("title text");
await addImage("uploads/card.png", "caption");      // the first image becomes the representative picture
await addHtml("<blockquote>...</blockquote>...");   // body blocks as HTML
await addImage("uploads/s1.png", "caption");
await addHtml("...");
await markAllAI();                                   // must show "1" for every image
```
- Split the work into calls under about 2 minutes. If the connection drops, re-attach the tab (list tabs, attach by `targetId`), reload the helpers, and **count what is already in the editor before adding more** so nothing is added twice.
- Body HTML that converts well: `<p style="text-align:center">`, `<b>`, `<h2>`, `<blockquote>`, `<a href>`, `<span style="font-size:15px">`, `<span style="background-color:#fff593">` (highlight, one per section).
- Paste only at the end of the document. If the cursor is in bold, the whole paste turns bold; the helpers turn bold off first.
- Tags use a hyphen-free list of 10 or more (added in the publish dialog by `naver-blog-scheduling`).

## Verify before moving on
- Title is correct, image count matches the plan, `markAllAI()` returns all `1`, links work (`links` count), no leftover empty paragraphs at odd places. Take a screenshot and look at it.
- The editor autosaves nothing you did not save, but leaving the page may ask about unsaved changes; use "cancel" or navigate away on purpose.

## Known traps
- Editor class names change; if a helper fails, inspect the element and update the selector.
- Replacing an image resets its AI mark; run `markAllAI()` again.
- Do not open a **scheduled** post by its edit URL; the publish dialog then shows "now" and confirming publishes it immediately. Open it from the "scheduled posts" list in the editor instead.
- A long REPL call (over about 2 minutes) is cut off by Aside. The page keeps working, so check state before repeating anything.

## Output
A filled, verified editor tab (not published) and a short report: title, image count, AI mark result, anything odd. Then hand over to `naver-blog-scheduling`.

---
만든이: sphereai.work (https://sphereai.work)
