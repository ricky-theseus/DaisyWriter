#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { spawnSync, execFile } = require('child_process');
const { promisify } = require('util');
const { ensureDir, ensureLoggedIn } = require('./fanqie_login_flow');
const { resolvePage } = require('./browser_page_picker');

let BOOK_ID = '';
let BOOK_NAME = '';
function draftURL() { return `https://fanqienovel.com/main/writer/${BOOK_ID}/publish/?enter_from=newchapter_0`; }
function chapterManageURL() { return `https://fanqienovel.com/main/writer/chapter-manage/${BOOK_ID}&${encodeURIComponent(BOOK_NAME)}?type=1`; }
const DEFAULT_DAILY_LIMIT_CHARS = 50000; // inferred from real Fanqie backend behavior; treat as a safety guard, not an official documented rule.
const execFileAsync = promisify(execFile);

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const key = argv[i];
    const next = argv[i + 1];
    if (!key.startsWith('--')) continue;
    if (!next || next.startsWith('--')) args[key.slice(2)] = true;
    else {
      args[key.slice(2)] = next;
      i += 1;
    }
  }
  return args;
}

function loadChapters(args) {
  const prep = path.resolve(__dirname, 'prepare_chapters.py');
  if (args.file) {
    const dir = path.dirname(args.file);
    const py = process.platform === 'win32' ? 'python' : 'python3';
    const res = spawnSync(py, [prep, '--dir', dir], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    if (res.status !== 0) throw new Error(res.stderr || 'prepare_chapters failed');
    return JSON.parse(res.stdout).filter((c) => c.file === args.file);
  }
  if (args.dir) {
    const py = process.platform === 'win32' ? 'python' : 'python3';
    const res = spawnSync(py, [prep, '--dir', args.dir], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    if (res.status !== 0) throw new Error(res.stderr || 'prepare_chapters failed');
    return JSON.parse(res.stdout);
  }
  throw new Error('Provide --file or --dir');
}

function filterChapters(chapters, args) {
  let items = [...chapters];

  // --range "第0005章-第0010章" or "5-10" or "0005-0010"
  if (args.range) {
    const rangeStr = String(args.range).trim();
    const parts = rangeStr.split(/[-–—]/).map(s => s.trim());
    if (parts.length === 2) {
      const findIdx = (kw) => items.findIndex((c) =>
        c.name.includes(kw) || c.title.includes(kw) || c.serial?.includes(kw) ||
        (c.display_title && (c.name.includes(kw) || c.title.includes(kw)))
      );
      // Try finding start/end by keyword
      let si = findIdx(parts[0]);
      if (si === -1) {
        // treat as chapter number (e.g. "5" → "第0005章")
        const padded = String(parts[0]).padStart(4, '0');
        si = items.findIndex(c => c.serial === `第${padded}章` || c.name.includes(padded));
        if (si === -1) si = Number(parts[0]) - 1;
      }
      let ei = findIdx(parts[1]);
      if (ei === -1) {
        const padded = String(parts[1]).padStart(4, '0');
        ei = items.findIndex(c => c.serial === `第${padded}章` || c.name.includes(padded));
        if (ei === -1) ei = Number(parts[1]) - 1;
      }
      if (si >= 0 && ei >= 0 && ei >= si) items = items.slice(si, ei + 1);
    }
    return items;
  }

  if (args['start-from']) {
    const keyword = String(args['start-from']).trim();
    const idx = items.findIndex((c) => c.name.includes(keyword) || c.title.includes(keyword) || c.display_title?.includes(keyword));
    if (idx >= 0) items = items.slice(idx);
  }

  if (args['end-at']) {
    const keyword = String(args['end-at']).trim();
    const idx = items.findIndex((c) => c.name.includes(keyword) || c.title.includes(keyword) || c.display_title?.includes(keyword));
    if (idx >= 0) items = items.slice(0, idx + 1);
  }

  const limit = args.range ? items.length : Number(args.limit || items.length || 1);
  return items.slice(0, limit);
}

function applyDailyLimitGuard(chapters, args) {
  const mode = args.mode || 'draft-only';
  if (mode !== 'immediate') return chapters;
  const dailyLimit = Number(args['daily-limit-chars'] || DEFAULT_DAILY_LIMIT_CHARS);
  const alreadyPublished = Number(args['already-published-chars'] || 0);
  let running = alreadyPublished;
  const accepted = [];
  for (const chapter of chapters) {
    const next = running + Number(chapter.word_count || 0);
    if (next > dailyLimit) break;
    accepted.push(chapter);
    running = next;
  }
  return accepted;
}

function resolveScheduleAt(base, index, stepMinutes = 30) {
  const dt = new Date(base.replace(' ', 'T'));
  if (Number.isNaN(dt.getTime())) throw new Error(`Invalid --schedule-at value: ${base}`);
  dt.setMinutes(dt.getMinutes() + index * stepMinutes);
  const yyyy = dt.getFullYear();
  const mm = String(dt.getMonth() + 1).padStart(2, '0');
  const dd = String(dt.getDate()).padStart(2, '0');
  const hh = String(dt.getHours()).padStart(2, '0');
  const mi = String(dt.getMinutes()).padStart(2, '0');
  return { date: `${yyyy}-${mm}-${dd}`, time: `${hh}:${mi}`, full: `${yyyy}-${mm}-${dd} ${hh}:${mi}` };
}

function loadPublishState(stateFile) {
  if (!fs.existsSync(stateFile)) return { published: [] };
  return JSON.parse(fs.readFileSync(stateFile, 'utf8'));
}

function savePublishState(stateFile, state) {
  ensureDir(path.dirname(stateFile));
  fs.writeFileSync(stateFile, JSON.stringify(state, null, 2), 'utf8');
}

function isPublishedInState(state, file) {
  return (state.published || []).some((item) => item.file === file);
}

function markPublished(stateFile, chapter, verify, mode) {
  const state = loadPublishState(stateFile);
  if (isPublishedInState(state, chapter.file)) return;
  state.published ||= [];
  state.published.push({
    file: chapter.file,
    title: chapter.title,
    status: verify.status || null,
    publishedAt: verify.publishTime || null,
    rowText: verify.rowText || null,
    mode,
    recordedAt: new Date().toISOString(),
  });
  savePublishState(stateFile, state);
}

function isRetryableFailure(result) {
  const reason = String(result?.reason || '');
  if (!reason) return false;
  if (/等待扫码登录超时|单日字数上限/.test(reason)) return false;
  return /未检测到最终发布弹窗|章节管理页未找到目标章节|弹窗仍未关闭|Target closed|Execution context was destroyed|Navigation failed|Timeout|ERR_|blocked:/.test(reason);
}

async function ensureRemoteBrowserReady(cdpUrl) {
  if (!cdpUrl || (!cdpUrl.startsWith('http://') && !cdpUrl.startsWith('https://'))) return;
  const jsonUrl = cdpUrl.replace(/\/$/, '') + '/json/version';

  const canReach = async () => {
    try {
      const res = await fetch(jsonUrl);
      return !!res.ok;
    } catch {
      return false;
    }
  };

  if (await canReach()) return;

  const ps1 = '/home/amm10090/.openclaw/workspace-fanqie-publish/scripts/start_remote_chrome.ps1';
  if (!fs.existsSync(ps1)) return;
  try {
    await execFileAsync('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', [
      '-NoProfile',
      '-ExecutionPolicy', 'Bypass',
      '-File', `\\wsl.localhost\\Ubuntu-24.04${ps1.replace(/\//g, '\\')}`,
    ], { timeout: 30000 });
  } catch {}

  for (let i = 0; i < 8; i++) {
    if (await canReach()) return;
    await new Promise((r) => setTimeout(r, 1000));
  }
}

async function connectBrowser(args, statePath, playwright) {
  let cdpUrl = args.cdp || null;
  const { chromium } = playwright;
  let browser;
  let context;

  if (cdpUrl) {
    await ensureRemoteBrowserReady(cdpUrl);
    if (cdpUrl.startsWith('http://') || cdpUrl.startsWith('https://')) {
      const jsonUrl = cdpUrl.replace(/\/$/, '') + '/json/version';
      const res = await fetch(jsonUrl);
      if (!res.ok) throw new Error(`Failed to query DevTools endpoint: ${jsonUrl} => ${res.status}`);
      const meta = await res.json();
      cdpUrl = meta.webSocketDebuggerUrl || cdpUrl;
    }
    browser = await chromium.connectOverCDP(cdpUrl);
    context = browser.contexts()[0] || await browser.newContext({ storageState: statePath });
  } else {
    browser = await chromium.launch({ headless: false, slowMo: 80 });
    context = await browser.newContext({ storageState: statePath });
  }

  return { browser, context };
}

function chapterNumber(chapter) {
  if (!chapter.serial) return null;
  return String(parseInt(String(chapter.serial).replace(/^第/, '').replace(/章$/, ''), 10));
}

async function collectVolumeDebugInfo(page) {
  return await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const nodes = Array.from(document.querySelectorAll('label,button,input,textarea,select,[role="combobox"],[role="button"],[role="option"],.arco-select,.byte-select,.semi-select,.arco-form-item,.byte-form-item,div,span'));
    const hits = [];
    for (const el of nodes) {
      if (!isVisible(el)) continue;
      const text = normalize(el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '');
      const cls = normalize(el.className || '');
      const role = normalize(el.getAttribute('role') || '');
      const placeholder = normalize(el.getAttribute('placeholder') || '');
      const ariaLabel = normalize(el.getAttribute('aria-label') || '');
      const joined = `${text} ${cls} ${role} ${placeholder} ${ariaLabel}`;
      if (!/(分卷|卷名|正文卷|作品相关|序章|尾声)/.test(joined)) continue;
      hits.push({
        tag: el.tagName.toLowerCase(),
        role,
        text: text.slice(0, 200),
        className: cls.slice(0, 200),
        placeholder,
        ariaLabel,
      });
      if (hits.length >= 40) break;
    }
    return hits;
  });
}

