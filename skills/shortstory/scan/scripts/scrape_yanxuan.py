#!/usr/bin/env python3
"""
知乎盐选榜单采集脚本。

使用 Playwright 浏览器工具采集盐选热门榜单数据。
由 agent 调用，不独立运行。

用法（在 SKILL.md 流程中集成）:
  1. browser_navigate "https://www.zhihu.com/yanxuan/"
  2. browser_snapshot → 提取榜单列表
  3. 逐个 browser_navigate 进入详情页
  4. 提取：标题、作者、题材标签、开头200字

注意：知乎页面 SSR + 动态加载，browser_wait_for 等待核心内容出现。
"""
import json
import sys


def parse_list_page(snapshot_text):
    """从 browser_snapshot 文本中解析榜单条目。
    由 agent 在收到 snapshot 后调用此函数提取结构化数据。"""
    items = []
    lines = snapshot_text.split('\n')
    current = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 提取标题（通常带链接）
        if line.startswith('http') or 'zhihu.com' in line:
            if current.get('title'):
                items.append(current)
                current = {}
            current['url'] = line
        elif current.get('title') is None and len(line) > 5 and len(line) < 80:
            current['title'] = line
        elif '标签' in line or '分类' in line:
            current['tags'] = line
        elif '点赞' in line or '热度' in line:
            current['heat'] = line
    if current.get('title'):
        items.append(current)
    return items


def extract_opening(text, max_chars=200):
    """提取正文开头 200 字。"""
    # 跳过标题行
    lines = text.split('\n')
    content_lines = [l for l in lines if l.strip() and not l.startswith('#')]
    content = '\n'.join(content_lines)
    return content[:max_chars]


if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
        items = parse_list_page(text)
        print(json.dumps(items, ensure_ascii=False, indent=2))
