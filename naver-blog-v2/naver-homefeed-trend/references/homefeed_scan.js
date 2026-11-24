// Naver mobile home feed reader (read only). Paste into an Aside REPL that is attached to a
// SEPARATE, view-only browser profile (not the profile you write posts with).
// It only clicks feed tabs and scrolls. It never likes, comments, follows or writes.
//
// Usage in the REPL:
//   eval(<this file's text>);
//   const cards = await hfScan({ pans: ['지식', '추천'], scrolls: 7 });
//   console.log(JSON.stringify(hfPick(cards, ['우주', '행성', '별']), null, 1));

globalThis.sleep = globalThis.sleep || ((ms) => new Promise((r) => setTimeout(r, ms)));

// Read the cards of one or more feed tabs ("pans"). Returns [{pan, rank, title, author, url, kind}].
globalThis.hfScan = async ({ pans = ['추천'], scrolls = 7, keepTab = false } = {}) => {
  const pg = await openTab('https://m.naver.com/');
  await pg.setViewportSize({ width: 420, height: 900 });
  await sleep(3000);
  const out = [];
  for (const pan of pans) {
    // Every feed tab is loaded side by side in one page, so read only the boxes of the chosen tab:
    // the tab link's href (#LECTURE, #SEARCH ...) names its feed boxes (id="feeditem-LECTURE-0" ...).
    const code = await pg.evaluate((name) => {
      const el = [...document.querySelectorAll('[role=tab]')]
        .find((e) => e.innerText && e.innerText.trim() === name && e.getBoundingClientRect().height > 0);
      if (!el) return null;
      el.click();
      return (el.getAttribute('href') || '').replace('#', '');
    }, pan);
    if (!code) { out.push({ pan, error: 'tab not found' }); continue; }
    await sleep(3000);
    await pg.evaluate(() => window.scrollTo(0, 0));
    for (let i = 0; i < scrolls; i++) { await pg.mouse.wheel(0, 2500); await sleep(1200); }
    const cards = await pg.evaluate((code) => {
      const seen = new Set();
      const res = [];
      let boxes = [...document.querySelectorAll(`[id^="feeditem-${code}-"]`)];
      // The 추천 tab uses other card classes and no feeditem boxes: keep links that sit on screen horizontally.
      const SEL = 'a[class*="thumb_link"], a[class*="title_link"], a[class*="chf_link_info"], a[class*="cc_link_clip"]';
      const onScreen = (a) => { const r = a.getBoundingClientRect(); return r.width > 0 && r.left > -5 && r.left < window.innerWidth; };
      const links = boxes.length
        ? boxes.flatMap((b) => [...b.querySelectorAll(SEL)])
        : [...document.querySelectorAll(SEL)].filter(onScreen);
      for (const a of links) {
        const title = a.innerText.replace(/\d페이지/g, '').replace(/\s+/g, ' ').trim();
        if (title.length < 8 || seen.has(a.href)) continue;
        seen.add(a.href);
        let box = a.parentElement, author = '';
        // 추천-style cards: the author sits in a sibling profile link ("name / badge / time").
        for (let i = 0; i < 5 && box && !author; i++, box = box.parentElement) {
          const prof = box.querySelector('a[class*="chf_link_profile"]');
          if (prof) author = prof.innerText.split('\n')[0].trim();
        }
        box = a.parentElement;
        // Other tabs: the author name is usually the first line after "더보기" in the same card box.
        for (let i = 0; i < 4 && box && !author; i++, box = box.parentElement) {
          const lines = box.innerText.split('\n').map((s) => s.trim()).filter(Boolean);
          const at = lines.findIndex((l) => title.startsWith(l.slice(0, 15)));
          if (at >= 0 && lines[at + 1] === '더보기' && lines[at + 2]) { author = lines[at + 2]; break; }
        }
        const kind = /shorts|clip/.test(a.href) ? 'clip' : /blog\.naver/.test(a.href) ? 'blog'
          : /in\.naver/.test(a.href) ? 'influencer' : /news/.test(a.href) ? 'news' : /cafe/.test(a.href) ? 'cafe' : 'other';
        res.push({ title: title.slice(0, 120), author, url: a.href, kind });
      }
      return res;
    }, code);
    cards.forEach((c, i) => out.push({ pan, rank: i + 1, ...c }));
  }
  if (!keepTab) await closeTab(pg);
  return out;
};

// Keep only cards whose title matches your subject words. Earlier rank = shown higher in the feed.
globalThis.hfPick = (cards, words) => {
  const re = new RegExp(words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'));
  return cards.filter((c) => c.title && re.test(c.title));
};

// Open one card and read its visible reaction numbers (likes / comments), if the page shows them.
globalThis.hfReactions = async (url) => {
  const pg = await openTab(url);
  await sleep(4000);
  const r = await pg.evaluate(() => {
    const t = document.body.innerText;
    const like = (t.match(/공감\s*([\d,]+)/) || t.match(/좋아요\s*([\d,]+)/) || [])[1] || null;
    const comment = (t.match(/댓글\s*([\d,]+)/) || [])[1] || null;
    const lines = t.split('\n').map((s) => s.trim()).filter((s) => s.length > 15).slice(0, 6);
    const heads = [...document.querySelectorAll('h2, h3, .se-section-sectionTitle')].map((h) => h.innerText.trim()).filter(Boolean).slice(0, 8);
    return { like, comment, firstLines: lines, subheads: heads };
  });
  await closeTab(pg);
  return r;
};