async function findVolumeTrigger(page) {
  const strongCssCandidates = [
    '.publish-maintain-volume',
    '.publish-header-volume-name',
  ];

  for (const selector of strongCssCandidates) {
    const locator = page.locator(selector).first();
    if (await locator.count()) return locator;
  }

  const xpathCandidates = [
    '//*[contains(normalize-space(.),"分卷")]/following::*[@role="combobox" or self::button or self::input or contains(@class,"select")][1]',
    '//*[contains(normalize-space(.),"分卷")]/ancestor::*[self::div or self::label][1]//*[self::button or self::input or @role="combobox" or contains(@class,"select")][1]',
    '//*[contains(normalize-space(.),"第一卷") or contains(normalize-space(.),"第二卷") or contains(normalize-space(.),"第三卷")][self::div or self::span or self::button][1]',
    '//*[contains(normalize-space(.),"卷：") or contains(normalize-space(.),"卷:")][self::div or self::span or self::button][1]',
  ];

  for (const xp of xpathCandidates) {
    const locator = page.locator(`xpath=${xp}`).first();
    if (await locator.count()) return locator;
  }

  const cssCandidates = [
    '[role="combobox"]',
    '.arco-select',
    '.byte-select',
    '.semi-select',
    'input[placeholder*="分卷"]',
    'input[aria-label*="分卷"]',
    'button:has-text("正文卷")',
    'button:has-text("作品相关")',
  ];

  for (const selector of cssCandidates) {
    const locator = page.locator(selector).first();
    if (await locator.count()) return locator;
  }
  return null;
}

