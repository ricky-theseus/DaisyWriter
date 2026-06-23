#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

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
  const args = parseArgs(process.argv);
  const cdp = args.cdp || 'http://127.0.0.1:9222';
  const childScript = path.resolve(__dirname, 'login_fanqie.js');
  const child = spawn(process.execPath, [childScript, '--cdp', cdp], {
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let stdout = '';
  let stderr = '';
  let mediaBlock = '';
  let inMediaBlock = false;
  let qrReady = null;
  let loginOk = false;
  let loginAlreadyOk = false;
  let loginTimeout = false;

  function handleLine(line, isErr = false) {
    const text = line.trimEnd();
    if (!text) return;

    if (text === '---OPENCLAW_MEDIA_REPLY_START---') {
      inMediaBlock = true;
      mediaBlock = '';
      return;
    }
    if (text === '---OPENCLAW_MEDIA_REPLY_END---') {
      inMediaBlock = false;
      return;
    }
    if (inMediaBlock) {
      mediaBlock += `${text}\n`;
      return;
    }

    if (text.startsWith('QR_READY:')) qrReady = text.slice('QR_READY:'.length);
    if (text === 'LOGIN_OK') loginOk = true;
    if (text === 'LOGIN_ALREADY_OK') loginAlreadyOk = true;
    if (text === 'LOGIN_TIMEOUT') loginTimeout = true;

    if (isErr) stderr += `${text}\n`;
    else stdout += `${text}\n`;
  }

  child.stdout.on('data', (buf) => {
    const chunk = buf.toString('utf8');
    chunk.split(/\r?\n/).forEach((line) => handleLine(line, false));
  });
  child.stderr.on('data', (buf) => {
    const chunk = buf.toString('utf8');
    chunk.split(/\r?\n/).forEach((line) => handleLine(line, true));
  });

  const code = await new Promise((resolve) => child.on('close', resolve));

  const summary = {
    ok: code === 0,
    code,
    qrReady,
    loginOk,
    loginAlreadyOk,
    loginTimeout,
    mediaReply: mediaBlock.trim(),
    stdout: stdout.trim(),
    stderr: stderr.trim(),
  };

  console.log(JSON.stringify(summary, null, 2));
  if (code !== 0) process.exit(code);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
