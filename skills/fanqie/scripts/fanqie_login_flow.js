#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const LOGIN_URL = 'https://fanqienovel.com/main/writer/?enter_from=author_zone';

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

async function safeText(locator) {
  try {
    return ((await locator.innerText()) || '').replace(/\s+/g, ' ').trim();
  } catch {
    return '';
  }
}

async function isLoggedIn(page) {
  const url = page.url();
  const bodyText = await safeText(page.locator('body').first());

  if (/扫码登录|二维码登录|登录后继续|手机号登录|微信登录|抖音登录/.test(bodyText)) {
    return false;
  }

  const loginHints = page.locator('text=/扫码登录|二维码登录|手机号登录|微信登录|抖音登录|登录后继续/');
  if (await loginHints.count()) return false;

  if ((/\/publish\//.test(url) || /chapter-manage/.test(url) || (/\/main\/writer\//.test(url) && !/login|passport|auth/i.test(url)))) {
    const cssHints = page.locator('.publish-button.auto-editor-next, .ProseMirror[contenteditable="true"], input[placeholder="请输入标题"], a[href*="/main/writer/chapter-manage/"]');
    if (await cssHints.count()) return true;

    const textHints = [
      page.getByText('章节管理', { exact: false }).first(),
      page.getByText('草稿箱', { exact: false }).first(),
      page.getByText('设置编辑分卷', { exact: false }).first(),
      page.getByText('新建章节', { exact: false }).first(),
    ];
    for (const hint of textHints) {
      if (await hint.count().catch(() => 0)) return true;
    }

    if (/章节管理/.test(bodyText) && /新建章节|设置编辑分卷|草稿箱/.test(bodyText)) {
      return true;
    }
  }

  return false;
}

async function switchToQrLogin(page, logger = null) {
  logger?.log?.('DEBUG: enter switchToQrLogin');
  const candidates = [
    page.locator('#slogin-pc-login-form .slogin-pc-form-header__title__tab').filter({ hasText: '扫码登录' }).first(),
    page.locator('.writer-login__content__form .slogin-pc-form-header__title__tab').filter({ hasText: '扫码登录' }).first(),
    page.locator('.slogin-pc-form-header__title__tab').filter({ hasText: '扫码登录' }).first(),
    page.getByText('扫码登录', { exact: true }).first(),
    page.getByText('扫码登录', { exact: false }).first(),
    page.getByText('二维码登录', { exact: false }).first(),
  ];

  for (let ci = 0; ci < candidates.length; ci++) {
    const candidate = candidates[ci];
    try {
      const count = await candidate.count();
      logger?.log?.(`DEBUG: switchToQrLogin candidate=${ci} count=${count}`);
      if (count) {
        for (let i = 0; i < 4; i++) {
          logger?.log?.(`DEBUG: switchToQrLogin candidate=${ci} clickAttempt=${i}`);
          await candidate.click({ timeout: 1500, force: true, noWaitAfter: true }).catch(() => {});
          const qrView = await isQrLoginView(page).catch(() => false);
          logger?.log?.(`DEBUG: switchToQrLogin candidate=${ci} clickAttempt=${i} qrView=${qrView}`);
          if (qrView) {
            logger?.log?.('DEBUG: leave switchToQrLogin success=true');
            return true;
          }
        }
      }
    } catch (err) {
      logger?.log?.(`DEBUG: switchToQrLogin candidate=${ci} error=${err?.message || err}`);
    }
  }
  const result = await isQrLoginView(page).catch(() => false);
  logger?.log?.(`DEBUG: leave switchToQrLogin success=${result}`);
  return result;
}

async function findLoginRoot(page) {
  const directCandidates = [
    '.writer-login__content__form',
    '#slogin-pc-login-form',
    '.slogin-pc-login-form',
    '.login',
    '.login-container',
    '.login-panel',
    '.login-box',
    '.passport-login-container',
    '.passport-login-panel',
    '[class*="login"]',
    '[class*="passport"]',
    '[data-testid*="login"]',
  ];

  for (const selector of directCandidates) {
    try {
      const locator = page.locator(selector).filter({ hasText: /扫码登录|二维码登录|手机号登录|登录后继续/ }).first();
      if (await locator.count()) {
        const box = await locator.boundingBox().catch(() => null);
        if (box && box.width >= 180 && box.height >= 180) return locator;
      }
    } catch {}
  }

  const textAnchors = [
    page.getByText('扫码登录', { exact: false }).first(),
    page.getByText('二维码登录', { exact: false }).first(),
    page.getByText('登录后继续', { exact: false }).first(),
  ];

  for (const anchor of textAnchors) {
    try {
      if (!(await anchor.count())) continue;
      const containers = [
        anchor.locator('xpath=ancestor::*[self::div or self::section or self::main][1]').first(),
        anchor.locator('xpath=ancestor::*[self::div or self::section or self::main][2]').first(),
        anchor.locator('xpath=ancestor::*[self::div or self::section or self::main][3]').first(),
      ];
      for (const container of containers) {
        if (!(await container.count())) continue;
        const box = await container.boundingBox().catch(() => null);
        if (box && box.width >= 180 && box.height >= 180) return container;
      }
    } catch {}
  }

  return null;
}

async function findQrLocator(page, loginRootHint = null) {
  const strongCandidates = [
    '.slogin-qrcode-scan-page__content__code__img',
    '.slogin-qrcode-scan-page__content__code',
    '.slogin-qrcode-scan-page__content',
    '.slogin-qrcode-scan-page',
  ];
  for (const selector of strongCandidates) {
    const locator = page.locator(selector).first();
    try {
      if (await locator.count()) {
        const box = await locator.boundingBox().catch(() => null);
        if (box && box.width >= 100 && box.height >= 100) return locator;
      }
    } catch {}
  }

  const loginRoot = loginRootHint ?? await findLoginRoot(page);
  const scoped = loginRoot || page.locator('body').first();
  const candidates = [
    '.slogin-pc-qrcode, .slogin-qrcode, .qrcode, .qr-code, .rcode',
    '.slogin-pc-qrcode img, .slogin-qrcode img, .qrcode img, .qr-code img, .rcode img',
    '.slogin-pc-qrcode canvas, .slogin-qrcode canvas, .qrcode canvas, .qr-code canvas, .rcode canvas',
    'img[alt*="二维码"]',
    'img[src*="qrcode"]',
    'img[src*="qr"]',
    '.semi-qrcode',
    '.arco-qrcode',
    'canvas',
    'img',
    'svg',
  ];

  const scored = [];
  for (const selector of candidates) {
    const locators = scoped.locator(selector);
    const count = Math.min(await locators.count().catch(() => 0), 12);
    for (let i = 0; i < count; i++) {
      const locator = locators.nth(i);
      try {
        const box = await locator.boundingBox().catch(() => null);
        if (!box) continue;
        if (box.width < 80 || box.height < 80) continue;
        if (box.width > 520 || box.height > 520) continue;
        const ratio = box.width / box.height;
        const squarePenalty = Math.abs(1 - ratio);
        if (squarePenalty > 0.35) continue;

        let score = 0;
        if (/qrcode|qr-code|rcode|semi-qrcode|arco-qrcode/i.test(selector)) score += 6;
        if (selector === 'canvas') score += 3;
        if (selector === 'img[src*="qrcode"]' || selector === 'img[src*="qr"]') score += 4;
        if (box.width >= 120 && box.width <= 360) score += 3;
        if (box.height >= 120 && box.height <= 360) score += 3;
        score -= squarePenalty * 10;
        score -= Math.abs(box.width - box.height) / 50;

        scored.push({ locator, score, box });
      } catch {}
    }
  }

  scored.sort((a, b) => b.score - a.score);
  if (scored.length > 0) return scored[0].locator;

  if (loginRoot) return loginRoot;
  return null;
}

async function getQrViewState(page, logger = null) {
  logger?.log?.('DEBUG: enter getQrViewState');
  const loginRoot = await findLoginRoot(page);
  const loginText = loginRoot ? await safeText(loginRoot) : '';

  const qrPanel = page.locator('.slogin-qrcode-scan-page').first();
  const qrImage = page.locator('.slogin-qrcode-scan-page__content__code__img').first();
  const qrCode = page.locator('.slogin-qrcode-scan-page__content__code').first();
  const qrExpiredOverlay = page.locator('.slogin-qrcode-scan-page__content__code__cover').first();
  const codeInput = page.locator('input[placeholder*="验证码"], input[placeholder*="手机号"], button:has-text("获取验证码")').first();

  const [qrPanelBox, qrImageBox, qrCodeBox, qrExpiredOverlayBox, codeInputBox] = await Promise.all([
    qrPanel.boundingBox().catch(() => null),
    qrImage.boundingBox().catch(() => null),
    qrCode.boundingBox().catch(() => null),
    qrExpiredOverlay.boundingBox().catch(() => null),
    codeInput.boundingBox().catch(() => null),
  ]);

  const hasQrPanel = !!(qrPanelBox && qrPanelBox.width >= 120 && qrPanelBox.height >= 120);
  const hasQrImage = !!(qrImageBox && qrImageBox.width >= 100 && qrImageBox.height >= 100);
  const hasQrCodeBox = !!(qrCodeBox && qrCodeBox.width >= 100 && qrCodeBox.height >= 100);
  const hasExpiredOverlay = !!(qrExpiredOverlayBox && qrExpiredOverlayBox.width >= 100 && qrExpiredOverlayBox.height >= 100);
  const hasStrongQrHint = /打开番茄小说或|番茄作家助手扫码登录|打开番茄小说/.test(loginText);
  const hasVisibleCodeInput = !!(codeInputBox && codeInputBox.width >= 40 && codeInputBox.height >= 20);
  // 真实过期态会在二维码上叠一层 cover，并显示“二维码已失效 / 点击刷新”。
  // 只有 cover 真正出现，或 QR 面板已经不存在时，才把这些文案当作过期信号。
  const rawExpiredText = /二维码已失效|点击刷新|刷新二维码|请刷新/.test(loginText);
  const hasExpiredText = rawExpiredText && (hasExpiredOverlay || !(hasQrPanel || hasQrImage || hasQrCodeBox));

  const result = {
    inQrView: (hasQrPanel || hasQrImage || hasQrCodeBox) && hasStrongQrHint,
    hasExpiredOverlay,
    hasExpiredText,
    hasVisibleCodeInput,
    hasQrPanel,
    hasQrImage,
    hasQrCodeBox,
    text: loginText,
  };
  logger?.log?.(`DEBUG: leave getQrViewState inQrView=${result.inQrView} hasExpiredOverlay=${result.hasExpiredOverlay} hasVisibleCodeInput=${result.hasVisibleCodeInput}`);
  return result;
}

async function isQrLoginView(page) {
  const state = await getQrViewState(page).catch(() => null);
  if (!state) return false;
  if (state.hasVisibleCodeInput) return false;
  return !!state.inQrView;
}

async function captureQrScreenshot(page, outPath, logger = null) {
  logger?.log?.('DEBUG: enter captureQrScreenshot');
  ensureDir(path.dirname(outPath));
  const loginRoot = await findLoginRoot(page);
  const qr = await findQrLocator(page, loginRoot);
  if (qr) {
    const qrBox = await qr.boundingBox().catch(() => null);
    if (qrBox && qrBox.width <= 440 && qrBox.height <= 440) {
      await qr.screenshot({ path: outPath }).catch(async () => {
        if (loginRoot) {
          await loginRoot.screenshot({ path: outPath }).catch(async () => {
            await page.screenshot({ path: outPath, fullPage: true });
          });
        } else {
          await page.screenshot({ path: outPath, fullPage: true });
        }
      });
      logger?.log?.('DEBUG: leave captureQrScreenshot scope=qr');
      return { ok: true, path: outPath, scope: 'qr' };
    }

    if (loginRoot) {
      await loginRoot.screenshot({ path: outPath }).catch(async () => {
        await page.screenshot({ path: outPath, fullPage: true });
      });
      logger?.log?.('DEBUG: leave captureQrScreenshot scope=login-root');
      return { ok: true, path: outPath, scope: 'login-root' };
    }

    await qr.screenshot({ path: outPath }).catch(async () => {
      await page.screenshot({ path: outPath, fullPage: true });
    });
    logger?.log?.('DEBUG: leave captureQrScreenshot scope=page');
    return { ok: true, path: outPath, scope: 'page' };
  }
  if (loginRoot) {
    await loginRoot.screenshot({ path: outPath }).catch(async () => {
      await page.screenshot({ path: outPath, fullPage: true });
    });
    logger?.log?.('DEBUG: leave captureQrScreenshot scope=login-root');
    return { ok: true, path: outPath, scope: 'login-root' };
  }
  await page.screenshot({ path: outPath, fullPage: true });
  logger?.log?.('DEBUG: leave captureQrScreenshot scope=page');
  return { ok: true, path: outPath, scope: 'page' };
}

async function detectQrExpiredFromDom(page, logger = null) {
  logger?.log?.('DEBUG: enter detectQrExpiredFromDom');
  const qrState = await getQrViewState(page, logger).catch(() => null);
  const loginText = qrState?.text || '';

  if (qrState?.inQrView && (qrState.hasExpiredOverlay || qrState.hasExpiredText)) {
    return {
      expired: true,
      source: qrState.hasExpiredOverlay ? 'dom-cover' : 'dom',
      text: loginText.slice(0, 500),
      qrView: true,
      hasExpiredOverlay: qrState.hasExpiredOverlay,
    };
  }

  // 明确正常 QR 视图（无过期覆盖层、无过期信号）：无需读 bodyText，提前返回
  if (qrState?.inQrView && !qrState.hasExpiredOverlay) {
    const result = { expired: false, source: 'dom', text: loginText.slice(0, 500), qrView: true, hasExpiredOverlay: false };
    logger?.log?.(`DEBUG: leave detectQrExpiredFromDom expired=false source=dom qrView=true hasExpiredOverlay=false`);
    return result;
  }

  // 其他情况（不在 QR 视图 / 状态不明确）才读 bodyText 做兜底
  const bodyText = await safeText(page.locator('body').first());

  // 若当前已在扫码视图且过期覆盖层不可见，则 bodyText 里残留的“点击刷新/二维码已失效”
  // 属于旧 DOM 残留，不视为真实过期信号。
  const cleanQrState = !!(qrState?.inQrView && !qrState?.hasExpiredOverlay);
  if (!cleanQrState && /二维码.*(失效|过期)|已失效|已过期|点击刷新|刷新二维码|二维码刷新|请刷新/.test(bodyText)) {
    return {
      expired: true,
      source: 'dom',
      text: bodyText.slice(0, 500),
    };
  }

  if ((!qrState || !qrState.inQrView) && (/请输入验证码|获取验证码|验证码登录|密码登录/.test(loginText || bodyText))) {
    return {
      expired: false,
      source: 'dom-non-qr-view',
      text: (loginText || bodyText).slice(0, 500),
      nonQrView: true,
    };
  }

  const result = { expired: false, source: 'dom', text: (loginText || bodyText).slice(0, 500), qrView: !!qrState?.inQrView, hasExpiredOverlay: !!qrState?.hasExpiredOverlay };
  logger?.log?.(`DEBUG: leave detectQrExpiredFromDom expired=${result.expired} source=${result.source} qrView=${result.qrView} hasExpiredOverlay=${result.hasExpiredOverlay}`);
  return result;
}

function sha256File(filePath) {
  try {
    const buf = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(buf).digest('hex');
  } catch {
    return null;
  }
}

async function notifyQrReadyIfNeeded({
  qrCapture,
  qrStatus,
  onQrReady,
  first = false,
  refreshed = false,
  lastNotifiedQrHash = null,
}) {
  if (typeof onQrReady !== 'function' || !qrCapture?.path) return lastNotifiedQrHash;
  if (qrStatus?.expired || qrStatus?.nonQrView) return lastNotifiedQrHash;

  const qrHash = sha256File(qrCapture.path);
  const shouldNotify = !lastNotifiedQrHash || (qrHash && qrHash !== lastNotifiedQrHash);
  if (!shouldNotify) return lastNotifiedQrHash;

  await onQrReady(qrCapture, {
    first,
    refreshed,
    qrStatus,
  }).catch(() => {});

  return qrHash || lastNotifiedQrHash;
}

function copyIfExists(src, dest) {
  try {
    if (src && fs.existsSync(src)) {
      ensureDir(path.dirname(dest));
      fs.copyFileSync(src, dest);
      return true;
    }
  } catch {}
  return false;
}

function timestampId() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function runTesseract(imagePath) {
  const bin = spawnSync('bash', ['-lc', 'command -v tesseract >/dev/null 2>&1 && echo yes || echo no'], { encoding: 'utf8' });
  if ((bin.stdout || '').trim() !== 'yes') return { available: false, text: '' };

  const result = spawnSync('tesseract', [imagePath, 'stdout', '-l', 'chi_sim+eng'], {
    encoding: 'utf8',
    timeout: 15000,
  });

  const text = `${result.stdout || ''}\n${result.stderr || ''}`.replace(/\s+/g, ' ').trim();
  return {
    available: true,
    ok: result.status === 0 || !!text,
    text,
  };
}

async function detectQrExpired(page, qrPath, logger = null) {
  logger?.log?.('DEBUG: enter detectQrExpired');
  const dom = await detectQrExpiredFromDom(page, logger);
  if (dom.expired || dom.nonQrView) return dom;

  if (!qrPath || !fs.existsSync(qrPath)) {
    return { expired: false, source: 'ocr-unavailable' };
  }

  logger?.log?.('DEBUG: enter tesseract');
  const ocr = runTesseract(qrPath);
  logger?.log?.(`DEBUG: leave tesseract available=${ocr.available} textLen=${(ocr.text || '').length}`);
  if (!ocr.available) return { expired: false, source: 'ocr-unavailable' };
  if (/二维码.*(失效|过期)|已失效|已过期|点击刷新|刷新二维码|二维码刷新|请刷新/.test(ocr.text)) {
    return {
      expired: true,
      source: 'ocr',
      text: ocr.text.slice(0, 500),
    };
  }

  if (/验证码登录|手机号|请输入验证码|获取验证码|密码登录/.test(ocr.text) && !/扫码登录|二维码/.test(ocr.text)) {
    return {
      expired: false,
      source: 'ocr-non-qr-view',
      text: ocr.text.slice(0, 500),
      nonQrView: true,
    };
  }

  const result = { expired: false, source: 'ocr', text: ocr.text.slice(0, 500) };
  logger?.log?.(`DEBUG: leave detectQrExpired expired=${result.expired} source=${result.source}`);
  return result;
}

// 点击刷新后，番茄二维码区域会经历：
//   [过期覆盖层] → [明文失效态 "二维码已失效"] → [新码就绪态]
// 这个函数在点击刷新后轮询，等待“过期覆盖层 + 失效文案”双双消失，再返回。
// maxWaitMs 默认 6000，pollMs 默认 400。
async function waitForQrTransitionDone(page, { maxWaitMs = 6000, pollMs = 400, logger = null } = {}) {
  const deadline = Date.now() + maxWaitMs;
  let round = 0;
  while (Date.now() < deadline) {
    const state = await getQrViewState(page, null).catch(() => null);
    round += 1;
    logger?.log?.(`DEBUG: waitForQrTransitionDone round=${round} hasExpiredOverlay=${state?.hasExpiredOverlay} hasExpiredText=${state?.hasExpiredText} inQrView=${state?.inQrView}`);
    // 既没有过期覆盖层、也没有失效文案，说明过渡完成（无论是新码还是其他状态）
    if (state && !state.hasExpiredOverlay && !state.hasExpiredText) {
      logger?.log?.(`DEBUG: waitForQrTransitionDone done after ${round} rounds`);
      return { done: true, rounds: round, state };
    }
    await page.waitForTimeout(pollMs);
  }
  // 超时：返回最后一次状态，让调用方自行处理
  const state = await getQrViewState(page, null).catch(() => null);
  logger?.log?.(`DEBUG: waitForQrTransitionDone timeout after ${round} rounds hasExpiredOverlay=${state?.hasExpiredOverlay} hasExpiredText=${state?.hasExpiredText}`);
  return { done: false, rounds: round, state, timedOut: true };
}

async function refreshQrIfExpired(page, qrPath, logger = console) {
  await page.bringToFront().catch(() => {});
  const status = await detectQrExpired(page, qrPath, logger);
  logger.log(`二维码状态检查: expired=${!!status.expired}, source=${status.source || 'unknown'}${status.nonQrView ? ', nonQrView=true' : ''}${status.text ? `, text=${JSON.stringify(status.text.slice(0, 120))}` : ''}`);
  if (status.nonQrView) {
    await switchToQrLogin(page, logger).catch(() => false);
    logger.log('检测到当前不在扫码登录视图，已尝试切回扫码登录。');
    return { refreshed: true, status, verified: await isQrLoginView(page).catch(() => false) };
  }
  if (!status.expired) return { refreshed: false, status, verified: true };

  logger.log(`检测到二维码可能已过期，来源: ${status.source}`);
  const debugDir = path.join(path.dirname(qrPath || path.join(process.cwd(), 'tmp.png')), 'refresh-debug');
  ensureDir(debugDir);
  const stamp = timestampId();
  const beforePath = path.join(debugDir, `${stamp}-before.png`);
  if (qrPath) {
    await captureQrScreenshot(page, qrPath, logger).catch(() => null);
    copyIfExists(qrPath, beforePath);
  }
  const beforeHash = qrPath ? sha256File(qrPath) : null;

  const candidates = [
    // 优先直接点击真实过期覆盖层（番茄当前结构）
    { locator: page.locator('.slogin-qrcode-scan-page__content__code__cover__text').first(), label: '过期覆盖层文案' },
    { locator: page.locator('.slogin-qrcode-scan-page__content__code__cover__text span').filter({ hasText: '点击刷新' }).first(), label: '过期覆盖层点击刷新' },
    { locator: page.locator('.slogin-qrcode-scan-page__content__code__cover').first(), label: '过期覆盖层' },
    { locator: page.getByText('点击刷新', { exact: false }).first(), label: '文案入口' },
    { locator: page.getByText('刷新二维码', { exact: false }).first(), label: '刷新二维码' },
    { locator: page.getByText('请刷新', { exact: false }).first(), label: '请刷新' },
    { locator: page.locator('button, a, div, span').filter({ hasText: '点击刷新' }).first(), label: '文案入口-filter' },
    { locator: page.locator('button, a, div, span').filter({ hasText: '刷新二维码' }).first(), label: '刷新二维码-filter' },
  ];

  let clickedLabel = null;
  for (const candidate of candidates) {
    try {
      if (!(await candidate.locator.count())) continue;
      // 对覆盖层候选额外检查可见性，避免命中隐藏节点。
      if (candidate.label.startsWith('过期覆盖层')) {
        const box = await candidate.locator.boundingBox().catch(() => null);
        if (!box || box.width < 80 || box.height < 80) continue;
      }
      let clicked = false;
      await candidate.locator.click({ timeout: 1200, force: true, noWaitAfter: true }).then(() => {
        clicked = true;
      }).catch(() => {});
      if (!clicked) {
        await candidate.locator.evaluate((node) => {
          if (node && typeof node.click === 'function') node.click();
        }).then(() => {
          clicked = true;
        }).catch(() => {});
      }
      if (!clicked) continue;
      clickedLabel = candidate.label;
      await page.waitForTimeout(250);
      break;
    } catch {}
  }

  if (!clickedLabel) {
    const qr = await findQrLocator(page);
    if (qr) {
      await qr.click({ timeout: 1500 }).catch(() => {});
      clickedLabel = '二维码区域兜底';
    }
  }

  if (!clickedLabel) {
    logger.log('检测到二维码可能过期，但未找到可点击的刷新入口。');
    return { refreshed: false, status, verified: false };
  }

  // 等待番茄完成“过期覆盖层→失效文案→新码”状态迁移，再截图，避免拍到中间过渡态
  const transition = await waitForQrTransitionDone(page, { maxWaitMs: 6000, pollMs: 400, logger });
  logger.log(`状态迁移等待: done=${transition.done} rounds=${transition.rounds} timedOut=${!!transition.timedOut}`);

  // 只有番茄跳回了验证码页时，才需要再次切回扫码视图。
  if (!transition.state?.inQrView || transition.state?.hasVisibleCodeInput) {
    await switchToQrLogin(page, logger).catch(() => false);
  }

  if (qrPath) {
    await captureQrScreenshot(page, qrPath, logger).catch(() => null);
  }
  const afterPath = path.join(debugDir, `${stamp}-after.png`);
  copyIfExists(qrPath, afterPath);
  const afterHash = qrPath ? sha256File(qrPath) : null;
  const changed = !!beforeHash && !!afterHash && beforeHash !== afterHash;

  // 此时已确认过渡完成（或超时），直接做一次 recheck
  let recheck = await detectQrExpired(page, qrPath, logger).catch(() => ({ expired: null, source: 'recheck-error' }));

  // 若过渡超时（状态迁移未完成），再多等一次
  if (transition.timedOut && recheck.expired) {
    logger.log('状态迁移超时，额外等待后再复检...');
    await page.waitForTimeout(2000);
    if (qrPath) {
      await captureQrScreenshot(page, qrPath, logger).catch(() => null);
      copyIfExists(qrPath, path.join(debugDir, `${stamp}-after-delayed.png`));
    }
    recheck = await detectQrExpired(page, qrPath, logger).catch(() => ({ expired: null, source: 'recheck-error-delayed' }));
  }

  // 成功判定：图片 hash 变化 且 过期标志消失 且 不是非扫码视图
  // 若 hash 未变但 inQrView 已清洁（无过期覆盖层、无失效文案），也认为刷新成功
  const finalQrState = await getQrViewState(page).catch(() => null);
  const cleanQrView = !!(finalQrState?.inQrView && !finalQrState?.hasExpiredOverlay && !finalQrState?.hasExpiredText);
  const verified = (changed || cleanQrView) && !recheck.expired && !recheck.nonQrView;

  logger.log(`已执行二维码刷新点击（${clickedLabel}），并尝试切回扫码登录。`);
  logger.log(`刷新验证: changed=${changed}, cleanQrView=${cleanQrView}, beforeHash=${beforeHash ? beforeHash.slice(0, 12) : 'null'}, afterHash=${afterHash ? afterHash.slice(0, 12) : 'null'}, expired=${String(recheck.expired)}, source=${recheck.source || 'unknown'}${recheck.nonQrView ? ', nonQrView=true' : ''}${recheck.hasExpiredOverlay ? ', hasExpiredOverlay=true' : ''}, qrView=${finalQrState?.inQrView ? 'true' : 'false'}, expiredOverlay=${finalQrState?.hasExpiredOverlay ? 'true' : 'false'}`);

  return { refreshed: true, status, verified, changed, cleanQrView, recheck, beforeHash, afterHash, clickedLabel, transition };
}

async function prepareQrForSharing(page, qrPath, logger = console) {
  logger.log('DEBUG: enter prepareQrForSharing');
  await page.bringToFront().catch(() => {});
  await switchToQrLogin(page, logger).catch(() => false);

  let qrCapture = null;
  if (qrPath) {
    qrCapture = await captureQrScreenshot(page, qrPath, logger).catch(() => null);
    if (qrCapture?.path) {
      logger.log(`扫码登录后已立即保存候选二维码截图: ${qrCapture.path} (${qrCapture.scope})`);
    }
  }

  let attempts = 0;
  while (attempts < 3) {
    const status = await detectQrExpired(page, qrCapture?.path || qrPath, logger).catch(() => ({ expired: false, source: 'check-error' }));
    logger.log(`二维码分享前检查: expired=${!!status.expired}, source=${status.source || 'unknown'}${status.nonQrView ? ', nonQrView=true' : ''}${status.text ? `, text=${JSON.stringify(status.text.slice(0, 120))}` : ''}`);

    if (status.nonQrView) {
      await switchToQrLogin(page, logger).catch(() => false);
      if (qrPath) {
        qrCapture = await captureQrScreenshot(page, qrPath, logger).catch(() => qrCapture);
        if (qrCapture?.path) {
          logger.log(`已切回扫码登录并更新候选二维码截图: ${qrCapture.path} (${qrCapture.scope})`);
        }
      }
      attempts += 1;
      continue;
    }

    if (status.expired) {
      const refreshResult = await refreshQrIfExpired(page, qrPath, logger).catch(() => ({ refreshed: false, status, verified: false }));
      const recheck = refreshResult?.recheck || await detectQrExpired(page, qrPath).catch(() => ({ expired: null, source: 'recheck-error' }));
      logger.log(`二维码分享前复检: expired=${String(recheck.expired)}, source=${recheck.source || 'unknown'}${recheck.nonQrView ? ', nonQrView=true' : ''}${recheck.text ? `, text=${JSON.stringify(recheck.text.slice(0, 120))}` : ''}`);
      if (refreshResult?.verified || (!recheck.expired && !recheck.nonQrView)) {
        qrCapture = await captureQrScreenshot(page, qrPath, logger);
        logger.log(`二维码刷新后已保存新鲜截图: ${qrCapture.path} (${qrCapture.scope})`);
        return { qrCapture, refreshResult, finalStatus: recheck };
      }
      attempts += 1;
      continue;
    }

    if (!qrCapture?.path && qrPath) {
      qrCapture = await captureQrScreenshot(page, qrPath, logger).catch(() => qrCapture);
    }
    logger.log(`二维码可用，直接采用候选截图: ${qrCapture.path} (${qrCapture.scope})`);
    return { qrCapture, refreshResult: { refreshed: false, status }, finalStatus: status };
  }

  const finalStatus = await detectQrExpired(page, qrPath).catch(() => ({ expired: null, source: 'final-check-error' }));
  if (!finalStatus?.expired && !finalStatus?.nonQrView) {
    qrCapture = await captureQrScreenshot(page, qrPath, logger).catch(() => qrCapture);
    if (qrCapture?.path) {
      logger.log(`最终兜底保存二维码截图: ${qrCapture.path} (${qrCapture.scope})`);
    }
  }
  return { qrCapture, refreshResult: { refreshed: false, status: finalStatus }, finalStatus };
}

async function ensureLoggedIn(page, options = {}) {
  const {
    loginUrl = LOGIN_URL,
    qrPath,
    logger = console,
    waitAfterOpenMs = 2500,
    pollIntervalMs = 3000,
    timeoutMs = 5 * 60 * 1000,
    saveStorageState,
    onQrReady,
  } = options;

  if (!page.url() || page.url() === 'about:blank') {
    await page.goto(loginUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(waitAfterOpenMs);
  }
  await page.bringToFront().catch(() => {});

  if (await isLoggedIn(page)) {
    return { loggedIn: true, alreadyLoggedIn: true };
  }

  let qrCapture = null;
  let lastNotifiedQrHash = null;
  if (qrPath) {
    const prepared = await prepareQrForSharing(page, qrPath, logger);
    qrCapture = prepared.qrCapture;
    const finalStatus = prepared.finalStatus || prepared.refreshResult?.status;
    if (finalStatus?.nonQrView) {
      logger.log('二维码分享准备失败：当前仍不是扫码登录视图，暂不发图。');
    } else {
      lastNotifiedQrHash = await notifyQrReadyIfNeeded({
        qrCapture,
        qrStatus: finalStatus,
        onQrReady,
        first: true,
        refreshed: !!prepared.refreshResult?.refreshed,
        lastNotifiedQrHash,
      });
    }
  }
  logger.log('检测到未登录，正在等待扫码登录完成...');

  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await page.waitForTimeout(pollIntervalMs);
    if (await isLoggedIn(page)) {
      if (typeof saveStorageState === 'function') {
        await saveStorageState();
      }
      logger.log('检测到登录完成。');
      return { loggedIn: true, alreadyLoggedIn: false, qrCapture };
    }

    if (qrPath) {
      const refreshResult = await refreshQrIfExpired(page, qrPath, logger).catch(() => ({ refreshed: false }));
      let status = null;
      if (refreshResult?.refreshed) {
        const refreshed = await captureQrScreenshot(page, qrPath, logger).catch(() => null);
        if (refreshed?.path) qrCapture = refreshed;
        status = await detectQrExpired(page, qrPath).catch(() => ({ expired: null, source: 'recheck-error' }));
        logger.log(`轮询期刷新后二次检查: expired=${String(status.expired)}, source=${status.source || 'unknown'}${status.nonQrView ? ', nonQrView=true' : ''}${status.text ? `, text=${JSON.stringify(status.text.slice(0, 120))}` : ''}`);
      }
      if ((refreshResult?.refreshed || !lastNotifiedQrHash) && qrCapture?.path) {
        if (!status) {
          status = await detectQrExpired(page, qrPath).catch(() => ({ expired: null, source: 'notify-check-error' }));
        }
        lastNotifiedQrHash = await notifyQrReadyIfNeeded({
          qrCapture,
          qrStatus: status,
          onQrReady,
          first: !lastNotifiedQrHash,
          refreshed: !!refreshResult?.refreshed,
          lastNotifiedQrHash,
        });
      }
    }
  }

  return { loggedIn: false, timedOut: true, qrCapture };
}

module.exports = {
  LOGIN_URL,
  ensureDir,
  isLoggedIn,
  switchToQrLogin,
  findQrLocator,
  captureQrScreenshot,
  detectQrExpired,
  refreshQrIfExpired,
  waitForQrTransitionDone,
  prepareQrForSharing,
  getQrViewState,
  ensureLoggedIn,
};