function expandVolumeNameCandidates(volumeName) {
  const base = String(volumeName || '').trim();
  if (!base) return [];
  const set = new Set([base]);
  if (base === '第一卷') set.add('默认');
  if (base === '默认') set.add('第一卷');
  if (base === '正文卷') set.add('正文');
  if (base === '正文') set.add('正文卷');
  return Array.from(set);
}

async function collectVisibleVolumeOptions(page) {
  return await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const optionLikeSelectors = [
      '[role="option"]',
      '.arco-select-option',
      '.byte-select-option',
      '.semi-select-option',
      '.arco-dropdown-menu-item',
      '.byte-dropdown-menu-item',
      '.arco-list-item',
      '.publish-maintain-volume',
      '.publish-header-volume-name',
      'li',
      'button',
      'div',
      'span'
    ];
    const seen = new Set();
    const results = [];
    for (const selector of optionLikeSelectors) {
      for (const el of Array.from(document.querySelectorAll(selector))) {
        if (!isVisible(el)) continue;
        const text = normalize(el.innerText || el.textContent || '');
        if (!text) continue;
        if (text.length > 120) continue;
        if (!/(卷|正文|默认|作品相关|序章|尾声)/.test(text)) continue;
        if (seen.has(text)) continue;
        seen.add(text);
        results.push({
          text,
          tag: el.tagName.toLowerCase(),
          role: normalize(el.getAttribute('role') || ''),
          className: normalize(el.className || '').slice(0, 160),
        });
        if (results.length >= 80) return results;
      }
    }
    return results;
  });
}

async function snapshotVolumeRelatedNodes(page) {
  return await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const selectors = [
      'body *',
      '[role="dialog"]',
      '[role="option"]',
      '.arco-modal',
      '.byte-modal',
      '.arco-dropdown',
      '.byte-dropdown',
      '.arco-popover',
      '.byte-popover',
      '.arco-trigger-popup',
      '.byte-trigger-popup',
      '.arco-select-view',
      '.arco-select-option',
      '.byte-select-option',
      '.publish-maintain-volume',
      '.publish-header-volume-name'
    ];
    const nodes = [];
    const seen = new Set();
    for (const selector of selectors) {
      for (const el of Array.from(document.querySelectorAll(selector))) {
        if (!isVisible(el)) continue;
        const text = normalize(el.innerText || el.textContent || '');
        const cls = normalize(el.className || '');
        const role = normalize(el.getAttribute('role') || '');
        const key = [el.tagName, cls, role, text.slice(0, 120)].join('|');
        if (seen.has(key)) continue;
        seen.add(key);
        if (!text && !cls) continue;
        if (!(role || /(卷|默认|正文|作品相关|序章|尾声|select|dropdown|popup|popover|modal|dialog|volume)/i.test(`${text} ${cls}`))) continue;
        nodes.push({
          tag: el.tagName.toLowerCase(),
          role,
          className: cls.slice(0, 240),
          text: text.slice(0, 240),
        });
        if (nodes.length >= 200) return nodes;
      }
    }
    return nodes;
  });
}

function diffVolumeNodeSnapshots(before = [], after = []) {
  const beforeKeys = new Set(before.map((item) => JSON.stringify(item)));
  return after.filter((item) => !beforeKeys.has(JSON.stringify(item)));
}

