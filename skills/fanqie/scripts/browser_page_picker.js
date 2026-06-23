#!/usr/bin/env node

const FANQIE_WRITER_URL_RE = /^https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\//i;
const FANQIE_URL_RE = /^https?:\/\/(?:www\.)?fanqienovel\.com\//i;
const BROWSER_INTERNAL_URL_RE = /^(about:blank|chrome:|devtools:|edge:)/i;

function toMatcher(pattern) {
  if (pattern instanceof RegExp) return (url) => pattern.test(url);
  if (typeof pattern === 'string' && pattern) return (url) => url.includes(pattern);
  return () => false;
}

function scorePage(page, matchers, index) {
  const url = page.url() || '';
  if (!url || BROWSER_INTERNAL_URL_RE.test(url)) {
    return { page, url, index, score: -1000 + index };
  }

  let score = index;
  if (matchers.some((matches) => matches(url))) score += 500;
  if (/\/main\/writer\/chapter-manage\//i.test(url)) score += 350;
  else if (/\/main\/writer\/\d+\/publish\//i.test(url)) score += 320;
  else if (/\/main\/writer\/book-manage/i.test(url)) score += 160;
  else if (/\/main\/writer\/data\?/i.test(url)) score -= 250;

  if (FANQIE_WRITER_URL_RE.test(url)) score += 200;
  else if (FANQIE_URL_RE.test(url)) score += 100;
  else if (/^https?:\/\//i.test(url)) score += 10;

  return { page, url, index, score };
}

async function resolvePage(context, options = {}) {
  const {
    preferredUrlPatterns = [],
    createIfMissing = true,
    collapseFanqieWriterTabs = false,
  } = options;

  const matchers = preferredUrlPatterns.map(toMatcher);
  const pages = context.pages();
  const ranked = pages
    .map((page, index) => scorePage(page, matchers, index))
    .sort((a, b) => b.score - a.score || b.index - a.index);

  const best = ranked[0];
  if (best && best.score > -100) {
    if (collapseFanqieWriterTabs) {
      for (const item of ranked) {
        if (item.page === best.page) continue;
        if (!isFanqieWriterPage(item.url)) continue;
        await item.page.close({ runBeforeUnload: true }).catch(() => {});
      }
    }
    await best.page.bringToFront().catch(() => {});
    return {
      page: best.page,
      reusedExistingPage: true,
      pageUrl: best.url,
    };
  }

  if (!createIfMissing) return { page: null, reusedExistingPage: false, pageUrl: '' };

  const page = await context.newPage();
  if (collapseFanqieWriterTabs) {
    for (const other of context.pages()) {
      if (other === page) continue;
      const url = other.url() || '';
      if (!isFanqieWriterPage(url)) continue;
      await other.close({ runBeforeUnload: true }).catch(() => {});
    }
  }
  await page.bringToFront().catch(() => {});
  return {
    page,
    reusedExistingPage: false,
    pageUrl: page.url() || '',
  };
}

function isFanqieWriterPage(url) {
  return FANQIE_WRITER_URL_RE.test(url || '');
}

module.exports = {
  resolvePage,
  isFanqieWriterPage,
};
