# Editor and publish-flow reference

## Confirmed dashboard signals
- writer dashboard loads successfully after login
- chapter management link exists
- create chapter link exists
- concrete create-chapter path resolves to a draft URL under `/main/writer/<bookId>/publish/<chapterId>`

## Confirmed editor selectors
- save draft button: `.auto-editor-save-btn`
- next button: `.publish-button.auto-editor-next`
- chapter serial input: `input.serial-input.byte-input.byte-input-size-default`
- title input: `input[placeholder="请输入标题"]`
- main editor: `.ProseMirror[contenteditable="true"]`

## Parsing rule adjustment
The Fanqie editor splits chapter number and chapter title into separate inputs.
Example:
- source heading: `第001章 拉闸`
- serial input should receive: `1`
- title input should receive: `拉闸`

Rule: strip leading zeroes from chapter numbers before filling the serial input.

## Observed caveat
The page may contain multiple `.ProseMirror` editors because of AI helper / outline sections.
The main chapter body editor currently appears as the **first** `.ProseMirror[contenteditable="true"]` on the page.
This should be re-verified before major changes.

## Detection flow
After clicking `下一步`, there may be multiple confirmation gates before the final publish dialog:
1. content risk detection confirm modal
2. typo / misspelling detection confirm modal
   - if smart correction appears, prefer `替换全部`
   - if a follow-up submit warning appears, prefer `提交`
3. possible writer-guide / tour overlay (`reactour__helper`)
4. final publish dialog

## Final publish dialog signals
- modal container: `.arco-modal.publish-confirm-container-new`
- AI selection exists with `是 / 否`
- scheduled publish switch exists as `button[role="switch"]`
- final primary button text: `确认发布`
- cancel button text: `取消`

## Safe stop point
A safe mode should:
- fill chapter serial, title, and body
- click `下一步`
- confirm risk / typo detection gates
- reach the final publish dialog
- select `AI = 否`
- stop before clicking `确认发布`

## Scheduled publish limitation
Fanqie may show the warning:
`请在发布时间前30分钟提交修改内容，否则无法完成修改`

Practical consequence:
- once a chapter is within ~30 minutes of its scheduled publish time, modifying that scheduled chapter may fail or be blocked
- if a reschedule is needed, do it well in advance
- prefer creating the final desired schedule correctly the first time