async function selectVolume(page, volumeName, shotsDir, prefix, args = {}) {
  if (!volumeName) return { ok: true, skipped: true };
  const debugInfo = await collectVolumeDebugInfo(page);
  if (args['debug-volume']) {
    console.log('VOLUME_DEBUG_CANDIDATES');
    console.log(JSON.stringify(debugInfo, null, 2));
  }

  await page.waitForTimeout(1200);
  const trigger = await findVolumeTrigger(page);
  if (!trigger) {
    return { ok: false, reason: '未找到“分卷选择”控件。', debugInfo };
  }

  const beforeText = ((await trigger.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
  const volumeCandidates = expandVolumeNameCandidates(volumeName);
  if (volumeCandidates.length && beforeText && volumeCandidates.some((name) => beforeText.includes(name))) {
    return { ok: true, alreadyMatched: true, selected: volumeName, matchedAs: beforeText, debugInfo, triggerText: beforeText };
  }

  const beforeSnapshot = (args['diff-volume-nodes'] || args['list-volume-options'])
    ? await snapshotVolumeRelatedNodes(page)
    : [];

  const clicked = await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const preferred = document.querySelector('.publish-maintain-volume, .publish-header-volume-name');
    if (preferred && isVisible(preferred)) {
      preferred.click();
      return normalize(preferred.innerText || preferred.textContent || '');
    }
    return null;
  });

  if (!clicked) {
    await trigger.click({ timeout: 5000 }).catch(async () => {
      const nested = trigger.locator('input,button,div,span').first();
      if (await nested.count()) {
        await nested.click({ timeout: 5000, force: true });
        return;
      }
      await trigger.click({ timeout: 5000, force: true });
    });
  }
  await page.waitForTimeout(800);
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-01a-volume-open.png`), fullPage: true }).catch(() => {});
  }

  const afterSnapshot = (args['diff-volume-nodes'] || args['list-volume-options'])
    ? await snapshotVolumeRelatedNodes(page)
    : [];
  const diffNodes = (args['diff-volume-nodes'] || args['list-volume-options'])
    ? diffVolumeNodeSnapshots(beforeSnapshot, afterSnapshot)
    : [];

  const visibleOptions = await collectVisibleVolumeOptions(page);
  if (args['diff-volume-nodes']) {
    console.log('VOLUME_DIFF_NODES');
    console.log(JSON.stringify(diffNodes, null, 2));
  }
  if (args['list-volume-options']) {
    console.log('VOLUME_VISIBLE_OPTIONS');
    console.log(JSON.stringify(visibleOptions, null, 2));
    await page.keyboard.press('Escape').catch(() => {});
    return { ok: true, inspectOnly: true, debugInfo, triggerText: beforeText, visibleOptions, diffNodes };
  }

  if (!volumeName) {
    return { ok: true, skipped: true, debugInfo, triggerText: beforeText, visibleOptions };
  }

  const optionSelectors = [
    '[role="option"]',
    '.arco-select-option',
    '.byte-select-option',
    '.semi-select-option',
    '.arco-cascader-option',
    '.arco-select-view-value',
    '.arco-dropdown-menu-item',
    '.byte-dropdown-menu-item',
    'li',
    'button',
    'div',
    'span',
  ];

  let option = null;
  for (const alias of volumeCandidates) {
    for (const selector of optionSelectors) {
      const exact = page.locator(selector).filter({ hasText: alias }).first();
      if (await exact.count()) {
        option = exact;
        break;
      }
    }
    if (option) break;
  }

  if (!option) {
    for (const alias of volumeCandidates) {
      const escaped = alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      for (const selector of optionSelectors) {
        const partial = page.locator(selector).filter({ hasText: new RegExp(escaped, 'i') }).first();
        if (await partial.count()) {
          option = partial;
          break;
        }
      }
      if (option) break;
    }
  }

  if (!option) {
    await page.keyboard.press('Escape').catch(() => {});
    return { ok: false, reason: `已打开分卷控件，但未找到目标分卷：${volumeName}`, debugInfo, triggerText: beforeText, visibleOptions };
  }

  await option.click({ timeout: 5000 });
  await page.waitForTimeout(800);
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-01b-volume-selected.png`), fullPage: true }).catch(() => {});
  }

  return { ok: true, selected: volumeName, debugInfo, triggerText: beforeText, visibleOptions };
}

async function ensureVolumeFromChapterManage(page, volumeName, shotsDir, prefix, args = {}) {
  const aliases = expandVolumeNameCandidates(volumeName);
  await page.goto(chapterManageURL(), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-00-chapter-manage-before-volume.png`), fullPage: true }).catch(() => {});
  }

  const current = ((await page.locator('.chapter-select .byte-select-view-value').first().innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
  if (aliases.length && aliases.some((name) => current.includes(name))) {
    return { ok: true, selected: volumeName, alreadyMatched: true, triggerText: current, via: 'chapter-manage' };
  }

  const trigger = page.locator('.chapter-select .serial-select.flat-serial-select.byte-select.byte-select-size-default, .chapter-select .serial-select, .chapter-select .byte-select-view-value').first();
  if (!await trigger.count()) {
    return { ok: false, reason: '章节管理页未找到分卷下拉控件。' };
  }
  await trigger.click({ timeout: 5000 }).catch(async () => trigger.click({ timeout: 5000, force: true }));
  await page.waitForTimeout(1000);
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-00a-chapter-manage-volume-open.png`), fullPage: true }).catch(() => {});
  }

  let option = null;
  for (const alias of aliases) {
    option = page.locator('.byte-select-popup .byte-select-option.chapter-select-option, .byte-select-option.chapter-select-option, .byte-select-option').filter({ hasText: alias }).first();
    if (await option.count()) break;
  }
  if (!option || !await option.count()) {
    await page.keyboard.press('Escape').catch(() => {});
    return { ok: false, reason: `章节管理页未找到目标分卷：${volumeName}` };
  }

  await option.click({ timeout: 5000 }).catch(async () => option.click({ timeout: 5000, force: true }));
  await page.waitForTimeout(1500);
  const after = ((await page.locator('.chapter-select .byte-select-view-value').first().innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-00b-chapter-manage-volume-selected.png`), fullPage: true }).catch(() => {});
  }
  if (!aliases.some((name) => after.includes(name))) {
    return { ok: false, reason: `章节管理页切分卷后未生效：${after || 'EMPTY'}` };
  }
  return { ok: true, selected: volumeName, triggerText: after, via: 'chapter-manage' };
}

async function openDraftFromChapterManage(page, shotsDir, prefix) {
  const newLink = page.locator('a[href*="/publish/"][href*="enter_from=newchapter"], a[href*="/publish/?enter_from=newchapter"], a:has-text("新建章节")').first();
  if (await newLink.count()) {
    const href = await newLink.getAttribute('href').catch(() => null);
    if (href) {
      const targetUrl = href.startsWith('http') ? href : new URL(href, page.url()).toString();
      await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    } else {
      await newLink.click({ timeout: 5000 }).catch(async () => newLink.click({ timeout: 5000, force: true }));
    }
  } else {
    const newBtn = page.locator('button').filter({ hasText: '新建章节' }).first();
    if (!await newBtn.count()) throw new Error('章节管理页未找到“新建章节”入口。');
    await newBtn.click({ timeout: 5000 }).catch(async () => newBtn.click({ timeout: 5000, force: true }));
  }
  await page.waitForTimeout(3500);
  if (!/\/publish\//.test(page.url())) {
    await page.goto(draftURL(), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
  }
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-01-publish-page.png`), fullPage: true }).catch(() => {});
  }
}

