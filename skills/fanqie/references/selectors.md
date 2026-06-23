# Selector checklist

## Chapter management
- Chapter management selector: `a[href*="/main/writer/chapter-manage/"]`
- Volume dropdown trigger on chapter management:
  - `.chapter-select .serial-select.flat-serial-select.byte-select.byte-select-size-default`
  - fallback: `.chapter-select .serial-select`
  - fallback: `.chapter-select .byte-select-view-value`
- Volume option on chapter management:
  - `.byte-select-popup .byte-select-option.chapter-select-option`
  - fallback: `.byte-select-option.chapter-select-option`
  - fallback: `.byte-select-option`
- New chapter entry on chapter management:
  - `a[href*="/publish/"][href*="enter_from=newchapter"]`
  - fallback: `a[href*="/publish/?enter_from=newchapter"]`
  - fallback: `button:has-text("新建章节")`

## Editor
- Serial/chapter-number input selector: `input.serial-input.byte-input.byte-input-size-default`
- Title input selector: `input[placeholder="请输入标题"]`
- Body editor selector: `.ProseMirror[contenteditable="true"]`
- Save draft button selector: `.auto-editor-save-btn` and visible text `存草稿`
- Next button selector: `.publish-button.auto-editor-next` and visible text `下一步`
- Guide / onboarding dialogs:
  - `.reactour__helper`
  - `.publish-guide`
  - generic fallback: `[role="dialog"]`, `.arco-modal`, `.byte-modal`

## Pre-publish intercept modals
- Misspelling / spellcheck modal text:
  - `检测到你还有错别字未修改，是否确定提交？`
  - continue button is **`提交`**
- Risk-detection modal text:
  - `是否进行内容风险检测？`
  - continue button is **`确定`**
- Generic dialog fallbacks:
  - `.arco-modal[role="dialog"]`
  - `.byte-modal[role="dialog"]`
  - `.arco-modal`
  - `.byte-modal`

## Final publish modal
- Publish modal container: `.arco-modal.publish-confirm-container-new`
- Must verify visible text contains:
  - target volume, e.g. `第二卷：城市猎场`
  - target chapter, e.g. `第90章 猎犬与新王`
- AI choice group: `.arco-radio-group`
- AI=no selector: label/text `否` inside publish modal
- Scheduled publish switch: `button[role="switch"]` inside publish modal
- Confirm publish selector: button text `确认发布`
- Cancel publish selector: button text `取消`
- Date picker selector: `input[placeholder="请选择日期"]`
- Time picker selector: `input[placeholder="请选择时间"]`

## Post-submit verification
- Verify by navigating back to chapter management URL
- Target row should contain normalized title `第N章 标题`
- Expected status after submit:
  - `审核中`
  - or `已发布`

## Known pitfalls
- `是否使用AI` is effectively required before `确认发布` can really submit; defaulting to no explicit selection can leave the modal in place.
- Directly opening the draft URL does not guarantee the correct volume; prefer selecting the volume on chapter management first, then entering `新建章节`.
