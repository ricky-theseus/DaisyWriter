#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { LOGIN_URL, ensureLoggedIn } = require('./fanqie_login_flow');
const { resolvePage, isFanqieWriterPage } = require('./browser_page_picker');

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    const next = argv[i + 1];
    if (key.startsWith('--')) {
      if (!next || next.startsWith('--')) args[key.slice(2)] = true;
      else {
        args[key.slice(2)] = next;
        i += 1;
      }
    }
  }
  return args;
}

async function main() {
  let playwright;
  try {
    playwright = require('playwright');
  } catch (err) {
    console.error('Missing dependency: playwright');
    console.error('Install with: npm i -D playwright  OR  npm i -g playwright');
    process.exit(1);
  }

  const args = parseArgs(process.argv);
  let cdpUrl = args.cdp || 'http://127.0.0.1:9222';
  const loginUrl = LOGIN_URL;
  const statePath = path.resolve(__dirname, '..', 'state', 'fanqie-storage-state.json');
  const qrPath = path.resolve(__dirname, '..', 'state', 'login-qr.png');
  fs.mkdirSync(path.dirname(statePath), { recursive: true });

  if (cdpUrl.startsWith('http://') || cdpUrl.startsWith('https://')) {
    const jsonUrl = cdpUrl.replace(/\/$/, '') + '/json/version';
    const res = await fetch(jsonUrl);
    if (!res.ok) throw new Error(`Failed to query DevTools endpoint: ${jsonUrl} => ${res.status}`);
    const meta = await res.json();
    cdpUrl = meta.webSocketDebuggerUrl || cdpUrl;
  }

  const { chromium } = playwright;
  console.log('DEBUG: before connectOverCDP');
  const browser = await chromium.connectOverCDP(cdpUrl);
  console.log('DEBUG: after connectOverCDP');
  console.log('DEBUG: before context setup');
  const context = args['fresh-context'] ? await browser.newContext() : (browser.contexts()[0] || await browser.newContext());
  console.log(`DEBUG: after context setup fresh=${!!args['fresh-context']}`);
  console.log('DEBUG: before resolvePage');
  const { page, reusedExistingPage } = await resolvePage(context, {
    preferredUrlPatterns: [
      LOGIN_URL,
      /https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\//i,
      /https?:\/\/(?:www\.)?fanqienovel\.com\//i,
    ],
  });
  console.log(`DEBUG: after resolvePage reused=${reusedExistingPage} url=${page.url() || 'about:blank'}`);
  if (!isFanqieWriterPage(page.url())) {
    console.log('DEBUG: before goto');
    await page.goto(loginUrl, { waitUntil: 'domcontentloaded' });
    console.log('DEBUG: after goto');
  }
  console.log('DEBUG: before wait login shell');
  await page.waitForSelector('#slogin-pc-login-form, .writer-login__content__form, .slogin-pc-form-header__title__tab', { timeout: 15000 }).catch(() => {});
  console.log('DEBUG: after wait login shell');
  console.log(`已连接 Windows 浏览器: ${cdpUrl}`);

  const loginResult = await ensureLoggedIn(page, {
    loginUrl,
    qrPath,
    logger: console,
    onQrReady: async (qrCapture) => {
      const qrAbs = path.resolve(qrCapture.path);
      console.log(`QR_READY:${qrAbs}`);
      console.log('---OPENCLAW_MEDIA_REPLY_START---');
      console.log('请扫码登录番茄作者后台。');
      console.log('');
      console.log(`MEDIA:${qrAbs}`);
      console.log('---OPENCLAW_MEDIA_REPLY_END---');
    },
    saveStorageState: async () => {
      await context.storageState({ path: statePath });
      console.log(`已保存登录态: ${statePath}`);
    },
  });

  if (!loginResult.loggedIn) {
    console.error('等待扫码登录超时。');
    console.error('LOGIN_TIMEOUT');
    if (loginResult.qrCapture?.path) {
      console.error(`最近一次二维码截图: ${loginResult.qrCapture.path}`);
    }
    if (!reusedExistingPage) {
      await page.close().catch(() => {});
    }
    await browser.close().catch(() => {});
    process.exit(2);
  }

  if (loginResult.alreadyLoggedIn) {
    await context.storageState({ path: statePath });
    console.log(`检测到当前会话已登录，已刷新保存登录态: ${statePath}`);
    console.log('LOGIN_ALREADY_OK');
  } else {
    console.log('LOGIN_OK');
  }

  if (!reusedExistingPage) {
    await page.close().catch(() => {});
  }
  await browser.close().catch(() => {});
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