async function dismissEditorGuides(page, shotsDir, prefix) {
  const maxRounds = 8;
  for (let round = 1; round <= maxRounds; round++) {
    const guide = page.locator('.reactour__helper, .publish-guide, [role="dialog"], .arco-modal, .byte-modal').last();
    if (!await guide.count()) break;
    const text = ((await guide.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
    let handled = false;
    const labels = ['知道了', '我知道了', '下一步', '完成', '跳过', '关闭'];
    for (const label of labels) {
      const btn = guide.locator('button, div, span').filter({ hasText: label }).first();
      if (await btn.count()) {
        await btn.click({ timeout: 3000 }).catch(async () => btn.click({ timeout: 3000, force: true }));
        handled = true;
        await page.waitForTimeout(800);
        break;
      }
    }
    if (!handled) {
      const closeBtn = guide.locator('[aria-label="Close"], .reactour__close-button, .arco-modal-close-icon, .byte-modal-close-icon').first();
      if (await closeBtn.count()) {
        await closeBtn.click({ timeout: 3000 }).catch(async () => closeBtn.click({ timeout: 3000, force: true }));
        handled = true;
        await page.waitForTimeout(800);
      }
    }
    if (!handled && /\d+\s*\/\s*\d+/.test(text)) {
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(500);
      handled = true;
    }
    if (!handled) break;
  }
  if (shotsDir && prefix) {
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-01-guide-dismissed.png`), fullPage: true }).catch(() => {});
  }
}

async function fillDraft(page, chapter, shotsDir, prefix, args = {}) {
  let volumeResult = { ok: true, skipped: true };
  if (args.volume) {
    volumeResult = await ensureVolumeFromChapterManage(page, args.volume, shotsDir, prefix, args);
    if (!volumeResult.ok) {
      throw new Error(volumeResult.reason || '章节管理页分卷切换失败');
    }
    if (args['debug-volume-stop']) {
      return { mode: 'debug-volume-stop', volumeResult };
    }
    await openDraftFromChapterManage(page, shotsDir, prefix);
    await dismissEditorGuides(page, shotsDir, prefix);
  } else {
    await page.goto(draftURL(), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3500);
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-01-publish-page.png`), fullPage: true });
    await dismissEditorGuides(page, shotsDir, prefix);

    volumeResult = await selectVolume(page, args.volume, shotsDir, prefix, args);
    if (!volumeResult.ok) {
      throw new Error(volumeResult.reason || '分卷选择失败');
    }
    if (args['debug-volume-stop']) {
      return { mode: 'debug-volume-stop', volumeResult };
    }
  }

  const serialInput = page.locator('input.serial-input.byte-input.byte-input-size-default').first();
  const num = chapterNumber(chapter);
  if (num) await serialInput.fill(num);

  const titleInput = page.locator('input[placeholder="请输入标题"]').first();
  await titleInput.fill(chapter.display_title || chapter.title);

  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(500);
  await editor.evaluate(() => {
    const editorEl = document.querySelector('.ProseMirror');
    const view = editorEl.pmViewDesc.node.type.schema.nodes.image.spec.editor.configurator.view;
    const tr = view.state.tr;
    tr.delete(0, view.state.doc.content.size);
    view.dispatch(tr);
  });
  const cleanContent = chapter.content.replace(/\r\n/g, '\n');
  await page.evaluate((c) => {
    const s = document.createElement('script');
    s.id = '__chapter_text';
    s.type = 'text/plain';
    s.textContent = c;
    document.body.appendChild(s);
  }, cleanContent);
  await editor.evaluate(() => {
    const content = document.getElementById('__chapter_text').textContent;
    const editorEl = document.querySelector('.ProseMirror');
    editorEl.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, content);
  });
  await page.waitForTimeout(3000);

  const saveBtn = page.locator('.auto-editor-save-btn').first();
  if (await saveBtn.count()) {
    await saveBtn.click();
    await page.waitForTimeout(2500);
  }

  await page.screenshot({ path: path.join(shotsDir, `${prefix}-02-filled-draft.png`), fullPage: true });
  return { mode: 'filled', volumeResult };
}

