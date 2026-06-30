---
name: xiaohongshu-minimal-technical-infographic
description: Use when creating clean 3:4 vertical technical teaching infographics for Xiaohongshu or social media, especially minimal grayscale engineering diagrams that must preserve real data flow, scheduling flow, hierarchy, or dependency semantics.
user-invocable: true
metadata: {"openclaw":{"skillKey":"xiaohongshu-minimal-technical-infographic"}}
---

# Xiaohongshu Minimal Technical Infographic

Create a 3:4 vertical technical infographic on a pure white background.

## Priority

1. Clarity
2. Technical correctness
3. Visual beauty

## Visual Style

- Use a minimal academic engineering diagram style.
- Use a clean black, dark gray, and light gray palette.
- Use thin, consistent lines.
- Use light gray rounded rectangles for grouped units.
- Use subtle dashed dividers for conceptual boundaries.
- Avoid emojis, cartoon icons, strong gradients, saturated colors, 3D perspective, and decorative shadows.

## Text Style

- Use concise, objective, engineering-oriented wording.
- Use short technical labels and one-line explanations.
- Avoid hype, rhetorical questions, repeated slogans, and the phrase pattern "not A but B".

## Layout Rules

- Organize content into clear sections or columns.
- Leave enough whitespace; do not overcrowd the canvas.
- Use arrows only for real data flow, scheduling flow, hierarchy, or dependency.
- Keep arrow widths consistent.
- Use dashed lines for conceptual boundaries.

## Color Rules

Use mostly grayscale. If needed, use only one or two muted accent colors:

- Blue: theoretical model or upper bound
- Green: runtime profiling or measured behavior
- Purple: insight or decision
- Orange: data movement or memory transfer

Do not use large colorful blocks.

## Technical Constraints

- Do not create false dependencies.
- Do not connect parallel compute units in series.
- Do not imply data flows that do not exist.
- Mark architecture-dependent details as optional or examples.
- Prefer a simplified correct structure over a visually complex diagram.

## Output

Return a clean, readable, social-media-ready technical teaching image.