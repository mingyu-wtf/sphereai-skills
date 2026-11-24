// Read-only Naver blog statistics helpers for the Aside REPL.
// Run them in a tab that is on https://blog.stat.naver.com/ (same origin, logged in to the blog owner's Naver account).
// Observed behavior of the statistics API (may change):
//   GET /api/blog/daily/cv?timeDimension=DATE&startDate=YYYY-MM-DD
//   -> cv: the 15 days ending at startDate; rankCv: top 6 posts of that day; refererTotal: traffic sources of that day;
//      refererDetail: about 20 search queries of that day. Today's numbers are still being counted.
// A 401 means the login expired: ask the user to log in again. Nothing here writes or changes anything.

globalThis.dayStats = async (date) => P.evaluate(async (d) => {
  const r = await fetch('https://blog.stat.naver.com/api/blog/daily/cv?timeDimension=DATE&startDate=' + d, { credentials: 'include' });
  if (r.status !== 200) return { error: r.status };
  const j = await r.json();
  const get = (id) => j.result.statDataList.find(s => s.dataId === id)?.data?.rows || {};
  const zip = (rows) => { const ks = Object.keys(rows); const n = (rows[ks[0]] || []).length; return Array.from({ length: n }, (_, i) => Object.fromEntries(ks.map(k => [k, rows[k][i]]))); };
  return { cv15: zip(get('cv')), topPosts: zip(get('rankCv')), sources: zip(get('refererTotal')), queries: zip(get('refererDetail')) };
}, date);

// Add up the search queries over several days (end date included). Returns the top N queries and total visits.
globalThis.queryTotals = async (endDate, days = 7, topN = 15) => {
  const totals = {}; let visits = 0;
  const end = new Date(endDate + 'T00:00:00Z');
  for (let i = 0; i < days; i++) {
    const d = new Date(end - i * 86400000).toISOString().slice(0, 10);
    const s = await dayStats(d);
    if (s.error) return { error: s.error, at: d };
    for (const q of s.queries) { totals[q.searchQuery] = (totals[q.searchQuery] || 0) + Number(q.cv); visits += Number(q.cv); }
    await new Promise(r => setTimeout(r, 400));
  }
  const top = Object.entries(totals).sort((a, b) => b[1] - a[1]).slice(0, topN).map(([query, cv]) => ({ query, cv }));
  return { days, visitsFromQueries: visits, distinctQueries: Object.keys(totals).length, top };
};
