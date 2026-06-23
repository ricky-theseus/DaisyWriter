# Fanqie current workflow notes

Validated from live publishing on 2026-03-20:

1. Open chapter management for the target book.
2. On chapter management page, switch to the target volume first.
3. Enter `新建章节` from chapter management, so the new draft inherits the currently selected volume.
4. On the editor page, dismiss onboarding / guide dialogs if present.
5. Fill chapter number, title, and正文.
6. Save draft once and confirm the visible word count is no longer `0`.
7. Click top-right `下一步`.
8. Handle spellcheck / typo warning modal:
   - common copy: `检测到你还有错别字未修改，是否确定提交？`
   - continue action: `提交`
9. Handle risk-detection modal:
   - common copy: `是否进行内容风险检测？`
   - if the operator chose to continue publishing, click `确定`
10. Handle final publish settings modal:
   - verify target volume and chapter title
   - **must select `是否使用AI -> 否`**
   - for immediate publish, leave scheduled switch off
   - for scheduled publish, enable `定时发布` and fill date/time
   - click `确认发布`
11. Verify by returning to chapter management:
   - row exists for the target chapter
   - expected post-submit states include `审核中` or `已发布`

Important platform constraint:
- if the backend warns `请在发布时间前30分钟提交修改内容，否则无法完成修改`, the scheduled chapter is too close to its publish time to safely modify

Important implementation note:
- opening `/publish/` directly is not enough when a specific volume is required; the reliable path is `章节管理 -> 切到目标分卷 -> 新建章节`

Current script support added:
- optional `--volume "<分卷名>"` before filling chapter number/title/body
- optional `--debug-volume` to print visible volume-related candidate nodes
- optional `--debug-volume-stop` to stop after opening/selecting the volume, for reconnaissance
