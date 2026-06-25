"""
CSDN Playwright Draft Uploader
三态管理：未上传 → 已上传（草稿箱）→ 已发布
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

STATE_FILE = Path(__file__).resolve().parent.parent / "csdn_playwright_state.json"
PUBLISHED_FILE = Path("D:/Writer/.author/published.json")
ARTICLE_MAP_FILE = Path(__file__).resolve().parent.parent / "csdn_article_map.json"
BO_WEN_ROOT = Path("D:/Writer/博文")
SAVE_DRAFT_TIMEOUT = 30000


def log(msg, level="info"):
    prefix = {"info": "[INFO]", "ok": "[OK]", "warn": "[WARN]", "err": "[ERR]"}
    print(f"{prefix.get(level, '[INFO]')} {msg}")


def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to load {path}: {e}", "warn")
        return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_published_titles():
    """已发布：来自 published.json 和 已发表/ 目录."""
    data = load_json(PUBLISHED_FILE)
    titles = set()
    for key in data:
        if isinstance(data[key], list):
            for item in data[key]:
                if isinstance(item, dict) and "title" in item:
                    titles.add(item["title"].strip().lower())
    for pub_dir in BO_WEN_ROOT.rglob("已发表"):
        if pub_dir.is_dir():
            for f in pub_dir.rglob("*.md"):
                content = f.read_text(encoding="utf-8")
                m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if m:
                    titles.add(m.group(1).strip().lower())
    return titles


def get_article_map():
    """已上传（含草稿箱和已发布追踪）."""
    data = load_json(ARTICLE_MAP_FILE)
    return data.get("articles", {}) if isinstance(data, dict) else {}


def save_article_map(articles):
    save_json(ARTICLE_MAP_FILE, {
        "version": 1,
        "articles": articles,
        "updated_at": datetime.now().isoformat(),
    })


def scan_drafts():
    """扫描 草稿/ 目录."""
    articles = []
    for draft_dir in BO_WEN_ROOT.rglob("草稿"):
        if not draft_dir.is_dir():
            continue
        for md_file in sorted(draft_dir.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = guess_title(md_file, content)
            articles.append({"path": md_file, "title": title, "content": content})
    return articles


def guess_title(filepath, content):
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else filepath.stem


def classify(drafts, published_titles, article_map):
    """将文章分为三组：未上传, 已上传, 已发布."""
    not_uploaded = []
    uploaded = []
    published = []

    for d in drafts:
        rel = str(d["path"].relative_to(Path("D:/Writer")))
        title_lower = d["title"].strip().lower()

        if title_lower in published_titles:
            published.append(d)
        elif rel in article_map:
            uploaded.append(d)
        else:
            not_uploaded.append(d)

    return not_uploaded, uploaded, published


# ── Login ────────────────────────────────────────────────

def do_login():
    log("=== CSDN 登录 ===")
    log("浏览器已打开，请手动登录 CSDN。")
    log("登录成功后请在终端按 Enter 继续。")
    input("按 Enter 继续...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://editor.csdn.net/md/", timeout=60000)
        log("等待登录...")

        page.wait_for_url(
            lambda url: "passport" not in url and "login" not in url and "editor" in url,
            timeout=300000,
        )
        log("登录成功！等待编辑器加载...")
        time.sleep(3)

        context.storage_state(path=str(STATE_FILE))
        log(f"登录状态已保存到 {STATE_FILE}", "ok")
        browser.close()


# ── Upload ───────────────────────────────────────────────

def upload_drafts():
    log("=== CSDN Playwright 草稿上传 ===")
    log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not STATE_FILE.exists():
        log("未找到登录状态文件。先用 --login 登录。", "err")
        sys.exit(1)

    published_titles = get_published_titles()
    article_map = get_article_map()
    drafts = scan_drafts()

    not_uploaded, uploaded, published = classify(drafts, published_titles, article_map)

    log(f"扫描结果: 未上传 {len(not_uploaded)} | 已在草稿箱 {len(uploaded)} | 已发布 {len(published)}")

    if not not_uploaded:
        log("没有需要上传的新文章。", "ok")
        return

    log("\n待上传文章:")
    for i, d in enumerate(not_uploaded, 1):
        rel = str(d["path"].relative_to(Path("D:/Writer")))
        log(f"  {i}. [{d['title']}]")
        log(f"      {rel}")

    log("\n" + "=" * 50)
    if "--no-confirm" not in sys.argv:
        c = input("上传这些文章到 CSDN 草稿箱？(y/N): ").strip().lower()
        if c != "y":
            log("已取消。", "warn")
            return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(STATE_FILE))
        success_count = 0
        fail_count = 0

        for i, d in enumerate(not_uploaded, 1):
            rel = str(d["path"].relative_to(Path("D:/Writer")))
            log(f"\n[{i}/{len(not_uploaded)}] {d['title']}")

            page = context.new_page()
            try:
                result = upload_one(page, d["title"], d["content"])
                if result:
                    article_map[rel] = {
                        "id": result["id"],
                        "url": result["url"],
                        "title": result["title"],
                        "uploaded_at": datetime.now().isoformat(),
                        "status": "draft",
                    }
                    save_article_map(article_map)
                    log(f"  ✓ 已上传: {result['url']}", "ok")
                    success_count += 1
                else:
                    log(f"  ✗ 上传失败（无返回结果）", "err")
                    fail_count += 1
            except Exception as e:
                log(f"  ✗ 上传失败: {e}", "err")
                fail_count += 1
            finally:
                page.close()

            if i < len(not_uploaded):
                log("  等待 10 秒...")
                time.sleep(10)

        browser.close()

    log("\n" + "=" * 50)
    log(f"完成: {success_count} 篇上传成功, {fail_count} 篇失败")


def upload_one(page, title, md_content):
    page.goto("https://editor.csdn.net/md/", timeout=60000)
    wait_for_editor(page)
    fill_title(page, title)
    time.sleep(1)
    fill_content(page, md_content)
    time.sleep(2)
    return click_save_draft(page)


def wait_for_editor(page):
    try:
        page.wait_for_url(lambda u: "passport" not in u and "login" not in u, timeout=15000)
    except Exception:
        log("  仍在登录页，等待更久...", "warn")
        page.wait_for_url(lambda u: "passport" not in u and "login" not in u, timeout=120000)
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)


def fill_title(page, title):
    try:
        inp = page.wait_for_selector("input[placeholder*='标题']", timeout=10000)
        inp.click()
        inp.fill("")
        time.sleep(0.5)
        inp.type(title, delay=20)
        log(f"  标题: {title[:50]}")
    except Exception:
        log("  未找到标题输入框，尝试 JS...", "warn")
        safe = title.replace("'", "\\'")
        page.evaluate(f"document.querySelector('input')?.value = '{safe}'")


def fill_content(page, md_content):
    has_cm = page.evaluate("() => !!document.querySelector('.CodeMirror')")
    if has_cm:
        js_content = json.dumps(md_content)
        page.evaluate(f"""
            const cm = document.querySelector('.CodeMirror');
            if (cm && cm.CodeMirror) {{
                cm.CodeMirror.setValue({js_content});
            }}
        """)
        log(f"  内容已写入 CodeMirror ({len(md_content)} 字符)")
        return
    ta = page.query_selector("textarea")
    if ta:
        ta.fill(md_content)
        log(f"  内容已写入 textarea ({len(md_content)} 字符)")
        return
    log("  未找到内容编辑器！", "err")


def click_save_draft(page):
    captured = []

    def on_resp(r):
        if "/saveArticle" in r.url and r.status == 200:
            try:
                captured.append(r.json())
            except Exception:
                pass

    page.on("response", on_resp)

    btn = None
    for sel in [
        "button:has-text('保存草稿')",
        "button:has-text('存草稿')",
        ".btn-save-draft",
        "[class*='save'] button",
    ]:
        try:
            b = page.wait_for_selector(sel, timeout=3000)
            if b and b.is_visible():
                btn = b
                break
        except Exception:
            continue

    if not btn:
        log("  未找到保存草稿按钮，尝试 JS fetch...", "warn")
        return save_via_api(page)

    log("  点击「保存草稿」...")
    with page.expect_response(lambda r: "/saveArticle" in r.url, timeout=SAVE_DRAFT_TIMEOUT) as info:
        btn.click()
    resp = info.value
    try:
        data = resp.json()
        if data.get("code") == 200:
            d = data.get("data", {})
            log(f"  保存成功: id={d.get('id')}", "ok")
            return {"id": d.get("id"), "url": d.get("url"), "title": d.get("title")}
        log(f"  API 返回异常: {json.dumps(data, ensure_ascii=False)[:200]}", "err")
    except Exception as e:
        log(f"  响应解析失败: {e}", "err")

    if captured:
        return extract_from_response(captured[-1])
    return None


def save_via_api(page):
    log("  尝试通过 JS fetch 直接调用 API...")
    try:
        result = page.evaluate("""
            async () => {
                const title = document.querySelector('input[placeholder*="标题"]')?.value || '';
                const cm = document.querySelector('.CodeMirror');
                const markdown = cm?.CodeMirror?.getValue() || '';
                const resp = await fetch('https://bizapi.csdn.net/blog-console-api/v3/mdeditor/saveArticle', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        markdowncontent: markdown,
                        content: '',
                        pubStatus: 'draft',
                        status: 2
                    })
                });
                return await resp.json();
            }
        """)
        if result.get("code") == 200:
            d = result.get("data", {})
            log(f"  JS fetch 成功: id={d.get('id')}", "ok")
            return {"id": d.get("id"), "url": d.get("url"), "title": d.get("title")}
        log(f"  JS fetch 失败: {json.dumps(result, ensure_ascii=False)[:200]}", "err")
    except Exception as e:
        log(f"  JS fetch 异常: {e}", "err")
    return None


def extract_from_response(data):
    if isinstance(data, dict) and data.get("code") == 200:
        d = data.get("data", {})
        return {"id": d.get("id"), "url": d.get("url"), "title": d.get("title")}
    return None


# ── Sync article_map with published status ───────────────

def sync_published():
    """将已发布的文章在 csdn_article_map 中标记为 published."""
    published_titles = get_published_titles()
    article_map = get_article_map()
    changed = False
    for rel, info in article_map.items():
        if info.get("status") == "draft":
            title_lower = info.get("title", "").strip().lower()
            if title_lower in published_titles:
                info["status"] = "published"
                info["published_at"] = datetime.now().isoformat()
                changed = True
                log(f"  {rel} → 已发布", "ok")
    if changed:
        save_article_map(article_map)
        log("article_map 已更新。", "ok")
    else:
        log("无变化。", "info")


# ── Entry ────────────────────────────────────────────────

if __name__ == "__main__":
    if "--login" in sys.argv:
        do_login()
    elif "--sync" in sys.argv:
        sync_published()
    elif "--dry-run" in sys.argv:
        published = get_published_titles()
        article_map = get_article_map()
        drafts = scan_drafts()
        nu, up, pb = classify(drafts, published, article_map)
        log(f"总计: {len(drafts)} 篇 (未上传 {len(nu)} | 草稿箱 {len(up)} | 已发布 {len(pb)})")
        log("")
        if nu:
            log("--- 未上传 ---")
            for d in nu:
                rel = str(d["path"].relative_to(Path("D:/Writer")))
                log(f"  {d['title']}")
                log(f"    {rel}")
        if up:
            log("--- 已在草稿箱 ---")
            for d in up:
                rel = str(d["path"].relative_to(Path("D:/Writer")))
                info = article_map.get(rel, {})
                log(f"  {d['title']}  (id={info.get('id')}, 上传于{info.get('uploaded_at','?')[:10]})")
        if pb:
            log("--- 已发布 ---")
            for d in pb:
                log(f"  {d['title']}")
    else:
        upload_drafts()
