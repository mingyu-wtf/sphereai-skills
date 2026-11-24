// Naver SmartEditor ONE helpers for the Aside REPL (Playwright-style page object).
// Load: set globalThis.BLOG_ID = "<your blog id>", globalThis.P = <the editor page>, then eval this file.
// Naver changes its editor class names; selectors below use stable prefixes. If one stops matching,
// inspect the page and fix the selector, do not guess.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
globalThis.sleep = sleep;

// Open a blank editor. Dismisses the "a draft in progress" popup by pressing Cancel.
globalThis.openEditor = async () => {
  try { await P.goto(`https://blog.naver.com/PostWriteForm.naver?blogId=${BLOG_ID}`); } catch (e) {}
  for (let k = 0; k < 12; k++) {
    await sleep(1000);
    const popup = await P.evaluate(() => {
      const pop = [...document.querySelectorAll('*')].find(e => e.children.length < 3 && /작성 중인 글이 있습니다/.test(e.innerText || '') && e.getBoundingClientRect().height > 0);
      if (!pop) return false;
      const btn = [...document.querySelectorAll('button')].find(b => b.innerText.trim() === '취소' && b.getBoundingClientRect().height > 0);
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (popup) { await sleep(1500); break; }
    if (k >= 5 && await P.evaluate(() => !!document.querySelector('.se-title-text'))) break;
  }
  // some accounts show a help panel on first use; close it if present
  await P.evaluate(() => { const c = document.querySelector('.se-help-panel-close-button'); c && c.click(); });
  return await P.evaluate(() => ({ title: !!document.querySelector('.se-title-text'), components: document.querySelectorAll('.se-component').length }));
};

globalThis.setTitle = async (text) => {
  await P.locator('.se-title-text .se-text-paragraph').first().click();
  await P.keyboard.press('Control+A');
  await P.keyboard.press('Delete');
  await P.keyboard.type(text, { delay: 3 });
  await P.locator('.se-component.se-text .se-text-paragraph').last().click();
  return await P.evaluate(() => document.querySelector('.se-title-text')?.innerText);
};

// Paste an HTML fragment into the body. The editor converts <p style="text-align:center">, <b>, <h2>,
// <blockquote>, <a href>, <span style="background-color:#fff593"> and font-size spans into its own components.
globalThis.pasteHtml = async (html) => P.evaluate((h) => {
  const f = document.activeElement;
  const d = f.tagName === 'IFRAME' ? f.contentDocument : document;
  const t = d.activeElement || d.body;
  const dt = new DataTransfer();
  dt.setData('text/html', h);
  dt.setData('text/plain', h.replace(/<[^>]+>/g, ''));
  return !t.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true, cancelable: true }));
}, html);

globalThis.clickLastText = async () => {
  await P.locator('.se-component.se-text .se-text-paragraph').last().click();
  await P.keyboard.press('End');
};
globalThis.boldOn = () => P.evaluate(() => document.querySelector('.se-bold-toolbar-button')?.className.includes('se-is-selected') ?? null);

// Add text at the end. Turns bold off first, because a bold cursor makes the whole paste bold.
globalThis.addHtml = async (html) => {
  await clickLastText();
  if (await boldOn()) await P.keyboard.press('Control+B');
  await pasteHtml(html);
  await sleep(600);
};

globalThis.imgCount = () => P.evaluate(() => document.querySelectorAll('.se-component.se-image').length);

globalThis.setCaption = async (cap) => {
  await P.locator('.se-component.se-image .se-module-image').last().click();
  await sleep(600);
  const h = await P.evaluate(() => { const cs = document.querySelectorAll('.se-component.se-image .se-caption'); return cs[cs.length - 1].getBoundingClientRect().height; });
  if (h < 5) return 'caption hidden';
  await P.locator('.se-component.se-image .se-caption .se-text-paragraph').last().click();
  await P.keyboard.type(cap, { delay: 2 });
  return 'ok';
};

// path is relative to the Aside session's "uploads" folder (e.g. "uploads/card.png").
globalThis.addImage = async (path, caption) => {
  await clickLastText();
  if (await boldOn()) await P.keyboard.press('Control+B');
  const before = await imgCount();
  await P.evaluate(() => [...document.querySelectorAll('button')].find(x => x.className.includes('se-image-toolbar-button')).click());
  await sleep(700);
  const idx = await P.evaluate(() => {
    const ins = [...document.querySelectorAll('input[type=file]')];
    const i = ins.findIndex(x => (x.accept || '').includes('image'));
    return i >= 0 ? i : ins.length - 1;
  });
  await P.locator('input[type=file]').nth(idx).setInputFiles(path);
  for (let k = 0; k < 40; k++) { await sleep(1000); if ((await imgCount()) > before) break; }
  if ((await imgCount()) <= before) return 'timeout';
  await sleep(500);
  return caption ? 'ok/' + (await setCaption(caption)) : 'ok';
};

// Switch the "AI generated" mark ON for every image. Required for AI-made images.
// (A replaced image resets this toggle, so run it again after replacing.)
globalThis.markAllAI = async () => {
  await P.evaluate(() => { [...document.querySelectorAll('.se-set-ai-mark-button-toggle')].forEach(t => { if (!t.classList.contains('se-is-selected')) t.click(); }); });
  await sleep(800);
  return await P.evaluate(() => ({
    ai: [...document.querySelectorAll('.se-set-ai-mark-button-toggle')].map(t => t.classList.contains('se-is-selected') ? 1 : 0).join(''),
    images: document.querySelectorAll('.se-component.se-image').length,
    links: document.querySelectorAll('.se-link').length,
    title: document.querySelector('.se-title-text')?.innerText,
  }));
};

// Run the check before publishing: every character of "ai" must be 1.
globalThis.checkPost = markAllAI;
