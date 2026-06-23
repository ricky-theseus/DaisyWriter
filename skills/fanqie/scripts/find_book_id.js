const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const context = browser.contexts()[0];
  if (!context) { console.log('No existing context'); await browser.close(); return; }
  const page = context.pages()[0] || await context.newPage();
  console.log('URL:', page.url());
  await page.goto('https://fanqienovel.com/main/writer/book-manage', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  console.log('After nav:', page.url());
  const links = await page.evaluate(() => {
    const all = document.querySelectorAll('a[href*="/main/writer/"]');
    return Array.from(all).map(a => a.href).filter(h => h.includes('chapter-manage') || h.includes('/publish'));
  });
  console.log('Book links:', JSON.stringify(links, null, 2));
  const books = await page.evaluate(() => {
    const items = document.querySelectorAll('.book-item, [class*="book"], [class*="Book"], tr, .arco-table-tr');
    return Array.from(items).slice(0, 5).map(el => el.innerText?.substring(0, 200) || '').filter(Boolean);
  });
  console.log('Book items:', JSON.stringify(books, null, 2));
  await browser.close();
})();
