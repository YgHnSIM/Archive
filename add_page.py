#!/usr/bin/env python3
"""요약 페이지 아카이브 관리 도구 (python3 표준 라이브러리만 사용, 모바일 검사만 Playwright 선택 사용).

사용 예:
  python3 add_page.py <source.html> --title "제목" --summary "요약" --tags AI,소프트웨어 [--date 2026-10-06]
  python3 add_page.py --rebuild              # catalog.json 손으로 고친 뒤 catalog.js 재생성
  python3 add_page.py --list                 # 항목 목록
  python3 add_page.py --remove <id> [--delete-file]
  python3 add_page.py --check [id|all]       # 모바일(390/360px) 가로 넘침·글자 크기 검사
  python3 add_page.py --fix-mobile [id|all]  # 기존 페이지에 모바일 보정 주입
  python3 add_page.py --restyle [id|all]     # 공통 머리띠·꼬리말·공통 CSS 주입/갱신 (STYLE_GUIDE.md)
  python3 add_page.py --check-style [id|all] # 형식 표준 검사
  python3 add_page.py --edit <id> --source-url URL [--title ..] [--tags ..] [--tokens on|off]
  python3 add_page.py --replace <id> <새 source.html> [--summary ..]  # 같은 id·같은 파일명으로 교체
  ... --commit [--no-push]                   # 작업 후 git commit (+ push)
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata

try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except Exception:  # tzdata 없는 환경 대비
    KST = dt.timezone(dt.timedelta(hours=9), "KST")

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(ROOT, "pages")
CATALOG_JSON = os.path.join(ROOT, "catalog.json")
CATALOG_JS = os.path.join(ROOT, "catalog.js")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHECK_WIDTHS = (390, 360)

# ---------------------------------------------------------------- 모바일 보정
MOBILE_MARK = "archive-mobile-css"
VIEWPORT_TAG = '<meta name="viewport" content="width=device-width, initial-scale=1">'
# :where() 로 감싸 명시도 0 → 원래 페이지 규칙과 충돌하면 항상 원래 규칙이 이김 (빈틈만 메움)
MOBILE_CSS = f"""<!-- {MOBILE_MARK} v1: 아카이브가 자동 추가한 모바일 보정 (본문 내용은 바꾸지 않음) -->
<style id="{MOBILE_MARK}">
:where(html){{-webkit-text-size-adjust:100%;text-size-adjust:100%}}
:where(img,video,canvas,iframe,embed,object,svg){{max-width:100%}}
:where(img,video){{height:auto}}
@media (max-width:640px){{
  :where(body){{overflow-wrap:break-word}}
  :where(pre){{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
  :where(table){{display:block;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}}
  :where(code,kbd,samp){{overflow-wrap:anywhere}}
  :where(input,select,textarea){{font-size:16px}}
}}
</style>
"""


def die(msg, code=1):
    print(f"오류: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"경고: {msg}", file=sys.stderr)


def nfc(s):
    return unicodedata.normalize("NFC", s)


def now_kst():
    return dt.datetime.now(KST)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def path_hash(path):
    """원본 경로 자체는 공개 저장소에 남기지 않고 해시만 보관 (중복 감지용)."""
    return hashlib.sha256(nfc(os.path.abspath(path)).encode("utf-8")).hexdigest()


def atomic_write(path, text, encoding="utf-8", errors="strict"):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=os.path.basename(path))
    try:
        with os.fdopen(fd, "w", encoding=encoding, errors=errors, newline="") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def inject_mobile(text):
    """(새 텍스트, 변경 내용 목록). 이미 주입된 경우 다시 넣지 않는다."""
    notes = []
    vp = re.search(r"<meta\b[^>]*\bname\s*=\s*[\"']?viewport\b[^>]*>", text, re.I)
    if vp is None:
        m = (re.search(r"<meta\b[^>]*\bcharset\b[^>]*>", text, re.I)
             or re.search(r"<head\b[^>]*>", text, re.I))
        if m:
            text = text[:m.end()] + "\n" + VIEWPORT_TAG + text[m.end():]
        else:
            m = re.search(r"<html\b[^>]*>", text, re.I)
            pos = m.end() if m else 0
            text = text[:pos] + "\n<head>" + VIEWPORT_TAG + "</head>\n" + text[pos:]
        notes.append("viewport meta 추가")
    elif not re.search(r"width\s*=\s*device-width", vp.group(0), re.I):
        text = text[:vp.start()] + VIEWPORT_TAG + text[vp.end():]
        notes.append(f"viewport 교체 (기존: {vp.group(0)})")
    if MOBILE_MARK not in text:
        m = re.search(r"</head\s*>", text, re.I)
        if m:  # 페이지 자체 스타일 뒤에 둠
            text = text[:m.start()] + MOBILE_CSS + text[m.start():]
        else:
            vp = re.search(r"<meta\b[^>]*\bname\s*=\s*[\"']?viewport\b[^>]*>", text, re.I)
            text = text[:vp.end()] + "\n" + MOBILE_CSS + text[vp.end():]
        notes.append("모바일 보정 CSS 추가")
    return text, notes


def apply_mobile(path):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        old = f.read()
    new, notes = inject_mobile(old)
    if new != old:
        atomic_write(path, new, errors="surrogateescape")
    return notes


def mobile_check(paths, widths=CHECK_WIDTHS):
    """Playwright 가 있으면 각 페이지를 모바일 폭으로 열어 검사. 문제 수 반환, 불가하면 None."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("Playwright 가 없어 모바일 검사를 건너뜁니다 (pip install playwright).")
        return None
    js = r"""() => {
      const vw = document.documentElement.clientWidth, bad = [];
      for (const el of document.body.querySelectorAll('*')) {
        const r = el.getBoundingClientRect(); if (!r.width) continue;
        if (r.right <= vw + 1 && r.left >= -1) continue;
        const st = getComputedStyle(el); if (st.position === 'fixed' || st.visibility === 'hidden') continue;
        let p = el.parentElement, ok = false;
        while (p && p !== document.body) {
          if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(p).overflowX)) {
            const pr = p.getBoundingClientRect(); if (pr.right <= vw + 1 && pr.left >= -1) { ok = true; break; } }
          p = p.parentElement; }
        if (!ok) bad.push(el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/)[0] : ''));
      }
      const vp = document.querySelector('meta[name=viewport]');
      return {scrollW: document.documentElement.scrollWidth, vw,
              viewport: vp ? vp.content : null,
              font: parseFloat(getComputedStyle(document.body).fontSize), bad: [...new Set(bad)].slice(0, 8)};
    }"""
    exe = next((p for p in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser")
                if os.path.exists(p)), None)
    problems = 0
    try:
        with sync_playwright() as pw:
            try:
                b = pw.chromium.launch(args=["--no-sandbox"])
            except Exception:
                if not exe:
                    raise
                b = pw.chromium.launch(executable_path=exe, args=["--no-sandbox"])
            for path in paths:
                for w in widths:
                    ctx = b.new_context(viewport={"width": w, "height": 800}, is_mobile=True, has_touch=True)
                    pg = ctx.new_page()
                    pg.goto("file://" + os.path.abspath(path))
                    pg.wait_for_timeout(300)
                    r = pg.evaluate(js)
                    ctx.close()
                    issues = []
                    if not r["viewport"] or "device-width" not in r["viewport"]:
                        issues.append("viewport 없음")
                    if r["scrollW"] > w:
                        issues.append(f"가로 넘침 {r['scrollW']}px")
                    if r["bad"]:
                        issues.append("화면 밖 요소: " + ", ".join(r["bad"]))
                    if r["font"] < 16:
                        issues.append(f"본문 글자 {r['font']}px (<16px)")
                    name = os.path.relpath(path, ROOT)
                    if issues:
                        problems += 1
                        print(f"  모바일 {w}px ✗ {name}: " + "; ".join(issues))
                    else:
                        print(f"  모바일 {w}px ✓ {name} (본문 {r['font']:g}px, 넘침 없음)")
            b.close()
    except Exception as e:
        warn(f"모바일 검사 실행 실패: {e}")
        return None
    return problems


# ---------------------------------------------------------------- 공통 형식 (STYLE_GUIDE.md)
import html as _html

ASSET_PAGE_CSS = "assets/archive-page.css"
ASSET_TOKENS_CSS = "assets/archive-tokens.css"
HEAD_START, HEAD_END = "<!-- archive-head:start", "<!-- archive-head:end -->"
HDR_START, HDR_END = "<!-- archive-header:start", "<!-- archive-header:end -->"
FTR_START, FTR_END = "<!-- archive-footer:start", "<!-- archive-footer:end -->"
FIX_MARK = "<!-- archive-fix"
AUTO_NOTE = "(자동 생성: add_page.py --restyle, 직접 고치지 마세요) -->"


def esc(s):
    return _html.escape(str(s or ""), quote=True)


def kdate(d):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d or "")
    return f"{m.group(1)}년 {int(m.group(2))}월 {int(m.group(3))}일" if m else (d or "")


def rel_root(entry):
    depth = entry["file"].count("/")
    return "../" * depth


def tag_links(entry, up):
    from urllib.parse import quote
    return "".join(
        f'<a class="arc-tag" href="{up}index.html#tags={quote(t, safe="")}">#{esc(t)}</a>'
        for t in entry.get("tags", []))


def render_head(entry):
    up = rel_root(entry)
    links = [f'<link rel="stylesheet" href="{up}{ASSET_PAGE_CSS}">']
    if entry.get("tokens", True):
        links.append(f'<link rel="stylesheet" href="{up}{ASSET_TOKENS_CSS}">')
    return f"{HEAD_START} {AUTO_NOTE}\n" + "\n".join(links) + f"\n{HEAD_END}\n"


def render_header(entry):
    up = rel_root(entry)
    src = entry.get("source_url")
    src_html = f'<a class="arc-src" href="{esc(src)}" rel="noopener">원문 ↗</a>' if src else ""
    return (
        f"{HDR_START} {AUTO_NOTE}\n"
        f'<div class="arc-band" role="navigation" aria-label="요약 아카이브"><div class="arc-inner">'
        f'<a class="arc-back" href="{up}index.html"><b>←</b>요약 아카이브</a>'
        f'<span class="arc-crumb">{esc(entry["title"])}</span>'
        f'<span class="arc-meta"><time datetime="{esc(entry["date"])}">{kdate(entry["date"])}</time>'
        f'{tag_links(entry, up)}{src_html}</span>'
        f"</div></div>\n{HDR_END}\n"
    )


def render_footer(entry):
    up = rel_root(entry)
    src = entry.get("source_url")
    src_html = f' · <a href="{esc(src)}" rel="noopener">원문 ↗</a>' if src else ""
    return (
        f"\n{FTR_START} {AUTO_NOTE}\n"
        f'<div class="arc-foot" aria-label="아카이브 정보"><div class="arc-inner">'
        f'<div class="arc-foot-label">요약 아카이브</div>'
        f'<div class="arc-foot-title">{esc(entry["title"])}</div>'
        f'<div class="arc-foot-meta"><time datetime="{esc(entry["date"])}">{kdate(entry["date"])}</time>'
        f'{tag_links(entry, up)}{src_html}</div>'
        f'<div class="arc-foot-nav"><a href="{up}index.html">← 목록으로</a><a href="#">↑ 맨 위로</a></div>'
        f"</div></div>\n{FTR_END}\n"
    )


def _replace_block(text, start, end, new):
    """start~end 표식 블록을 new 로 교체. 없으면 None."""
    i = text.find(start)
    if i < 0:
        return None
    j = text.find(end, i)
    if j < 0:
        return None
    j += len(end)
    if text[j:j + 1] == "\n":
        j += 1
    return text[:i] + new + text[j:]


def restyle_text(text, entry):
    notes = []
    # 1) 공통 CSS 링크: 페이지 자체 스타일 뒤, archive-fix 블록 앞
    head = render_head(entry)
    t = _replace_block(text, HEAD_START, HEAD_END, head)
    if t is None:
        k = text.find(FIX_MARK)
        if k < 0:
            k = re.search(r"</head\s*>", text, re.I).start()
        t = text[:k] + head + text[k:]
        notes.append("공통 CSS 연결")
    elif t != text:
        notes.append("공통 CSS 연결 갱신")
    text = t
    # 2) 머리띠: <body> 바로 뒤 (맨 앞이 '본문 바로가기' 링크면 그 뒤)
    hdr = render_header(entry)
    t = _replace_block(text, HDR_START, HDR_END, hdr)
    if t is None:
        m = re.search(r"<body\b[^>]*>\s*", text, re.I)
        pos = m.end()
        skip = re.match(r"<a\b[^>]*href=[\"']#[^>]*>.*?</a>\s*", text[pos:], re.I | re.S)
        if skip:
            pos += skip.end()
        t = text[:pos] + hdr + text[pos:]
        notes.append("머리띠 추가")
    elif t != text:
        notes.append("머리띠 갱신")
    text = t
    # 3) 꼬리말: </body> 바로 앞
    ftr = render_footer(entry)
    t = _replace_block(text, "\n" + FTR_START, FTR_END, ftr)
    if t is None:
        t = _replace_block(text, FTR_START, FTR_END, ftr.lstrip("\n"))
    if t is None:
        k = text.lower().rfind("</body")
        t = text[:k] + ftr + text[k:]
        notes.append("꼬리말 추가")
    elif t != text:
        notes.append("꼬리말 갱신")
    return t, notes


def restyle_page(entry, path=None):
    path = path or os.path.join(ROOT, entry["file"])
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        old = f.read()
    if not re.search(r"<body\b", old, re.I) or not re.search(r"</head\s*>", old, re.I):
        warn(f"{entry['file']}: <head>/<body> 구조가 없어 공통 형식을 넣지 못했습니다.")
        return []
    new, notes = restyle_text(old, entry)
    if new != old:
        atomic_write(path, new, errors="surrogateescape")
    for a in (ASSET_PAGE_CSS, ASSET_TOKENS_CSS):
        if not os.path.isfile(os.path.join(ROOT, a)):
            warn(f"공통 파일이 없습니다: {a}")
    return notes


def strip_archive_blocks(text):
    """검사용: 아카이브가 넣은 블록을 빼고 원래 페이지 부분만 남김."""
    for a, b in ((HEAD_START, HEAD_END), (HDR_START, HDR_END), (FTR_START, FTR_END)):
        while True:
            t = _replace_block(text, a, b, "")
            if t is None or t == text:
                break
            text = t
    text = re.sub(r"<!-- archive-[\w-]+.*?-->\s*<style id=\"archive-[\w-]+\">.*?</style>", "", text, flags=re.S)
    return text


def style_lint(entry):
    """(필수 위반 목록, 권장 미충족 목록)"""
    path = os.path.join(ROOT, entry["file"])
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    req, rec = [], []
    if not re.search(r"<html\b[^>]*\blang=[\"']?ko", text, re.I):
        req.append('<html lang="ko"> 없음')
    if not re.search(r"<meta\b[^>]*charset=[\"']?utf-8", text, re.I):
        req.append("<meta charset=\"utf-8\"> 없음")
    if not re.search(r"<meta\b[^>]*name=[\"']?viewport[^>]*width=device-width", text, re.I):
        req.append("viewport(width=device-width) 없음")
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not m or not m.group(1).strip():
        req.append("<title> 비어 있음")
    own = strip_archive_blocks(text)
    n_h1 = len(re.findall(r"<h1[\s>]", own, re.I))
    if n_h1 != 1:
        req.append(f"<h1> 이 {n_h1}개 (정확히 1개여야 함)")
    for start, end, name, fn in ((HEAD_START, HEAD_END, "공통 CSS 연결", render_head),
                                 (HDR_START, HDR_END, "공통 머리띠", render_header),
                                 (FTR_START, FTR_END, "공통 꼬리말", render_footer)):
        i = text.find(start)
        if i < 0:
            req.append(f"{name} 없음 → --restyle")
            continue
        block = text[i:text.find(end, i) + len(end)]
        if block.strip() != fn(entry).strip():
            req.append(f"{name}이(가) 카탈로그와 다름 → --restyle")
    if MOBILE_MARK not in text:
        req.append("모바일 보정 CSS 없음 → --fix-mobile")
    ext = re.findall(r"<(?:script|img|iframe|video|audio|source|embed)\b[^>]*\bsrc=[\"']?(https?:)?//", own, re.I)
    ext += re.findall(r"<link\b(?=[^>]*rel=[\"']?(?:stylesheet|preload|icon|modulepreload))[^>]*href=[\"']?(https?:)?//", own, re.I)
    ext += re.findall(r"(?:@import|url\()\s*[\"']?(https?:)?//", own, re.I)
    if ext:
        req.append(f"외부 리소스 {len(ext)}개 (CDN·웹폰트·외부 이미지 금지, 오프라인 동작 필수)")
    # 권장
    if not re.search(r"<meta\b[^>]*name=[\"']?description", text, re.I):
        rec.append("<meta name=\"description\"> 권장")
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", own, re.S | re.I))
    missing = [v for v in ("--bg", "--ink", "--accent") if not re.search(re.escape(v) + r"\s*:", css)]
    if missing:
        rec.append(f"CSS 변수 {', '.join(missing)} 를 쓰면 공통 토큰이 자동 적용됨")
    small = [float(x) for x in re.findall(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", css)]
    tiny = [x for x in small if x < 12]
    if tiny:
        rec.append(f"12px 미만 font-size 선언 {len(tiny)}개 (꼬리표·라벨 외에는 피하기)")
    if len(re.findall(r"<h2[\s>]", own, re.I)) >= 4 and not re.search(r"<nav\b|class=[\"'][^\"']*toc", own, re.I):
        rec.append("절이 4개 이상이면 목차(nav) 권장")
    if not entry.get("source_url") and not re.search(r"출처|원문", own):
        rec.append("출처 표기(본문 끝 '출처' 문단 또는 --source-url) 권장")
    return req, rec


# ---------------------------------------------------------------- 카탈로그
def migrate(e):
    """예전 형식(원본 절대경로 'source')을 공개용 형식으로 바꾼다."""
    if "source" in e:
        src = e.pop("source")
        e.setdefault("source_name", os.path.basename(src))
        e.setdefault("source_path_sha256", path_hash(src))
    return e


def load_catalog():
    if not os.path.exists(CATALOG_JSON):
        return []
    try:
        with open(CATALOG_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        die(f"catalog.json 파싱 실패: {e}")
    if not isinstance(data, list):
        die("catalog.json 최상위는 배열(list)이어야 합니다.")
    return [migrate(e) if isinstance(e, dict) else e for e in data]


def sort_key(e):
    return (e.get("date", ""), e.get("added", ""))


def validate(entries):
    problems = []
    ids = set()
    for i, e in enumerate(entries):
        where = f"항목 #{i + 1} ({e.get('id', '?') if isinstance(e, dict) else '?'})"
        if not isinstance(e, dict):
            problems.append(f"{where}: 객체가 아님")
            continue
        for k in ("id", "title", "summary", "tags", "date", "file"):
            if k not in e:
                problems.append(f"{where}: '{k}' 필드 없음")
        if e.get("id") in ids:
            problems.append(f"{where}: id 중복")
        ids.add(e.get("id"))
        if not isinstance(e.get("tags", []), list):
            problems.append(f"{where}: tags는 배열이어야 함")
        if "date" in e and not DATE_RE.match(str(e["date"])):
            problems.append(f"{where}: date 형식은 YYYY-MM-DD")
        f = e.get("file")
        if f and not os.path.isfile(os.path.join(ROOT, f)):
            problems.append(f"{where}: 파일 없음 → {f}")
    return problems


def save_catalog(entries):
    entries.sort(key=sort_key, reverse=True)
    atomic_write(CATALOG_JSON, json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    build_js(entries)


def build_js(entries=None):
    if entries is None:
        entries = load_catalog()
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    js = (
        "/* 자동 생성 파일 — 직접 수정하지 마세요. catalog.json을 고친 뒤\n"
        "   `python3 add_page.py --rebuild` 를 실행하면 다시 만들어집니다. */\n"
        f"window.ARCHIVE_CATALOG = {payload};\n"
    )
    atomic_write(CATALOG_JS, js)


def git_commit(message, push=True):
    """아카이브 폴더가 git 저장소일 때 변경분을 커밋하고(원격이 있으면) push."""
    import subprocess

    def git(*args, check=True):
        return subprocess.run(["git", "-C", ROOT, *args], check=check, text=True, capture_output=True)

    try:
        if git("rev-parse", "--is-inside-work-tree", check=False).returncode != 0:
            warn("git 저장소가 아니어서 --commit 을 건너뜁니다.")
            return 1
        git("add", "-A", "--", "pages", "catalog.json", "catalog.js", "assets")
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            print("git: 커밋할 변경 사항 없음")
            return 0
        git("commit", "-m", message)
        h = git("rev-parse", "--short", "HEAD").stdout.strip()
        print(f"git: 커밋 {h}  {message}")
        if push and git("remote", check=False).stdout.strip():
            r = git("push", check=False)
            if r.returncode == 0:
                print("git: push 완료 (GitHub Pages 반영까지 1~2분)")
            else:
                warn("git push 실패 (커밋은 로컬에 남아 있음):\n" + (r.stderr or r.stdout).strip())
                return 1
        return 0
    except FileNotFoundError:
        warn("git 명령을 찾을 수 없습니다.")
        return 1
    except subprocess.CalledProcessError as e:
        warn(f"git 오류: {(e.stderr or e.stdout or '').strip()}")
        return 1


def slugify(stem):
    stem = nfc(stem).strip()
    stem = re.sub(r"\s+", "-", stem)
    stem = re.sub(r"[^\w\-]", "", stem, flags=re.UNICODE)  # 한글·영문·숫자·_·- 만
    stem = re.sub(r"-{2,}", "-", stem).strip("-_")
    return stem[:80] or "page"


def unique_filename(date, stem, ext):
    base = f"{date}-{stem}"
    name = f"{base}{ext}"
    n = 2
    while os.path.exists(os.path.join(PAGES_DIR, name)):
        name = f"{base}-{n}{ext}"
        n += 1
    return name


def new_id(entries, date):
    prefix = date.replace("-", "")
    used = {e.get("id") for e in entries}
    n = 1
    while f"{prefix}-{n:02d}" in used:
        n += 1
    return f"{prefix}-{n:02d}"


def parse_tags(s):
    out = []
    for t in re.split(r"[,，、]", s or ""):
        t = nfc(t).strip()
        if t and t not in out:
            out.append(t)
    return out


def html_title(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(200_000)
        m = re.search(r"<title[^>]*>(.*?)</title>", head, re.I | re.S)
        if m:
            import html
            return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    except OSError:
        pass
    return None


def select_entries(entries, which):
    if which in (None, "all"):
        return entries
    hit = [e for e in entries if e.get("id") == which]
    if not hit:
        die(f"id를 찾을 수 없습니다: {which}  (--list 로 확인)")
    return hit


# ---------------------------------------------------------------- 명령
def cmd_add(a):
    src = os.path.abspath(a.source)
    if not os.path.isfile(src):
        die(f"원본 파일이 없습니다: {src}")
    ext = os.path.splitext(src)[1].lower()
    if ext not in (".html", ".htm"):
        warn(f"HTML 파일이 아닌 것 같습니다 ({ext or '확장자 없음'}). 계속 진행합니다.")
        ext = ext or ".html"

    date = a.date or now_kst().date().isoformat()
    if not DATE_RE.match(date):
        die("--date 형식은 YYYY-MM-DD 입니다.")
    try:
        dt.date.fromisoformat(date)
    except ValueError:
        die(f"유효하지 않은 날짜: {date}")

    title = nfc(a.title or html_title(src) or os.path.splitext(os.path.basename(src))[0]).strip()
    if not a.title:
        warn(f"--title 이 없어 HTML <title>/파일명에서 가져왔습니다: {title}")
    summary = nfc(a.summary or "").strip()
    tags = parse_tags(a.tags)

    entries = load_catalog()
    known = {}
    for e in entries:
        for t in e.get("tags", []):
            known.setdefault(t.casefold(), t)
    for i, t in enumerate(tags):
        k = known.get(t.casefold())
        if k and k != t:
            warn(f"태그 '{t}' → 기존 표기 '{k}' 로 통일")
            tags[i] = k
    tags = list(dict.fromkeys(tags))

    digest, phash = sha256(src), path_hash(src)
    dups = []
    for e in entries:
        if e.get("source_sha256") == digest:
            dups.append(f"같은 내용의 파일이 이미 있음 → {e['id']} ({e['title']})")
        elif e.get("source_path_sha256") == phash:
            dups.append(f"같은 원본 경로가 이미 등록됨 → {e['id']} ({e['title']})")
        if nfc(e.get("title", "")).casefold() == title.casefold():
            dups.append(f"같은 제목이 이미 있음 → {e['id']}")
    if dups:
        for d in dups:
            print(("경고: " if a.force else "중복: ") + d, file=sys.stderr)
        if not a.force:
            die("중복으로 판단되어 추가하지 않았습니다. 그래도 추가하려면 --force 를 붙이세요.", 2)

    stem = slugify(a.name if a.name else os.path.splitext(os.path.basename(src))[0])
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", stem) or "page"
    fname = unique_filename(date, stem, ext)
    dest = os.path.join(PAGES_DIR, fname)

    if a.dry_run:
        print(f"[dry-run] {src} → pages/{fname}")
        return

    os.makedirs(PAGES_DIR, exist_ok=True)
    shutil.copy2(src, dest)  # 원본은 읽기만 함
    if sha256(dest) != digest:
        os.unlink(dest)
        die("복사본 검증(sha256) 실패")
    os.chmod(dest, 0o644)
    notes = [] if a.no_mobile else apply_mobile(dest)  # 복사본에만 적용

    entry = {
        "id": new_id(entries, date),
        "title": title,
        "summary": summary,
        "tags": tags,
        "date": date,
        "file": f"pages/{fname}",
        "added": now_kst().isoformat(timespec="seconds"),
        "source_name": os.path.basename(src),
        "source_sha256": digest,
        "source_path_sha256": phash,
    }
    if a.source_url:
        entry["source_url"] = a.source_url.strip()
    if a.tokens == "off":
        entry["tokens"] = False
    style_notes = [] if a.no_restyle else restyle_page(entry)
    entries.append(entry)
    save_catalog(entries)
    print(f"추가됨: {entry['id']}  {title}")
    print(f"  파일: {entry['file']}")
    print(f"  태그: {', '.join(tags) or '(없음)'}  날짜: {date}")
    print(f"  모바일 보정: {', '.join(notes) if notes else ('건너뜀 (--no-mobile)' if a.no_mobile else '이미 적용됨')}")
    print(f"  공통 형식: {', '.join(style_notes) if style_notes else ('건너뜀 (--no-restyle)' if a.no_restyle else '변경 없음')}")
    print(f"  총 {len(entries)}개 항목, catalog.js 재생성 완료")
    if not a.no_restyle:
        req, rec = style_lint(entry)
        for r in req:
            print(f"  형식 필수 ✗ {r}")
        for r in rec:
            print(f"  형식 권장 · {r}")
    if not a.no_check:
        mobile_check([dest])
    if a.commit:
        git_commit(f"페이지 추가: {title} ({entry['id']})", push=not a.no_push)


def cmd_rebuild(a):
    entries = load_catalog()
    problems = validate(entries)
    for p in problems:
        warn(p)
    known = {e.get("file") for e in entries}
    if os.path.isdir(PAGES_DIR):
        for n in sorted(os.listdir(PAGES_DIR)):
            if n.lower().endswith((".html", ".htm")) and f"pages/{n}" not in known:
                warn(f"catalog.json에 없는 파일: pages/{n}")
    save_catalog(entries)
    print(f"catalog.js 재생성 완료 ({len(entries)}개 항목{', 문제 ' + str(len(problems)) + '건' if problems else ''})")
    if a.commit:
        git_commit("카탈로그 재생성 (--rebuild)", push=not a.no_push)
    return 1 if problems else 0


def cmd_list(_a):
    entries = sorted(load_catalog(), key=sort_key, reverse=True)
    if not entries:
        print("(비어 있음)")
    for e in entries:
        print(f"{e['id']}  {e['date']}  {e['title']}  [{', '.join(e.get('tags', []))}]  {e['file']}")


def cmd_remove(a):
    entries = load_catalog()
    e = select_entries(entries, a.remove)[0]
    entries = [x for x in entries if x is not e]
    save_catalog(entries)
    print(f"카탈로그에서 제거: {e['id']}  {e['title']}")
    path = os.path.join(ROOT, e["file"])
    if a.delete_file:
        if os.path.isfile(path):
            os.unlink(path)
            print(f"  복사본 삭제: {e['file']}")
    else:
        print(f"  복사본은 남겨둠: {e['file']}  (함께 지우려면 --delete-file)")
    if a.commit:
        git_commit(f"페이지 제거: {e['title']} ({e['id']})", push=not a.no_push)


def cmd_fix_mobile(a):
    for e in select_entries(load_catalog(), a.fix_mobile):
        notes = apply_mobile(os.path.join(ROOT, e["file"]))
        print(f"{e['id']}  {e['file']}: {', '.join(notes) if notes else '이미 적용됨'}")
    if a.commit:
        git_commit("모바일 보정 적용 (--fix-mobile)", push=not a.no_push)


def cmd_restyle(a):
    for e in select_entries(load_catalog(), a.restyle):
        notes = restyle_page(e)
        print(f"{e['id']}  {e['file']}: {', '.join(notes) if notes else '변경 없음'}")
    if a.commit:
        git_commit("공통 형식 적용 (--restyle)", push=not a.no_push)


def cmd_check_style(a):
    entries = select_entries(load_catalog(), a.check_style)
    bad = 0
    for e in entries:
        req, rec = style_lint(e)
        mark = "✓" if not req else "✗"
        print(f"{mark} {e['id']}  {e['file']}")
        for r in req:
            print(f"    필수 ✗ {r}")
        for r in rec:
            print(f"    권장 · {r}")
        bad += bool(req)
    if not a.no_check:
        n = mobile_check([os.path.join(ROOT, e["file"]) for e in entries])
        bad += n or 0
    print("형식 검사 통과" if not bad else f"필수 항목 위반 {bad}건")
    return 1 if bad else 0


def cmd_edit(a):
    entries = load_catalog()
    e = select_entries(entries, a.edit)[0]
    changed = []
    if a.title:
        e["title"] = nfc(a.title).strip(); changed.append("title")
    if a.summary:
        e["summary"] = nfc(a.summary).strip(); changed.append("summary")
    if a.tags:
        e["tags"] = parse_tags(a.tags); changed.append("tags")
    if a.date:
        if not DATE_RE.match(a.date):
            die("--date 형식은 YYYY-MM-DD 입니다.")
        e["date"] = a.date; changed.append("date")
    if a.source_url is not None:
        if a.source_url.strip():
            e["source_url"] = a.source_url.strip()
        else:
            e.pop("source_url", None)
        changed.append("source_url")
    if a.tokens:
        if a.tokens == "off":
            e["tokens"] = False
        else:
            e.pop("tokens", None)
        changed.append("tokens")
    if not changed:
        die("바꿀 항목이 없습니다 (--title/--summary/--tags/--date/--source-url/--tokens).")
    save_catalog(entries)
    notes = restyle_page(e)
    print(f"수정: {e['id']}  ({', '.join(changed)})  공통 형식: {', '.join(notes) or '변경 없음'}")
    if a.commit:
        git_commit(f"항목 수정: {e['title']} ({e['id']})", push=not a.no_push)


def cmd_replace(a):
    """같은 id·같은 파일명(URL)을 유지한 채 보관본을 새 원본으로 교체하고 파이프라인을 다시 돌린다."""
    if not a.source:
        die("교체할 새 원본 경로가 필요합니다: --replace <id> <source.html>")
    src = os.path.abspath(a.source)
    if not os.path.isfile(src):
        die(f"원본 파일이 없습니다: {src}")
    entries = load_catalog()
    e = select_entries(entries, a.replace)[0]
    digest = sha256(src)
    if e.get("source_sha256") == digest and not a.force:
        die("보관본과 같은 원본입니다 (내용 해시 동일). 그래도 다시 돌리려면 --force.", 2)
    for o in entries:
        if o is not e and o.get("source_sha256") == digest and not a.force:
            die(f"다른 항목과 같은 내용입니다 → {o['id']} ({o['title']}). 그래도 하려면 --force.", 2)
    dest = os.path.join(ROOT, e["file"])
    old_fix = False
    if os.path.isfile(dest):
        with open(dest, encoding="utf-8", errors="replace") as f:
            old_fix = FIX_MARK in f.read()

    # 카탈로그 값 갱신 (주어진 것만)
    if a.title:
        e["title"] = nfc(a.title).strip()
    if a.summary:
        e["summary"] = nfc(a.summary).strip()
    if a.tags:
        e["tags"] = parse_tags(a.tags)
    if a.date:
        if not DATE_RE.match(a.date):
            die("--date 형식은 YYYY-MM-DD 입니다.")
        e["date"] = a.date
    if a.source_url is not None:
        if a.source_url.strip():
            e["source_url"] = a.source_url.strip()
        else:
            e.pop("source_url", None)
    if a.tokens:
        if a.tokens == "off":
            e["tokens"] = False
        else:
            e.pop("tokens", None)

    if a.dry_run:
        print(f"[dry-run] {src} → {e['file']} (id {e['id']} 유지)")
        return

    # 임시 파일에서 복사·검증·보정을 마친 뒤 한 번에 바꿔치기 (중간 실패 시 기존 보관본 유지)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(dest), prefix=".tmp-replace-", suffix=".html")
    os.close(fd)
    try:
        shutil.copyfile(src, tmp)  # 원본은 읽기만 함
        if sha256(tmp) != digest:
            die("복사본 검증(sha256) 실패")
        notes = [] if a.no_mobile else apply_mobile(tmp)
        style_notes = [] if a.no_restyle else restyle_page(e, tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

    e["source_name"] = os.path.basename(src)
    e["source_sha256"] = digest
    e["source_path_sha256"] = path_hash(src)
    e["updated"] = now_kst().isoformat(timespec="seconds")
    save_catalog(entries)
    print(f"교체됨: {e['id']}  {e['title']}  (파일·URL 유지: {e['file']})")
    print(f"  모바일 보정: {', '.join(notes) or ('건너뜀' if a.no_mobile else '이미 적용됨')}")
    print(f"  공통 형식: {', '.join(style_notes) or ('건너뜀' if a.no_restyle else '변경 없음')}")
    if old_fix:
        print("  참고: 이전 보관본의 archive-fix 블록은 옮기지 않았습니다. 필요하면 --check-style 결과를 보고 새로 넣으세요.")
    if not a.no_restyle:
        req, rec = style_lint(e)
        for r in req:
            print(f"  형식 필수 ✗ {r}")
        for r in rec:
            print(f"  형식 권장 · {r}")
    if not a.no_check:
        mobile_check([dest])
    if a.commit:
        git_commit(f"페이지 교체: {e['title']} ({e['id']})", push=not a.no_push)


def cmd_check(a):
    paths = [os.path.join(ROOT, e["file"]) for e in select_entries(load_catalog(), a.check)]
    if a.check in (None, "all"):
        paths.append(os.path.join(ROOT, "index.html"))
    n = mobile_check(paths)
    if n is None:
        return 2
    print("모바일 검사 통과" if n == 0 else f"모바일 문제 {n}건")
    return 1 if n else 0


def main():
    p = argparse.ArgumentParser(description="HTML 요약 페이지 아카이브 도구")
    p.add_argument("source", nargs="?", help="추가할 HTML 파일 경로 (원본은 수정하지 않음)")
    p.add_argument("--title", help="제목 (없으면 HTML <title> 사용)")
    p.add_argument("--summary", default="", help="한두 줄 요약")
    p.add_argument("--tags", default="", help="쉼표로 구분한 태그, 예: AI,소프트웨어,강연")
    p.add_argument("--date", help="YYYY-MM-DD (기본: 오늘, Asia/Seoul)")
    p.add_argument("--name", help="pages/ 안 파일명(확장자 제외). 기본: 원본 파일명")
    p.add_argument("--force", action="store_true", help="중복 경고를 무시하고 추가")
    p.add_argument("--dry-run", action="store_true", help="복사/기록 없이 결과만 출력")
    p.add_argument("--no-mobile", action="store_true", help="복사본에 모바일 보정(viewport·CSS)을 넣지 않음")
    p.add_argument("--no-check", action="store_true", help="추가 후 모바일 검사(Playwright)를 생략")
    p.add_argument("--rebuild", action="store_true", help="catalog.json 검증 후 catalog.js 재생성")
    p.add_argument("--list", action="store_true", help="항목 목록 출력")
    p.add_argument("--remove", metavar="ID", help="카탈로그에서 항목 제거")
    p.add_argument("--delete-file", action="store_true", help="--remove 시 pages/ 복사본도 삭제")
    p.add_argument("--check", nargs="?", const="all", metavar="ID|all", help="모바일 검사 (기본 all)")
    p.add_argument("--fix-mobile", nargs="?", const="all", metavar="ID|all", help="기존 페이지에 모바일 보정 주입")
    p.add_argument("--source-url", help="원문 주소 (머리띠·꼬리말에 '원문 ↗' 링크). --edit 에서 빈 문자열이면 삭제")
    p.add_argument("--tokens", choices=("on", "off"), help="공통 기본 토큰(archive-tokens.css) 적용 여부 (기본 on)")
    p.add_argument("--no-restyle", action="store_true", help="추가 시 공통 머리띠·꼬리말·CSS를 넣지 않음")
    p.add_argument("--restyle", nargs="?", const="all", metavar="ID|all", help="공통 형식 주입/갱신")
    p.add_argument("--check-style", nargs="?", const="all", metavar="ID|all", help="형식 표준 검사 (+모바일 검사)")
    p.add_argument("--edit", metavar="ID", help="카탈로그 항목 수정 후 공통 형식 갱신")
    p.add_argument("--replace", metavar="ID",
                   help="같은 id·파일명으로 보관본 교체: --replace <id> <새 source.html> [--summary ..]")
    p.add_argument("--commit", action="store_true",
                   help="작업 후 git add/commit, 원격(origin)이 있으면 push (추가·수정·삭제·재생성·보정)")
    p.add_argument("--no-push", action="store_true", help="--commit 시 push는 하지 않음")
    a = p.parse_args()

    if a.rebuild:
        sys.exit(cmd_rebuild(a))
    if a.list:
        return cmd_list(a)
    if a.remove:
        return cmd_remove(a)
    if a.fix_mobile:
        return cmd_fix_mobile(a)
    if a.restyle:
        return cmd_restyle(a)
    if a.check_style:
        sys.exit(cmd_check_style(a))
    if a.edit:
        return cmd_edit(a)
    if a.replace:
        return cmd_replace(a)
    if a.check:
        sys.exit(cmd_check(a))
    if not a.source:
        p.print_help()
        sys.exit(1)
    cmd_add(a)


if __name__ == "__main__":
    main()
