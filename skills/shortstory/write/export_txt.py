#!/usr/bin/env python3
"""
从 正文.md 导出纯文本版本 正文.txt。

用法: python export_txt.py <项目目录>

处理规则：
- 剥离 ## / # 标题标记（保留标题文字）
- 剥离 ** * 加粗/斜体（保留文字）
- 剥离 [text](url) 链接 → 只保留 text
- 剥离 > 引用块标记
- 剥离 ` 代码标记（保留行内代码的文字）
- 剥离 --- *** ___ 分隔线
- 保留：「」"" …… —— 段落空行 所有标点
- 连续空行压缩为单空行
"""
import io, re, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def strip_md(text):
    # 1. 图片/链接: ![alt](url) → alt, [text](url) → text
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # 2. 加粗/斜体: **text** 或 *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)

    # 3. 行内代码: `text`
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # 4. 引用块: 移除行首 >
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)

    # 5. 标题标记: 移除行首的 ##... 或 #... 但保留标题文字
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # 6. 分隔线: 移除纯 --- *** ___ 行
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 7. 连续空行压缩为最多一个空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 8. 首尾空白
    text = text.strip()

    # 9. 每段首行缩进两个全角空格（中文正文排版规范）
    # 分段规则：连续空行或行首无缩进标记的分段
    paragraphs = re.split(r'\n\n+', text)
    indented = []
    for para in paragraphs:
        para = para.strip()
        if para:
            indented.append('\u3000\u3000' + para)
        else:
            indented.append('')
    text = '\n\n'.join(indented)

    return text


def main():
    if len(sys.argv) < 2:
        print("用法: python export_txt.py <项目目录>")
        sys.exit(1)

    proj = Path(sys.argv[1])
    body_file = proj / '正文.md'
    txt_file = proj / '正文.txt'

    if not body_file.exists():
        print(f"  [SKIP] 未找到 {body_file}")
        return

    body = body_file.read_text('utf-8')
    stripped = strip_md(body)
    txt_file.write_text(stripped, 'utf-8')

    md_len = len(body)
    txt_len = len(stripped)
    print(f"  正文.md  ({md_len}字) → 正文.txt ({txt_len}字, 剥离{md_len - txt_len}字符)")
    print(f"  输出: {txt_file}")


if __name__ == '__main__':
    main()
