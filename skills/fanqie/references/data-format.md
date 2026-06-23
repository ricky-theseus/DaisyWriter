# Chapter source format

Observed source directory:
- /path/to/chapters

Observed file naming:
- 第001章_拉闸.md
- 第002章_卖命契约.md

Observed content format:
- line 1: markdown heading, e.g. `# 第001章 拉闸`
- remaining lines: chapter body

Current parser behavior:
- use first markdown heading as title when present
- otherwise derive title from filename
- split chapter heading into serial + display title when it matches `第NNN章 标题`
- fill the Fanqie serial input with the numeric part **without leading zeroes**
- remove first heading from body
- preserve body paragraphs as plain text
