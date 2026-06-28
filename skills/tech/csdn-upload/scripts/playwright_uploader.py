"""
CSDN Draft Uploader
===================
Three-state management: not-uploaded -> draft -> published.

Uses Playwright to supply an authenticated browser context (saved in
chrome_profile/) and calls the CSDN bizapi directly via a JavaScript
injection that computes the HMAC-SHA256 X-Ca signature in-browser.

This avoids fragile UI automation against the Vue 3 contenteditable editor.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

# ── Paths ─────────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
USER_DATA_DIR = SKILL_ROOT / "chrome_profile"
ARTICLE_MAP_FILE = SKILL_ROOT / "csdn_article_map.json"
BO_WEN_ROOT = Path("D:/Writer/博文")
PUBLISHED_FILE = Path("D:/Writer/.author/published.json")
FAILED_FILE = SKILL_ROOT / ".upload_failed.json"

# ── CSDN API credentials (from app chunk analysis) ───────────────────────

CA_KEY = "203803574"
CA_SECRET = "9znpamsyl2c7cdrr9sas0le9vbc3r6ba"
SAVE_URL = "https://bizapi.csdn.net/blog-console-api/v3/mdeditor/saveArticle"


# ── Helpers ───────────────────────────────────────────────────────────────

def log(msg: str, level: str = "info") -> None:
    prefix = {"info": "[INFO]", "ok": "[OK]", "warn": "[WARN]", "err": "[ERR]"}
    print(f"{prefix.get(level, '[INFO]')} {msg}")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"Failed to load {path}: {e}", "warn")
        return {}


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def md_to_html(md_text: str) -> str:
    html = markdown.markdown(md_text, extensions=["fenced_code", "codehilite", "tables", "nl2br"])
    return html if html.strip() else "<p></p>"


# ── Article scanning & classification ────────────────────────────────────

def scan_drafts() -> list[dict]:
    articles = []
    for draft_dir in BO_WEN_ROOT.rglob("草稿"):
        if not draft_dir.is_dir():
            continue
        for md_file in sorted(draft_dir.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            title = _guess_title(md_file, content)
            articles.append({"path": md_file, "title": title, "content": content})
    return articles


def _guess_title(filepath: Path, content: str) -> str:
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else filepath.stem


def get_published_titles() -> set[str]:
    titles: set[str] = set()

    data = load_json(PUBLISHED_FILE)
    for val in data.values():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "title" in item:
                    titles.add(item["title"].strip().lower())

    for pub_dir in BO_WEN_ROOT.rglob("已发表"):
        if pub_dir.is_dir():
            for f in pub_dir.rglob("*.md"):
                m = re.search(r"^#\s+(.+)$", f.read_text(encoding="utf-8"), re.MULTILINE)
                if m:
                    titles.add(m.group(1).strip().lower())

    return titles


def get_article_map() -> dict:
    return load_json(ARTICLE_MAP_FILE).get("articles", {})


def save_article_map(articles: dict) -> None:
    save_json(ARTICLE_MAP_FILE, {
        "version": 1,
        "articles": articles,
        "updated_at": datetime.now().isoformat(),
    })


def classify(drafts: list[dict], published_titles: set[str], article_map: dict):
    not_uploaded, uploaded, published_list = [], [], []
    for d in drafts:
        rel = str(d["path"].relative_to(Path("D:/Writer")))
        tl = d["title"].strip().lower()
        if tl in published_titles:
            published_list.append(d)
        elif rel in article_map:
            uploaded.append(d)
        else:
            not_uploaded.append(d)
    return not_uploaded, uploaded, published_list


# ── JavaScript injection for X-Ca signed API call ────────────────────────

def make_save_js(key: str, secret: str, url: str, body: dict) -> str:
    """Build a JS async IIFE string consumable by page.evaluate().

    All values are inlined directly (no Playwright `args` parameter)
    because the IIFE is wrapped by Playwright as
    ``function(args) { return (EXPRESSION) }`` and the `args` variable
    is NOT accessible from within the IIFE scope.
    """
    body_str = json.dumps(body, ensure_ascii=False)

    return (
        "(async () => {\n"
        f"const nonce = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {{\n"
        f"    const r = Math.random() * 16 | 0;\n"
        f"    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);\n"
        f"}});\n"
        f"const path = new URL('{url}').pathname;\n"
        f"const sigStr = 'POST\\n*/*\\n\\napplication/json\\n\\nx-ca-key:{key}\\nx-ca-nonce:' + nonce + '\\n' + path;\n"
        f"const ek = await crypto.subtle.importKey('raw', new TextEncoder().encode('{secret}'),\n"
        f"    {{name: 'HMAC', hash: 'SHA-256'}}, false, ['sign']);\n"
        f"const sg = await crypto.subtle.sign('HMAC', ek, new TextEncoder().encode(sigStr));\n"
        f"const sig = btoa(String.fromCharCode(...new Uint8Array(sg)));\n"
        f"try {{\n"
        f"    const r = await fetch('{url}', {{\n"
        f"        method: 'POST', credentials: 'include',\n"
        f"        headers: {{\n"
        f"            'Content-Type':'application/json','Accept':'*/*',\n"
        f"            'X-Ca-Key':'{key}','X-Ca-Nonce':nonce,\n"
        f"            'X-Ca-Signature-Headers':'x-ca-key,x-ca-nonce','X-Ca-Signature':sig\n"
        f"        }},\n"
        f"        body: JSON.stringify({body_str}),\n"
        f"    }});\n"
        f"    const d = await r.json();\n"
        f"    return JSON.stringify({{code: d.code, id: d.data ? d.data.id : null, msg: d.msg}});\n"
        f"}} catch(e) {{\n"
        f"    return JSON.stringify({{code: -1, msg: e.message}});\n"
        f"}}\n"
        "})()"
    )


# ── Login ─────────────────────────────────────────────────────────────────

def do_login() -> None:
    log("=== CSDN 登录 ===")
    log("浏览器已打开，请在浏览器中登录 CSDN，然后关掉浏览器窗口。")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(USER_DATA_DIR), headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://editor.csdn.net/md/", timeout=60000)
        page.wait_for_url(
            lambda u: "passport" not in u and "login" not in u and "editor" in u,
            timeout=300000,
        )
        log("检测到登录成功！请关掉浏览器窗口继续。", "ok")
        context.close()


def check_login() -> bool:
    if not USER_DATA_DIR.exists():
        return False
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(USER_DATA_DIR), headless=True,
            )
            page = context.new_page()
            page.goto("https://www.csdn.net/", timeout=30000)
            time.sleep(3)
            ok = "passport" not in page.url and "login" not in page.url
            context.close()
            return ok
    except Exception:
        return False


# ── Upload (core) ─────────────────────────────────────────────────────────

RETRY_WAIT = 10       # seconds between articles
MAX_RETRIES = 3       # per-article retries on rate-limit


def upload_articles(articles: list[dict]) -> None:
    if not articles:
        return

    article_map = get_article_map()
    success = fail = 0
    batch_failed_paths: list[str] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(USER_DATA_DIR), headless=True,
        )
        page = context.new_page()
        page.goto("https://www.csdn.net/", timeout=30000)
        time.sleep(2)

        for i, d in enumerate(articles, 1):
            rel = str(d["path"].relative_to(Path("D:/Writer")))
            log(f"\n[{i}/{len(articles)}] {d['title']}")

            html_content = md_to_html(d["content"])
            body = {
                "title": d["title"],
                "markdowncontent": d["content"],
                "content": html_content,
                "readType": "public", "tags": "",
                "status": 2, "categories": "",
                "type": "original", "original_link": "",
                "authorized_status": False, "not_auto_saved": "1",
                "source": "pc_mdeditor", "cover_images": [], "cover_type": 0,
                "is_new": 1, "vote_id": 0, "pubStatus": "draft", "level": 0,
            }

            ok = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    js = make_save_js(CA_KEY, CA_SECRET, SAVE_URL, body)
                    result_str = page.evaluate(js)

                    try:
                        result = json.loads(result_str)
                    except json.JSONDecodeError:
                        log(f"  JSON 解析失败: {result_str[:200]}", "err")
                        break

                    code = result.get("code")
                    msg = result.get("msg", "")

                    if code == 200:
                        article_map[rel] = {
                            "id": result["id"],
                            "title": d["title"],
                            "uploaded_at": datetime.now().isoformat(),
                            "status": "draft",
                        }
                        save_article_map(article_map)
                        log(f"  OK id={result['id']}", "ok")
                        ok = True
                        success += 1
                        break

                    if "频繁" in str(msg):
                        if attempt < MAX_RETRIES:
                            wait = RETRY_WAIT * attempt
                            log(f"  频率限制，{wait}s 后重试({attempt}/{MAX_RETRIES})...", "warn")
                            time.sleep(wait)
                        else:
                            log(f"  频率限制，已达最大重试次数", "err")
                            fail += 1
                    else:
                        log(f"  FAIL ({code}): {msg}", "err")
                        fail += 1
                        break

                except Exception as e:
                    log(f"  异常: {e}", "err")
                    fail += 1
                    break

            if not ok:
                batch_failed_paths.append(rel)

            if i < len(articles):
                log(f"  间隔 {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)

        context.close()

    log(f"\n完成: {success} 篇成功, {fail} 篇失败")

    if batch_failed_paths:
        save_json(FAILED_FILE, {"failed": batch_failed_paths, "updated_at": datetime.now().isoformat()})
        log(f"失败列表已保存，可用 --retry-failed 重试", "warn")


# ── Sync published status ─────────────────────────────────────────────────

def sync_published() -> None:
    published_titles = get_published_titles()
    article_map = get_article_map()
    changed = False
    for rel, info in article_map.items():
        if info.get("status") == "draft":
            if info.get("title", "").strip().lower() in published_titles:
                info["status"] = "published"
                info["published_at"] = datetime.now().isoformat()
                changed = True
                log(f"  {rel} -> published", "ok")
    if changed:
        save_article_map(article_map)
    else:
        log("无变更。")


# ── Entry point ───────────────────────────────────────────────────────────

def main() -> None:
    log(f"=== CSDN 草稿上传 ===")
    log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --login --------------------------------------------------------------
    if "--login" in sys.argv:
        do_login()
        return

    # Login check (everything below needs it)
    if not check_login():
        log("未检测到有效登录状态。请先执行 --login 登录。", "err")
        sys.exit(1)

    published_titles = get_published_titles()
    article_map = get_article_map()
    drafts = scan_drafts()

    # --sync ---------------------------------------------------------------
    if "--sync" in sys.argv:
        sync_published()
        return

    # --dry-run ------------------------------------------------------------
    if "--dry-run" in sys.argv:
        nu, up, pb = classify(drafts, published_titles, article_map)
        log(f"总计: {len(drafts)} 篇 | 未上传 {len(nu)} | 草稿箱 {len(up)} | 已发布 {len(pb)}")
        if nu:
            log("\n--- 未上传 ---")
            for d in nu:
                log(f"  {d['title']}")
                log(f"    {str(d['path'].relative_to(Path('D:/Writer')))}")
        if up:
            log("\n--- 草稿箱 ---")
            am = get_article_map()
            for d in up:
                rel = str(d["path"].relative_to(Path("D:/Writer")))
                info = am.get(rel, {})
                log(f"  {d['title']} (id={info.get('id')}, status={info.get('status')})")
        if pb:
            log("\n--- 已发布 ---")
            for d in pb:
                log(f"  {d['title']}")
        return

    # --retry-failed -------------------------------------------------------
    if "--retry-failed" in sys.argv:
        failed_data = load_json(FAILED_FILE)
        failed_paths = set(failed_data.get("failed", []))
        if not failed_paths:
            log("没有找到失败记录。", "warn")
            return
        to_retry = [d for d in drafts if str(d["path"].relative_to(Path("D:/Writer"))) in failed_paths]
        log(f"上次失败 {len(failed_paths)} 篇，本次重试 {len(to_retry)} 篇")
        upload_articles(to_retry)
        return

    # --default: upload drafts ---------------------------------------------
    not_uploaded, uploaded, published_list = classify(drafts, published_titles, article_map)
    log(f"扫描: 未上传 {len(not_uploaded)} | 草稿箱 {len(uploaded)} | 已发布 {len(published_list)}")

    if not not_uploaded:
        log("没有需要上传的新文章。", "ok")
        return

    log("\n待上传:")
    for i, d in enumerate(not_uploaded, 1):
        log(f"  {i}. {d['title']}")
        log(f"     {str(d['path'].relative_to(Path('D:/Writer')))}")

    log("=" * 50)
    if "--no-confirm" not in sys.argv:
        c = input("上传到 CSDN 草稿箱？(y/N): ").strip().lower()
        if c != "y":
            log("已取消。", "warn")
            return

    upload_articles(not_uploaded)


if __name__ == "__main__":
    main()
