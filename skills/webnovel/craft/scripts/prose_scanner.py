#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行文约束集量化扫描脚本。
输入：章节正文文件路径
输出：JSON 报告（句式计数 + 词库扫描 + 段落统计）
审查流程中先跑此脚本，输出的量化数据作为 reviewer 的输入。
"""

import re
import json
import sys
from pathlib import Path


# ============================================================
# 一、句式正则
# ============================================================

# 1.1 "不是...是..." 否定前置式（含破折号变体 "不是...——是..."）
RE_NOT_BUT = re.compile(r"不是.{0,20}(?:，|——|是)")
# 1.2 身体部位自主拟人：部位 + 自己 + 动词
RE_BODY_AUTO = re.compile(
    r"(?:手|脚|眼|肩|腿|嘴|身体|指|膝盖|背|脖子|脊椎|锁骨|无名指|小指|无名印记|脉搏|心跳)"
    r".{0,6}(?:自己|自主|比意识先|先于|不等.{0,2}就|替.{0,2})"
)
# 1.3 哲理收束句：段末以"不是X。是Y。"或"X不是Y。X是Z。"结构收尾
RE_PHILO_END = re.compile(r"[。.]\s*$")


# ============================================================
# 二、禁止词库
# ============================================================

# 心理标签词
EMOTION_LABELS = [
    "心里想", "心中涌起", "一阵悲伤", "一阵感动", "感到一阵",
    "心里一阵", "心中一阵", "涌起一股", "泛起一阵",
]

# 情绪副词
EMOTION_ADVERBS = [
    "轻轻地说", "痛苦地闭", "温柔地看", "难过地走", "愤怒地",
    "悲伤地", "绝望地", "欣慰地", "感动地", "无奈地",
    "深深地", "狠狠地", "用力地", "温柔地",
]

# 直述情绪词（需要上下文判断，这里只做粗筛）
DIRECT_EMOTION = [
    "他很痛苦", "她很难过", "他不舍", "她感动",
    "他心疼", "她心疼", "他绝望", "她绝望",
]


# ============================================================
# 三、段落统计
# ============================================================

def count_sentences(paragraph: str) -> int:
    """粗略计句：按中文句号/问号/感叹号/省略号分割"""
    return len(re.findall(r"[。？！…]{1,2}", paragraph))


def is_single_sentence(paragraph: str) -> bool:
    return count_sentences(paragraph) == 1


# ============================================================
# 四、感官统计
# ============================================================

TOUCH_WORDS = ["凉", "冷", "温", "热", "烫", "触", "摸", "硌", "压", "贴", "按", "抵", "刺", "麻", "痒", "僵", "软", "硬"]
HEAR_WORDS = ["听", "声", "响", "铃", "静", "嗡", "闷", "脆", "钝", "余音"]
SIGHT_WORDS = ["光", "色", "亮", "暗", "影", "轮廓", "金", "银", "灰", "白", "黑", "黄", "蓝", "红"]


def sensory_stats(text: str) -> dict:
    """统计三类感官词出现次数"""
    return {
        "touch": sum(text.count(w) for w in TOUCH_WORDS),
        "hear": sum(text.count(w) for w in HEAR_WORDS),
        "sight": sum(text.count(w) for w in SIGHT_WORDS),
    }


# ============================================================
# 五、主扫描函数
# ============================================================

def scan_chapter(filepath: str) -> dict:
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    text = path.read_text(encoding="utf-8")

    # 去除 markdown 标题
    lines = [l for l in text.splitlines() if not l.strip().startswith("#")]

    # 按空行拆分段落
    paragraphs = []
    current = []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                paragraphs.append("".join(current))
                current = []
    if current:
        paragraphs.append("".join(current))

    # ---- 句式计数 ----
    not_but_count = len(RE_NOT_BUT.findall(text))
    body_auto_count = len(RE_BODY_AUTO.findall(text))

    # 哲理收束：段末句是否具有"不是X。是Y。"结构
    philo_count = 0
    for p in paragraphs:
        sentences = re.split(r"[。！？…]{1,2}", p)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 2:
            last_two = "。".join(sentences[-2:])
            if re.search(r"不是.{0,30}(?:是|而是)", last_two):
                philo_count += 1

    # ---- 词库扫描 ----
    emotion_label_hits = []
    for w in EMOTION_LABELS:
        count = text.count(w)
        if count > 0:
            emotion_label_hits.append({"word": w, "count": count})

    emotion_adverb_hits = []
    for w in EMOTION_ADVERBS:
        count = text.count(w)
        if count > 0:
            emotion_adverb_hits.append({"word": w, "count": count})

    direct_emotion_hits = []
    for w in DIRECT_EMOTION:
        count = text.count(w)
        if count > 0:
            direct_emotion_hits.append({"word": w, "count": count})

    # ---- 句长统计 ----
    sentences_raw = re.split(r"[。！？…]{1,2}", text)
    sentences_raw = [s.strip() for s in sentences_raw if s.strip() and not s.strip().startswith("#")]
    sentence_lens = [len(s) for s in sentences_raw]
    very_short = sum(1 for l in sentence_lens if l <= 8)
    short = sum(1 for l in sentence_lens if 9 <= l <= 15)
    medium = sum(1 for l in sentence_lens if 16 <= l <= 30)
    long = sum(1 for l in sentence_lens if l > 30)
    total_sentences = len(sentence_lens)
    avg_sentence_len = sum(sentence_lens) / max(total_sentences, 1)

    # 连续极短句检测
    consecutive_short_runs = []
    run = 0
    for l in sentence_lens:
        if l <= 8:
            run += 1
        else:
            if run >= 3:
                consecutive_short_runs.append(run)
            run = 0
    if run >= 3:
        consecutive_short_runs.append(run)
    max_consecutive_short = max(consecutive_short_runs) if consecutive_short_runs else 0

    # ---- 段落统计 ----
    para_sentence_counts = [count_sentences(p) for p in paragraphs]
    single_sentence_paras = sum(1 for c in para_sentence_counts if c == 1)
    long_paras = sum(1 for c in para_sentence_counts if c > 7)
    avg_para_len = sum(para_sentence_counts) / max(len(para_sentence_counts), 1)

    # ---- 感官统计 ----
    sensory = sensory_stats(text)

    # ---- 情绪温度标记 ----
    # 简单规则：搜"凉""温""烫""热"在印记/身体相关上下文中的出现
    mark_cool = len(re.findall(r"印记.{0,20}(?:凉|冷)", text))
    mark_warm = len(re.findall(r"印记.{0,20}(?:温|热|烫)", text))

    # ---- 安静时刻检测 ----
    # 规则：段落中无事件动词（说/走/拿/放/推/拉/进/出），仅有描写词
    quiet_count = 0
    event_verbs = ["说", "走", "拿", "放", "推", "拉", "进", "出", "站", "坐", "给", "问", "答"]
    for p in paragraphs:
        if len(p) > 20 and not any(v in p for v in event_verbs):
            quiet_count += 1

    # ---- 主角主动性检测 ----
    active_verbs = ["推", "拉", "走", "跑", "抓", "握", "站起", "蹲下", "跟踪", "数", "画", "写", "咬", "按", "拿出", "收起"]
    passive_verbs = ["看", "听", "感觉", "感受", "察觉", "注意", "发现", "等", "待", "观望", "蹲着", "趴着"]
    dialogue_markers = ["说", "问", "答", "道", "叫", "喊"]
    protag_active = sum(text.count(v) for v in active_verbs)
    protag_passive = sum(text.count(v) for v in passive_verbs)

    # ---- 开篇冲突检测 ----
    opening_text = text[:300]
    opening_slow = not (any(m in opening_text for m in dialogue_markers) or any(v in opening_text for v in active_verbs))

    # ---- 重复体感词密度 ----
    repeat_body_words = ["凉", "冷", "印记", "胸口", "膝盖", "脚尖", "指尖", "发麻", "发抖", "酸痛", "僵"]
    repeat_body_hits = {w: text.count(w) for w in repeat_body_words if text.count(w) >= 8}

    # ---- 静态段落占比 ----
    # 段落既无对白也无动作动词 → 静态段
    dialogue_markers = ["说", "问", "答", "道", "叫", "喊"]
    static_paras = 0
    for p in paragraphs:
        has_dialogue = any(m in p for m in dialogue_markers)
        has_action = any(v in p for v in active_verbs)
        if not has_dialogue and not has_action and len(p) > 15:
            static_paras += 1

    # ---- 情绪单调检测 ----
    # 全章无温度波动（仅有凉或仅有温/烫）→ 情绪单调
    has_cool = mark_cool > 0 or any(w in text for w in ["凉", "冷", "寒意", "冰凉"])
    has_warm = mark_warm > 0 or any(w in text for w in ["温", "热", "烫", "暖", "火"])
    emotional_flat = not (has_cool and has_warm)

    # ---- 动作间隔检测 ----
    # 统计连续无动作段落的平均长度（字符数）
    no_action_runs = []
    current_run = 0
    for p in paragraphs:
        has_action = any(v in p for v in active_verbs) or any(v in p for v in passive_verbs)
        if not has_action and len(p) > 10:
            current_run += len(p)
        else:
            if current_run > 0:
                no_action_runs.append(current_run)
            current_run = 0
    if current_run > 0:
        no_action_runs.append(current_run)
    max_no_action_gap = max(no_action_runs) if no_action_runs else 0

    # ---- 判定 ----
    issues = []
    if not_but_count > 3:
        issues.append({"check": "不是A是B", "value": not_but_count, "limit": 3, "severity": "blocking"})
    if body_auto_count > 4:
        issues.append({"check": "身体自主拟人", "value": body_auto_count, "limit": 4, "severity": "blocking"})
    if philo_count > 2:
        issues.append({"check": "哲理收束", "value": philo_count, "limit": 2, "severity": "blocking"})
    if emotion_label_hits:
        issues.append({"check": "情绪标签词", "hits": emotion_label_hits, "severity": "blocking"})
    if emotion_adverb_hits:
        issues.append({"check": "情绪副词", "hits": emotion_adverb_hits, "severity": "blocking"})
    if single_sentence_paras == 0:
        issues.append({"check": "单句成段", "value": 0, "limit": "≥1", "severity": "warning"})
    if quiet_count == 0:
        issues.append({"check": "安静时刻", "value": 0, "limit": "≥1", "severity": "warning"})
    if sensory.get("sight", 0) > sensory.get("touch", 0) * 2:
        issues.append({"check": "感官视觉偏重", "touch": sensory["touch"], "sight": sensory["sight"], "severity": "warning"})
    if very_short / max(total_sentences, 1) > 0.15:
        issues.append({"check": "极短句占比过高(六爻仅6%)", "value": f"{very_short/total_sentences*100:.0f}%", "limit": "≤15%", "severity": "blocking"})
    if max_consecutive_short >= 3:
        issues.append({"check": "连续极短句过多", "value": max_consecutive_short, "limit": "≤2", "severity": "warning"})
    if avg_sentence_len < 25:
        issues.append({"check": "平均句长过短(六爻45字)", "value": f"{avg_sentence_len:.0f}字", "limit": "≥25字", "severity": "blocking"})
    elif avg_sentence_len < 30:
        issues.append({"check": "平均句长偏短", "value": f"{avg_sentence_len:.0f}字", "limit": "≥30字", "severity": "warning"})
    if avg_sentence_len > 55:
        issues.append({"check": "平均句长过长", "value": f"{avg_sentence_len:.0f}字", "limit": "≤55字", "severity": "blocking"})
    elif avg_sentence_len > 50:
        issues.append({"check": "平均句长偏长", "value": f"{avg_sentence_len:.0f}字", "limit": "≤55字", "severity": "warning"})
    long_pct = long / max(total_sentences, 1)
    if long_pct < 0.30:
        issues.append({"check": "长句(>30字)占比不足", "value": f"{long_pct*100:.0f}%", "limit": "≥30%", "severity": "warning"})
    if static_paras / max(len(paragraphs), 1) > 0.5:
        issues.append({"check": "静态段落占比过高(主角被动旁观)", "value": f"{static_paras/len(paragraphs)*100:.0f}%", "limit": "≤50%", "severity": "warning"})
    if emotional_flat:
        issues.append({"check": "情绪单调无起伏(全程同温)", "severity": "warning"})
    if protag_active < protag_passive * 0.5:
        issues.append({"check": "主角主动行为过少", "active": protag_active, "passive": protag_passive, "severity": "warning"})
    if max_no_action_gap > 600:
        issues.append({"check": "连续无动作段落过长", "value": f"{max_no_action_gap}字", "limit": "≤600字", "severity": "warning"})
    if opening_slow:
        issues.append({"check": "开篇纯环境铺垫(前300字无对话/动作)", "severity": "warning"})
    if repeat_body_hits:
        issues.append({"check": "体感词重复堆砌(单章≥8次)", "words": list(repeat_body_hits.keys()), "severity": "warning"})
    if protag_active == 0:
        issues.append({"check": "主角全程无主动行为(纯旁观)——注意：群像视角切换时本项可能不适用", "severity": "warning"})

    return {
        "chapter_file": filepath,
        "metrics": {
            "not_but_count": not_but_count,
            "body_auto_count": body_auto_count,
            "philo_count": philo_count,
            "emotion_label_hits": emotion_label_hits,
            "emotion_adverb_hits": emotion_adverb_hits,
            "direct_emotion_hits": direct_emotion_hits,
            "total_paragraphs": len(paragraphs),
            "total_sentences": total_sentences,
            "very_short_sentences": very_short,
            "very_short_pct": round(very_short / max(total_sentences, 1) * 100),
            "max_consecutive_short": max_consecutive_short,
            "avg_sentence_len": round(avg_sentence_len, 1),
            "single_sentence_paras": single_sentence_paras,
            "long_paras": long_paras,
            "avg_para_len": round(avg_para_len, 1),
            "quiet_passages": quiet_count,
            "sensory_touch": sensory["touch"],
            "sensory_hear": sensory["hear"],
            "sensory_sight": sensory["sight"],
            "marker_cool": mark_cool,
            "marker_warm": mark_warm,
            "static_para_pct": round(static_paras / max(len(paragraphs), 1) * 100),
            "protag_active": protag_active,
            "protag_passive": protag_passive,
            "emotional_flat": emotional_flat,
            "max_no_action_gap": max_no_action_gap,
        },
        "issues": issues,
        "blocking_count": sum(1 for i in issues if i.get("severity") == "blocking"),
        "warning_count": sum(1 for i in issues if i.get("severity") == "warning"),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python prose_scanner.py <chapter_file>"}, ensure_ascii=False))
        sys.exit(1)

    result = scan_chapter(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
