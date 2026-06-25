const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const DASHSCOPE_ENDPOINT = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';
const WAN_MODEL = 'wan2.6-t2i';
const GEN_SIZE = '768*1024';

function loadApiKey() {
  const paths = [
    path.join(__dirname, '..', '..', '..', '.env'),
    path.join(__dirname, '.env'),
  ];
  for (const p of paths) {
    if (fs.existsSync(p)) {
      const m = fs.readFileSync(p, 'utf-8').match(/^DASHSCOPE_API_KEY=(.+)$/m);
      if (m) return m[1].trim();
    }
  }
  return process.env.DASHSCOPE_API_KEY || null;
}

function readMeta(projPath) {
  const meta = { title: '', author: '里克修斯', summary: '', candidates: [] };
  const folder = path.basename(projPath);

  const infoDir = path.join(projPath, '作品信息');
  const info = fs.existsSync(path.join(infoDir, '作品信息.md'))
    ? path.join(infoDir, '作品信息.md')
    : path.join(projPath, '作品信息.md');
  if (fs.existsSync(info)) {
    const text = fs.readFileSync(info, 'utf-8');
    const t = text.match(/作品名称[^：:]*[：:]\s*(.+)/);
    if (t) meta.title = t[1].replace(/[*《》]/g, '').replace(/[（(].*[）)]/, '').trim();
    const a = text.match(/笔名[：:]\s*(.+)/);
    if (a) meta.author = a[1].trim();
    let d = text.match(/(?:故事|作品)简介[^：:]*[：:]\s*(.+)/);
    if (!d) d = text.match(/(?:故事|作品)简介[^：:]*[：:]\s*\n\s*(.+)/);
    if (d) meta.summary = d[1].trim();
    const ct = text.match(/候选书名[^：:]*[：:]\s*([\s\S]+?)(?=\n#|\n##|\*\*|$)/);
    if (ct) {
      meta.candidates = ct[1]
        .split('\n')
        .map(l => l.replace(/^\d+[.、]\s*/, '').trim())
        .filter(l => l.length > 0 && l.length <= 15 && !l.startsWith('*') && !l.startsWith('**'));
    }
  }

  if (!meta.summary) {
    let outline = path.join(projPath, '大纲/总纲.md');
    if (!fs.existsSync(outline)) outline = path.join(projPath, '总纲.md');
    if (fs.existsSync(outline)) {
      const text = fs.readFileSync(outline, 'utf-8');
      let s = text.match(/故事一句话[：:]\s*(.+)/);
      if (!s) s = text.match(/##?\s*故事一句话\s*\n\s*(.+)/);
      if (s) meta.summary = s[1].trim();
    }
  }

  if (!meta.title) meta.title = folder;
  if (meta.candidates.length === 0) meta.candidates = [meta.title];
  return meta;
}

async function callWan(prompt) {
  const apiKey = loadApiKey();
  const resp = await fetch(DASHSCOPE_ENDPOINT, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: WAN_MODEL,
      input: { messages: [{ role: 'user', content: [{ text: prompt }] }] },
      parameters: { prompt_extend: true, watermark: false, n: 1, size: GEN_SIZE },
    }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${resp.status}: ${text}`);
  }
  const data = await resp.json();
  for (const c of (data.output?.choices?.[0]?.message?.content || [])) {
    if (c.image) {
      const img = await fetch(c.image);
      return Buffer.from(await img.arrayBuffer());
    }
  }
  throw new Error('API 返回无图片: ' + JSON.stringify(data).slice(0, 200));
}

function slugify(s) {
  return s.replace(/[《》\s\/\\?%*:|"<>]/g, '').slice(0, 30);
}

function parseArgs() {
  const args = { path: null, singleTitle: null };
  for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i] === '--title') {
      args.singleTitle = process.argv[++i];
    } else if (!args.path) {
      args.path = process.argv[i];
    }
  }
  return args;
}

async function makeCover(title, meta, candidateStr, absPath) {
  const outDir = path.join(absPath, '作品信息');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const byline = `${meta.author}　〇　著`;
  const prompt = `请为我的小说生成一个网文封面。
小说标题：《${title}》
作者：${meta.author}
${meta.summary ? '故事简介：' + meta.summary + '\n' : ''}
候选书名：
${candidateStr}

要求：
1. 封面中清晰显示作品名称和作者笔名，笔名格式为"${byline}"
2. 画面元素符合小说题材和风格
3. 封面设计美观有艺术感
4. 尺寸 600×800 像素，格式 jpg 或 png，文件大小不超过 5MB`;

  console.log(`生成《${title}》封面...`);
  const raw = await callWan(prompt);
  const resized = await sharp(raw).resize(600, 800, { fit: 'cover', position: 'centre' }).png().toBuffer();

  const isPrimary = title === meta.title;
  const filename = isPrimary ? 'cover.png' : `cover-${slugify(title)}.png`;
  const output = path.join(outDir, filename);
  fs.writeFileSync(output, resized);
  console.log(`  → 作品信息/${filename} (${(resized.length / 1024).toFixed(0)}KB)`);
}

async function main() {
  const args = parseArgs();
  if (!args.path) { console.error('用法: node generate_cover.js <项目路径> [--title "书名"]'); process.exit(1); }
  const absPath = path.resolve(args.path);
  if (!fs.existsSync(absPath)) { console.error(`项目不存在: ${absPath}`); process.exit(1); }
  if (!loadApiKey()) { console.error('未配置 DASHSCOPE_API_KEY'); process.exit(1); }

  const meta = readMeta(absPath);
  const candidates = meta.candidates;
  const candidateStr = candidates.map((c, i) => `${i + 1}. 《${c}》`).join('\n');

  if (args.singleTitle) {
    // 单独生成一个书名
    await makeCover(args.singleTitle, meta, candidateStr, absPath);
  } else {
    // 批量生成所有候选书名
    console.log(`候选书名 (${candidates.length}个):`);
    candidates.forEach(c => console.log(`  - ${c}`));
    for (const title of candidates) {
      await makeCover(title, meta, candidateStr, absPath);
    }
    console.log(`\n完成: 共生成 ${candidates.length} 张封面`);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
