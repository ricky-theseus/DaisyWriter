"""
短篇正文机械检查。
用法：python <skill_dir>/check.py <正文.md路径>
检查项：场景字数(400-800)、段落句数(≤2)、禁用词、过渡词超限、角括号、标记文字。
只读不改，退出码 0=通过 1=不通过。
"""
import re, sys, os

def check(path):
    text = open(path, encoding="utf-8").read()
    errors = []

    # 1. 禁用词
    banned = ["然而","值得一提","由此可见","事实上","不难看出","综上所述","与此同时","不可否认"]
    for w in banned:
        if w in text:
            errors.append(f"禁用词：{w}")

    # 2. 过渡词超限
    trans = ["日子一天天过去","时间过得很快","不知不觉","转眼间","就这样","没过多久"]
    count_t = sum(text.count(t) for t in trans)
    if count_t > 3:
        errors.append(f"过渡词超限：{count_t}处")

    # 3. 角括号
    if "<" in text or ">" in text:
        errors.append("正文含角括号 < 或 >")

    # 4. 标记文字
    markers = ["[试读","[钩子","[卡点]","[场景]","[正文开始]","[正文结束]"]
    for m in markers:
        if m in text:
            errors.append(f"正文含标记文字：{m}")

    # 5. 场景字数 & 段落句数
    scenes = re.split(r'\n(?=\d+\n)', text)
    for raw in scenes:
        m = re.match(r'(\d+)', raw.strip())
        if not m:
            continue
        num = int(m.group(1))
        body = raw[m.end():].strip()
        cn = len(re.sub(r'[\s【】""《》「」,，。．！？；：、…—\-A-Za-z0-9]', '', body))
        if cn < 400:
            errors.append(f"场景{num}不足400字：{cn}")
        elif cn > 800:
            errors.append(f"场景{num}超过800字：{cn}")

        paras = body.split('\n\n')
        for pi, p in enumerate(paras):
            p = p.strip()
            if p and not re.match(r'^\d+$', p) and p.count('。') > 2:
                errors.append(f"场景{num}段落{pi+1}超2句：{p[:50]}")

    return errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python check.py <正文.md路径>")
        sys.exit(1)
    errs = check(sys.argv[1])
    if errs:
        print("检查未通过：")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("检查通过 ✓")
