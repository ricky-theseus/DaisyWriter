---
name: xiaohongshu-technical-post-copy
description: Use when writing Xiaohongshu technical post copy that accompanies a technical infographic, especially for engineering, AI, chip, or CUDA readers who need practical interpretation, boundaries, and reading guidance rather than image repetition.
user-invocable: true
metadata: {"openclaw":{"skillKey":"xiaohongshu-technical-post-copy"}}
---

# Xiaohongshu Technical Post Copy

Generate a Xiaohongshu technical note based on a technical infographic.

## Inputs

Require or infer these inputs from the user:

- Content topic: `[fill image topic]`
- Image information: `[briefly describe image content, modules, key arrows, or conclusions]`
- Target length: `[for example 200 words / 500 words / 1000 words]`

Target readers have some technical foundation, but may not be familiar with the specific engineering, AI, chip, or CUDA topic.

## Goal

Do not restate the image. Add the engineering judgment, applicability boundaries, and reading method behind the image.

## Output Format

1. Provide 3 title candidates.
2. Provide one formal post body.
3. Keep the body within the requested target length.
4. End with one calm takeaway sentence.

## Title Rules

- Write titles like technical section names.
- Do not use clickbait, questions, exaggeration, or hype.
- Avoid expressions such as "全网最全", "一文看懂", "终于讲清楚", and "颠覆认知".
- A colon is allowed.
- Technical terms and English terms may be kept.

## Body Style

- Be concise, practical, calm, and engineering-oriented.
- Avoid marketing tone, filler, emojis, emotional language, and excessive adjectives.
- Avoid the sentence pattern "不是……而是……".

## Body Structure

- Start by stating directly what problem the image helps solve.
- Add judgments, boundaries, and common mistakes beyond the image.
- Summarize key judgments with 2 to 4 short sentences.
- End with a restrained engineering takeaway.

## Technical Requirements

- Avoid absolute claims.
- For architecture, experience, and performance-related content, use qualifiers such as:
  - 通常
  - 取决于 workload
  - 作为粗评估
  - 简化视角
  - 需要结合 profiling
- Do not imply technical certainty when the image only supports a simplified view.