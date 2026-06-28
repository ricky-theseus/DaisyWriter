const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const DASHSCOPE_ENDPOINT = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';
const WAN_MODEL = 'wan2.6-t2i';

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

async function callWan(prompt) {
  const apiKey = loadApiKey();
  const resp = await fetch(DASHSCOPE_ENDPOINT, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: WAN_MODEL,
      input: { messages: [{ role: 'user', content: [{ text: prompt }] }] },
      parameters: { prompt_extend: true, watermark: false, n: 1, size: '1024*768' },
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

async function main() {
  const apiKey = loadApiKey();
  if (!apiKey) { console.error('未配置 DASHSCOPE_API_KEY'); process.exit(1); }

  const outDir = path.resolve(__dirname, '..', '..', '..', '博文');

  // === C++ STL 系列封面 ===
  const stlPrompt = `Generate a vertical book cover for a technical blog series "C++ STL 详解".
Title: C++ STL 详解
Subtitle: Standard Template Library

Style requirements:
- Dark blue / deep tech background with subtle circuit board or data stream patterns
- C++ logo or code brackets "<>" as a central visual element, glowing in cyan/blue neon
- Abstract data structure diagrams (linked nodes, arrays, tree structures) floating in background
- Clean, minimalist tech aesthetic — no people, no characters
- Text must be clearly readable: title in large bold font, white/cyan color
- 800×600 landscape composition, PNG format, high contrast professional look`;

  console.log('生成 C++ STL 系列封面...');
  const raw1 = await callWan(stlPrompt);
  const img1 = await sharp(raw1).resize(800, 600, { fit: 'cover', position: 'centre' }).png().toBuffer();
  const stlPath = path.join(outDir, 'C++', 'STL', 'cover.png');
  fs.writeFileSync(stlPath, img1);
  console.log(`  → 博文/C++/STL/cover.png (${(img1.length / 1024).toFixed(0)}KB)`);

  // === AI Agent 系列封面 ===
  const agentPrompt = `Generate a vertical cover image for a technical blog series "AI Agent 实战系列".
Title: AI Agent 实战
Subtitle: 多智能体系统从入门到精通

Style requirements:
- Futuristic tech background in deep space blue / purple gradient
- Abstract neural network or agent communication nodes connected by glowing lines
- Subtle robot silhouette or AI brain icon as central element, glowing in gold/teal neon
- Floating geometric shapes suggesting AI agents collaborating
- Clean, minimalist sci-fi aesthetic — no people, no characters
- Text must be clearly readable: title in large bold font, white/gold color
- 800×600 landscape composition, PNG format, premium tech feel`;

  console.log('生成 AI Agent 系列封面...');
  const raw2 = await callWan(agentPrompt);
  const img2 = await sharp(raw2).resize(800, 600, { fit: 'cover', position: 'centre' }).png().toBuffer();
  const agentPath = path.join(outDir, 'AI', 'Agent', 'cover.png');
  fs.writeFileSync(agentPath, img2);
  console.log(`  → 博文/AI/Agent/cover.png (${(img2.length / 1024).toFixed(0)}KB)`);

  // === 数据结构与算法 系列封面 ===
  const dsPrompt = `Generate a landscape cover image for a technical blog series "数据结构与算法".
Title: 数据结构与算法
Subtitle: 面试必备

Style requirements:
- Deep dark background with subtle binary code / matrix data stream patterns
- Central visual: abstract data structure diagrams (linked list nodes, binary tree, array blocks) connected by glowing cyan lines
- Floating element: a glowing brain silhouette or gear icon suggesting algorithmic thinking
- Clean, minimalist tech aesthetic — no people, no characters
- Text must be clearly readable: Chinese title in large bold white/gold font
- 800×600 landscape composition, PNG format, high contrast professional look`;

  console.log('生成数据结构与算法系列封面...');
  const raw3 = await callWan(dsPrompt);
  const img3 = await sharp(raw3).resize(800, 600, { fit: 'cover', position: 'centre' }).png().toBuffer();
  const dsPath = path.join(outDir, '数据结构与算法', 'cover.png');
  fs.writeFileSync(dsPath, img3);
  console.log(`  → 博文/数据结构与算法/cover.png (${(img3.length / 1024).toFixed(0)}KB)`);

  // === C++ 后端面试八股文 系列封面 ===
  const baguePrompt = `Generate a landscape cover image for a technical blog series "C++ 后端面试八股文".
Title: C++ 后端面试八股文
Subtitle: 不背八股，理解八股

Style requirements:
- Dark navy blue background with subtle matrix code / binary data stream patterns
- Central visual: C++ code brackets "<>" with a glowing brain or lightbulb icon suggesting deep understanding
- Floating elements: key C++ keywords (const, virtual, auto, thread, template) in faint glowing text
- Clean, minimalist tech aesthetic — no people, no characters
- Text must be clearly readable: title in large bold white/gold font
- 800×600 landscape composition, PNG format, high contrast professional look`;

  console.log('生成 C++ 后端八股文系列封面...');
  const raw4 = await callWan(baguePrompt);
  const img4 = await sharp(raw4).resize(800, 600, { fit: 'cover', position: 'centre' }).png().toBuffer();
  const baguePath = path.join(outDir, 'C++', '后端八股文', 'cover.png');
  fs.writeFileSync(baguePath, img4);
  console.log(`  → 博文/C++/后端八股文/cover.png (${(img4.length / 1024).toFixed(0)}KB)`);

  console.log('\n完成: 四张封面已生成');
}

main().catch(e => { console.error(e); process.exit(1); });