async function handleInterceptors(page) {
  const maxRounds = 15;
  for (let round = 1; round <= maxRounds; round++) {
    const publishModal = page.locator('.arco-modal.publish-confirm-container-new').last();
    if (await publishModal.count()) return 'publish-modal';

    const dialog = page.locator('.arco-modal[role="dialog"], .byte-modal[role="dialog"], .reactour__helper[role="dialog"], .reactour__helper, .arco-modal, .byte-modal').last();
    if (await dialog.count()) {
      const text = ((await dialog.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();

      const isSpellcheck = /错别字|智能纠错|是否确定提交|发布提示/.test(text);
      const isRiskDetection = /是否进行内容风险检测|风险检测/.test(text);
      const isGuide = /知道了|我知道了|下一步|跳过|完成|欢迎|引导|卡文锦囊|AI帮你/.test(text);

      let candidates = [];
      if (isSpellcheck) {
        candidates = ['替换全部', '全部替换', '确认替换', '提交'];
      } else if (isRiskDetection) {
        candidates = ['普通检测', '确定', '确认', '提交'];
      } else if (isGuide) {
        candidates = ['我知道了', '知道了', '下一步', '完成', '跳过', '关闭'];
      }

      let handled = false;
      for (const label of candidates) {
        const btn = dialog.locator('button').filter({ hasText: label }).first();
        if (await btn.count()) {
          console.log(`已处理拦路弹窗 ${round}: [${label}] ${text.slice(0, 160)}`);
          await btn.click().catch(async () => btn.click({ force: true }));
          await page.waitForTimeout(2500);
          handled = true;
          break;
        }
      }

      const publishModal2 = page.locator('.arco-modal.publish-confirm-container-new').last();
      if (await publishModal2.count()) return 'publish-modal';

      const anyDialog = page.locator('.arco-modal[role="dialog"], .byte-modal[role="dialog"], .reactour__helper[role="dialog"], .reactour__helper, .arco-modal, .byte-modal').last();
      if (!(await anyDialog.count())) continue;

      if (!handled && isGuide) {
        const closeBtn = anyDialog.locator('[aria-label="Close"], .reactour__close-button, .arco-modal-close-icon, .byte-modal-close-icon').first();
        if (await closeBtn.count()) {
          const t = ((await anyDialog.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
          console.log(`已关闭引导弹窗 ${round}: ${t.slice(0, 160)}`);
          await closeBtn.click().catch(async () => closeBtn.click({ force: true }));
          await page.waitForTimeout(2500);
          continue;
        }
      }

      if (!handled && (isSpellcheck || isRiskDetection)) {
        return `blocked:${isSpellcheck ? 'spellcheck' : 'risk-detection'}`;
      }

      if (!handled && !isGuide) {
        return 'blocked:unknown-dialog';
      }
    }
    await page.waitForTimeout(1200);
  }
  return 'unknown';
}

async function goToFinalPublishModal(page, chapter, shotsDir, prefix, args = {}) {
  await page.locator('.publish-button.auto-editor-next').first().click();
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(shotsDir, `${prefix}-03-after-next.png`), fullPage: true }).catch(() => {});

  const gateResult = await handleInterceptors(page);
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(shotsDir, `${prefix}-04-after-interceptors.png`), fullPage: true }).catch(() => {});

  const publishModal = page.locator('.arco-modal.publish-confirm-container-new').last();
  if (!await publishModal.count()) {
    return { ok: false, reason: `未检测到最终发布弹窗。gateResult=${gateResult}` };
  }

  const modalText = ((await publishModal.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
  const expectedNum = chapterNumber(chapter);
  const expectedTitle = chapter.display_title || chapter.title;
  const expectedFullTitle = expectedNum ? `第${expectedNum}章 ${expectedTitle}` : expectedTitle;
  if (args.volume && !modalText.includes(args.volume)) {
    return { ok: false, reason: `最终发布弹窗分卷不匹配：期望包含「${args.volume}」；实际为：${modalText.slice(0, 200)}` };
  }
  if (!modalText.includes(expectedTitle) && !modalText.includes(expectedFullTitle)) {
    return { ok: false, reason: `最终发布弹窗章节标题不匹配：期望「${expectedFullTitle}」；实际为：${modalText.slice(0, 200)}` };
  }

  const noLabel = publishModal.locator('label').filter({ hasText: '否' }).first();
  if (await noLabel.count()) {
    await noLabel.click().catch(async () => noLabel.click({ force: true }));
    await page.waitForTimeout(500);
  }

  const selectedAiNo = await publishModal.evaluate((el) => {
    const textNodes = Array.from(el.querySelectorAll('label, .arco-radio, .arco-radio-wrapper, [role="radio"], span, div'));
    for (const node of textNodes) {
      const text = String(node.textContent || '').replace(/\s+/g, ' ').trim();
      if (text !== '否') continue;
      const cls = String(node.className || '');
      const checked = cls.includes('checked') || node.getAttribute('aria-checked') === 'true';
      const nestedChecked = !!node.querySelector('.checked, .arco-radio-checked, [aria-checked="true"]');
      if (checked || nestedChecked) return true;
    }
    return false;
  }).catch(() => false);

  await page.screenshot({ path: path.join(shotsDir, `${prefix}-05-final-publish-modal-ai-no.png`), fullPage: true });
  if (!selectedAiNo) {
    return { ok: false, reason: '最终发布弹窗未成功选中「是否使用AI=否」。' };
  }
  return { ok: true, publishModal, modalText };
}

async function collectVisibleMessages(page) {
  return await page.evaluate(() => {
    const normalize = (s) => String(s || '').replace(/\s+/g, ' ').trim();
    const isVisible = (el) => {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const selectors = [
      '.arco-message', '.byte-message', '.arco-message-notice', '.byte-message-notice',
      '.arco-notification', '.byte-notification', '.toast', '[class*="toast"]',
      '[class*="message"]', '[class*="notification"]'
    ];
    const out = [];
    const seen = new Set();
    for (const selector of selectors) {
      for (const el of Array.from(document.querySelectorAll(selector))) {
        if (!isVisible(el)) continue;
        const text = normalize(el.innerText || el.textContent || '');
        if (!text) continue;
        if (seen.has(text)) continue;
        seen.add(text);
        out.push({ text, className: normalize(el.className || '').slice(0, 200) });
      }
    }
    return out;
  });
}

function detectPublishLimit(messages = []) {
  const joined = messages.map((m) => m.text).join(' | ');
  if (/(单日|当天|今日).*(字数|上限|限制)/.test(joined) || /(字数|章节).*(达到|超过).*(上限|限制)/.test(joined)) {
    return joined;
  }
  return null;
}

async function verifyPublished(page, chapter, shotsDir, prefix) {
  await page.goto(chapterManageURL(), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(shotsDir, `${prefix}-07-chapter-manage-after-publish.png`), fullPage: true });

  const expectedNum = chapterNumber(chapter);
  const displayTitle = chapter.display_title || chapter.title;
  return await page.evaluate(({ title, num }) => {
    const normalizedTitle = num ? `第${num}章 ${title}` : title;
    const rows = Array.from(document.querySelectorAll('.arco-table-tr'));
    for (const row of rows) {
      const text = (row.innerText || row.textContent || '').replace(/\s+/g, ' ').trim();
      if (!text || !text.includes(normalizedTitle)) continue;
      const cells = Array.from(row.querySelectorAll('.arco-table-td, .arco-table-cell'))
        .map((el) => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim())
        .filter(Boolean);
      return {
        found: true,
        title: normalizedTitle,
        rowText: text,
        cells,
        status: cells[3] || null,
        publishTime: cells[4] || null,
      };
    }
    return { found: false, title: normalizedTitle };
  }, { title: displayTitle, num: expectedNum });
}

async function publishOneOnce(page, context, chapter, args, shotsDir, stateFile, statePath, qrPath, index, attempt = 1) {
  const prefix = `${String(index + 1).padStart(2, '0')}-try${attempt}`;
  const mode = args.mode || 'immediate';
  const scheduleInfo = mode === 'scheduled' && args['schedule-at']
    ? resolveScheduleAt(args['schedule-at'], index, Number(args['schedule-step-minutes'] || 30))
    : null;
  console.log(`开始处理: ${chapter.title} (${path.basename(chapter.file)}) attempt=${attempt}`);

  const currentUrl = page.url() || '';
  if (!/\/main\/writer\/(chapter-manage\/|\d+\/publish\/|book-manage)/i.test(currentUrl)) {
    await page.goto(chapterManageURL(), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1500);
  }

  const loginCheck = await ensureLoggedIn(page, {
    qrPath,
    logger: console,
    saveStorageState: async () => {
      await context.storageState({ path: statePath });
      console.log(`已刷新登录态: ${statePath}`);
    },
  });
  if (!loginCheck.loggedIn) {
    return {
      chapter,
      ok: false,
      reason: loginCheck.qrCapture?.path
        ? `等待扫码登录超时。二维码截图: ${loginCheck.qrCapture.path}`
        : '等待扫码登录超时。',
    };
  }

  let fillResult;
  try {
    fillResult = await fillDraft(page, chapter, shotsDir, prefix, args);
  } catch (err) {
    return { chapter, ok: false, reason: err.message || String(err) };
  }

  if (fillResult?.mode === 'debug-volume-stop') {
    return { chapter, mode: 'debug-volume-stop', ok: true, volumeResult: fillResult.volumeResult };
  }

  // Default: save as draft. Use --confirm-publish to actually publish.
  const isDraftOnly = !args['confirm-publish'];
  if (args['dry-run'] || args['fill-only'] || isDraftOnly) {
    return { chapter, mode: 'draft-only', ok: true, volumeResult: fillResult?.volumeResult };
  }

  const modalResult = await goToFinalPublishModal(page, chapter, shotsDir, prefix);
  if (!modalResult.ok) return { chapter, ok: false, reason: modalResult.reason };

  if (args['to-final-modal']) {
    return { chapter, mode: 'to-final-modal', ok: true, volumeResult: fillResult?.volumeResult };
  }

  if (mode === 'scheduled') {
    if (!scheduleInfo) {
      return { chapter, ok: false, reason: 'scheduled 模式需要 --schedule-at，例如 2026-03-13 21:00' };
    }
    const switchBtn = modalResult.publishModal.locator('button[role="switch"]').first();
    if (await switchBtn.count()) {
      const checked = ((await switchBtn.getAttribute('class')) || '').includes('checked');
      if (!checked) {
        await switchBtn.click();
        await page.waitForTimeout(800);
      }
    }
    const dateInput = modalResult.publishModal.locator('input[placeholder="请选择日期"]').first();
    const timeInput = modalResult.publishModal.locator('input[placeholder="请选择时间"]').first();
    if (!await dateInput.count() || !await timeInput.count()) {
      return { chapter, ok: false, reason: '未找到定时发布的日期/时间控件。' };
    }
    await dateInput.fill(scheduleInfo.date);
    await dateInput.press('Enter').catch(() => {});
    await page.waitForTimeout(300);
    await timeInput.fill(scheduleInfo.time);
    await timeInput.press('Enter').catch(() => {});
    await page.waitForTimeout(600);
    await page.screenshot({ path: path.join(shotsDir, `${prefix}-06-scheduled-filled.png`), fullPage: true });
  } else if (mode !== 'immediate') {
    return { chapter, ok: false, reason: '当前版本只开放 immediate / scheduled。' };
  }

  const confirmPublishBtn = modalResult.publishModal.locator('button').filter({ hasText: '确认发布' }).first();
  if (!await confirmPublishBtn.count()) {
    return { chapter, ok: false, reason: '未找到“确认发布”按钮。' };
  }

  await page.screenshot({ path: path.join(shotsDir, `${prefix}-06-before-confirm-publish.png`), fullPage: true });
  await confirmPublishBtn.click().catch(async () => confirmPublishBtn.click({ force: true }));
  await page.waitForTimeout(2500);
  const stillOnPublishModal = await page.locator('.arco-modal.publish-confirm-container-new').last().count();
  const postConfirmMessages = await collectVisibleMessages(page).catch(() => []);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(shotsDir, `${prefix}-06-after-confirm-publish.png`), fullPage: true });

  if (stillOnPublishModal) {
    return {
      chapter,
      ok: false,
      verify: { found: false },
      scheduleInfo,
      volumeResult: fillResult?.volumeResult,
      reason: '点击“确认发布”后发布设置弹窗仍未关闭；通常表示必填项未完成（例如“是否使用AI”未正确选中）或页面未真正提交。',
      postConfirmMessages,
    };
  }

  const publishLimitReason = detectPublishLimit(postConfirmMessages);
  if (publishLimitReason) {
    return {
      chapter,
      ok: false,
      verify: { found: false },
      scheduleInfo,
      volumeResult: fillResult?.volumeResult,
      reason: `触发单日字数上限：${publishLimitReason}`,
      postConfirmMessages,
    };
  }

  const verify = await verifyPublished(page, chapter, shotsDir, prefix);
  if (verify.found) {
    markPublished(stateFile, chapter, verify, mode);
  }
  return {
    chapter,
    ok: !!verify.found,
    verify,
    scheduleInfo,
    volumeResult: fillResult?.volumeResult,
    reason: verify.found ? null : '章节管理页未找到目标章节',
    postConfirmMessages,
  };
}

