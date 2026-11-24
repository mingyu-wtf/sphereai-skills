// Scheduling helpers for the Naver SmartEditor publish dialog (Aside REPL, same P and BLOG_ID as editor_helpers.js).
// Load editor_helpers.js first. The helpers NEVER confirm by themselves: confirmPublish() is a separate call
// that you run only after the user approved the exact date, hour and category.
// Class names use stable prefixes ("publish_btn", "confirm_btn", ...). If one stops matching, inspect and fix.

globalThis.openPublishDialog = async () => {
  await P.evaluate(() => document.querySelector('button[class*="publish_btn"]').click());
  await sleep(1500);
  return await P.evaluate(() => !!document.querySelector('button[class*="confirm_btn"]'));
};

globalThis.closePublishDialog = async () => {
  // closes the dialog without publishing: press Escape, then click the page background if it is still open
  await P.keyboard.press('Escape');
  await sleep(600);
  return await P.evaluate(() => !document.querySelector('button[class*="confirm_btn"]') || document.querySelector('button[class*="confirm_btn"]').getBoundingClientRect().height === 0);
};

globalThis.setCategory = async (name) => {
  await P.evaluate(() => document.querySelector('button[class*="selectbox_button"]').click());
  await sleep(700);
  await P.evaluate((c) => {
    const o = [...document.querySelectorAll('li, button, span, label')].filter(e => (e.innerText || '').trim() === c && e.getBoundingClientRect().width > 0);
    const t = o[o.length - 1];
    t && (t.closest('button,label,li') || t).click();
  }, name);
  await sleep(700);
  return await P.evaluate(() => document.querySelector('button[class*="selectbox_button"]')?.innerText.trim());
};

// Tags: 10 or more, no hyphens (a hyphen in a tag blocks tag input).
globalThis.addTags = async (tags) => {
  await P.locator('#tag-input').click();
  for (const t of tags) { await P.keyboard.type(t.replace(/-/g, ''), { delay: 5 }); await P.keyboard.press('Enter'); await sleep(150); }
  return await P.evaluate(() => document.querySelectorAll('[class*="tag_textarea"] [class*="tag__"]').length);
};

globalThis.pickDate = async (month, day) => {
  const open = await P.evaluate(() => [...document.querySelectorAll('button.ui-state-default')].some(b => b.getBoundingClientRect().height > 0));
  if (!open) { await P.evaluate(() => document.querySelector('input[class*="input_date"]').click()); await sleep(800); }
  for (let k = 0; k < 12; k++) { // click "next month" until the calendar shows the wanted month
    const m = await P.evaluate(() => (document.querySelector('.ui-datepicker-title, .ui-datepicker-month') || {}).innerText || '');
    const mm = parseInt((m.match(/(\d+)\s*월/) || m.match(/\.\s*(\d+)/) || [])[1] || '0');
    if (mm === month || mm === 0) break;
    await P.evaluate(() => { const n = document.querySelector('.ui-datepicker-next'); n && n.click(); });
    await sleep(500);
  }
  const res = await P.evaluate((d) => {
    const b = [...document.querySelectorAll('button.ui-state-default')].find(x => x.innerText.trim() === String(d) && x.getBoundingClientRect().height > 0);
    if (!b) return 'no day button';
    b.click(); return 'ok';
  }, day);
  await sleep(500);
  return res;
};

// Set (not confirm) a reservation. hh is "00".."23", minutes are "00" or "10"... in 10-minute steps.
// Returns the values the dialog really shows so you can compare them with what the user asked for.
globalThis.setSchedule = async (year, month, day, hh, mm = '00') => {
  await P.evaluate(() => { const r = document.querySelector('input[value="pre"]'); (r.labels?.[0] || r).click(); });
  await sleep(800);
  const pk = await pickDate(month, day);
  await P.locator('select[class*="hour_option"]').selectOption(hh);
  await P.locator('select[class*="minute_option"]').selectOption(mm);
  await sleep(400);
  const v = await P.evaluate(() => ({
    date: document.querySelector('input[class*="input_date"]')?.value,
    hour: document.querySelector('select[class*="hour_option"]')?.value,
    minute: document.querySelector('select[class*="minute_option"]')?.value,
    reserved: document.querySelector('input[value="pre"]').checked,
    category: document.querySelector('button[class*="selectbox_button"]')?.innerText.trim(),
    tags: document.querySelectorAll('[class*="tag_textarea"] [class*="tag__"]').length,
  }));
  const want = `${year}. ${String(month).padStart(2, '0')}. ${String(day).padStart(2, '0')}`;
  v.ok = v.date === want && v.hour === hh && v.minute === mm && v.reserved && v.tags >= 10 && pk === 'ok';
  return v;
};

// Run ONLY after the user approved. It publishes or schedules the post for real.
globalThis.confirmPublish = async () => {
  await P.evaluate(() => document.querySelector('button[class*="confirm_btn"]').click());
  await sleep(5000);
  return P.url();
};

// How many posts are scheduled now (shown on the editor's top bar as "예약 발행 N건").
globalThis.reservedCount = () => P.evaluate(() => (document.body.innerText.match(/예약\s*발행\s*(\d+)\s*건/) || [])[1] || null);