async function publishOne(page, context, chapter, args, shotsDir, stateFile, statePath, qrPath, index) {
  const first = await publishOneOnce(page, context, chapter, args, shotsDir, stateFile, statePath, qrPath, index, 1);
  if (first.ok || !isRetryableFailure(first)) return first;

  console.log(`检测到可恢复失败，准备重试一次: ${chapter.title} :: ${first.reason || 'unknown'}`);
  try {
    await page.goto(chapterManageURL(), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
  } catch {}

  const second = await publishOneOnce(page, context, chapter, args, shotsDir, stateFile, statePath, qrPath, index, 2);
  second.retried = true;
  second.firstFailureReason = first.reason || null;
  return second;
}

async function main() {
  const args = parseArgs(process.argv);
  // Default: save as draft for safety. Use --confirm-publish to actually publish.
  const isPublish = args['confirm-publish'];
  const mode = isPublish ? (args.mode || 'immediate') : 'draft-only';
  if (isPublish && args.mode) { /* explicit mode */ }
  else if (!isPublish) args['draft-only'] = true;
  if (args['book-id']) BOOK_ID = args['book-id'];
  if (args['book-name']) BOOK_NAME = args['book-name'];
  const skillRoot = path.resolve(__dirname, '..');
  const statePath = path.join(skillRoot, 'state', 'fanqie-storage-state.json');
  const stateFile = path.join(skillRoot, 'state', 'publish-state.json');
  const shotsDir = path.join(skillRoot, 'state', 'screenshots');
  const qrPath = path.join(skillRoot, 'state', 'login-qr.png');
  ensureDir(shotsDir);

  let playwright;
  try {
    playwright = require('playwright');
  } catch {
    console.error('Missing dependency: playwright');
    console.error('Install with: npm i -D playwright');
    process.exit(1);
  }
  if (!fs.existsSync(statePath)) {
    console.error('缺少登录态。请先运行: node skills/fanqie-publisher/scripts/login_fanqie.js --cdp http://127.0.0.1:9222');
    process.exit(1);
  }

  const loaded = loadChapters(args);
  let chapters = filterChapters(loaded, args);
  if (!chapters.length) {
    console.error('No chapters found to publish');
    process.exit(1);
  }

  if (args['draft-only'] || !args['confirm-publish']) {
    // 草稿模式不受每日字数限制
  } else {
    chapters = applyDailyLimitGuard(chapters, { ...args, mode });
  }
  if (!chapters.length) {
    console.log(`按照每日字数保护阈值停止：当前 mode=${mode}，没有可安全继续发布的章节。可用 --already-published-chars / --daily-limit-chars 调整。`);
    return;
  }

  if (args['skip-published']) {
    const state = loadPublishState(stateFile);
    chapters = chapters.filter((c) => !isPublishedInState(state, c.file));
  }
  if (!chapters.length) {
    console.log('待处理章节为空。');
    return;
  }

  const { browser, context } = await connectBrowser(args, statePath, playwright);
  const { page, reusedExistingPage } = await resolvePage(context, {
    preferredUrlPatterns: [
      draftURL(),
      chapterManageURL(),
      /https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\/chapter-manage\//i,
      /https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\/\d+\/publish\//i,
      /https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\/book-manage/i,
      /https?:\/\/(?:www\.)?fanqienovel\.com\/main\/writer\//i,
      /https?:\/\/(?:www\.)?fanqienovel\.com\//i,
    ],
    collapseFanqieWriterTabs: true,
  });
  console.log(`发布页选择完成: reused=${reusedExistingPage} url=${page.url() || 'about:blank'}`);

  const results = [];
  for (let i = 0; i < chapters.length; i++) {
    const chapter = chapters[i];
    const result = await publishOne(page, context, chapter, { ...args, mode }, shotsDir, stateFile, statePath, qrPath, i);
    results.push(result);
    console.log(JSON.stringify(result, null, 2));

    if (!result.ok) {
      console.log(`停止批量流程，卡在: ${chapter.title}`);
      break;
    }
    if (i < chapters.length - 1) {
      await page.waitForTimeout(2000);
    }
  }

  await browser.close().catch(() => {});

  const successCount = results.filter((r) => r.ok && r.verify?.found).length;
  const final = {
    requested: chapters.length,
    processed: results.length,
    publishedVerified: successCount,
    mode,
    volume: args.volume || null,
    dailyLimitChars: Number(args['daily-limit-chars'] || DEFAULT_DAILY_LIMIT_CHARS),
    alreadyPublishedChars: Number(args['already-published-chars'] || 0),
    results: results.map((r) => ({
      title: r.chapter.title,
      ok: r.ok,
      reason: r.reason || null,
      status: r.verify?.status || null,
      publishTime: r.verify?.publishTime || null,
      selectedVolume: r.volumeResult?.selected || null,
      alreadyMatchedVolume: !!r.volumeResult?.alreadyMatched,
    })),
  };
  console.log('BATCH_SUMMARY');
  console.log(JSON.stringify(final, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
