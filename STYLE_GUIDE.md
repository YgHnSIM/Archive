# 요약 페이지 형식 표준 (최소 공통 규격)

**대상:** 요약 HTML 페이지를 만드는 비서실장
**기준 형식:** 첫 페이지 `pages/2026-10-06-좋은추상화.html`
**목적:** 페이지마다 구성은 자유롭게 두되, 아카이브 안에서 **한 가족처럼** 보이게 하는 것. 전면 재디자인이 아닙니다.

검사: `python3 add_page.py --check-style` (필수 위반이 있으면 실패, 권장은 안내만)

---

## 1. 필수 (지켜야 함)

| # | 항목 | 누가 |
|---|------|------|
| R1 | `<html lang="ko">`, `<meta charset="utf-8">`, 비어 있지 않은 `<title>` | 작성자 |
| R2 | `<meta name="viewport" content="width=device-width, initial-scale=1">` | 없으면 도구가 넣음 |
| R3 | 페이지 제목 `<h1>`은 **정확히 1개** | 작성자 |
| R4 | **한 파일로 완결**: CDN·웹폰트·외부 스크립트/이미지 금지. 이미지는 data URI로 넣기 (외부로 가는 `<a>` 링크는 괜찮음) | 작성자 |
| R5 | 모바일(360~390px)에서 **가로 스크롤 없음**, 읽는 글 **16px 이상** (라벨·꼬리표·각주는 13px 이상) | 작성자 (도구가 보정·검사) |
| R6 | 공통 머리띠 `← 아카이브 · 날짜 · #태그 · 원문↗` | **도구가 자동으로 넣음** |
| R7 | 공통 꼬리말 (아카이브 표시, 제목, 날짜, 태그, 원문, 목록으로/맨 위로) | **도구가 자동으로 넣음** |
| R8 | 공통 CSS 연결: `assets/archive-page.css` (머리띠·꼬리말), `assets/archive-tokens.css` (기본 토큰) | **도구가 자동으로 넣음** |

R6~R8은 `add_page.py`가 카탈로그(제목·날짜·태그·`source_url`)를 읽어 **복사본에** 넣습니다. 작성자는 원본에 따로 만들 필요가 없습니다.

## 2. 기본 토큰 (첫 페이지에서 뽑은 값)

`archive-tokens.css`가 페이지 자체 스타일 **뒤에서** 아래 값을 덮어씁니다. 그래서 페이지가 **같은 이름의 CSS 변수**를 쓰면 색이 자동으로 맞춰집니다.

| 토큰 | 값 | 용도 |
|------|----|------|
| `--bg` | `#faf8f3` | 바탕 (따뜻한 미색) |
| `--ink` | `#1f2328` | 본문 글자 |
| `--muted` | `#5b6470` | 보조 글자 |
| `--line` | `#e6e1d6` | 구분선·테두리 |
| `--accent` / `--accent-soft` | `#c8553d` / `#fbeee9` | 강조 (테라코타) / 강조 바탕 |
| 링크 | `#4a6b8a` | 청회색 |
| `--radius` | `14px` | 카드 모서리 |
| 글꼴 | `"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Noto Sans CJK KR","Malgun Gothic","Gothic A1",system-ui,sans-serif` | 본문 |
| 본문 | 17px / 줄간격 1.75 (640px 이하 16px), `word-break:keep-all` | |

**제목 크기 (권장, 토큰으로 강제하지 않음):**
- h1: `clamp(28px, 4.4vw, 44px)`, 줄간격 1.25
- h2: `clamp(23px, 3vw, 30px)`
- h3: 19px

**본문 최대 폭:** 1180px (목차 포함)

**의미 색은 페이지 고유로 둡니다.** 예: 보호/적용, 좋음/나쁨. 이름을 `--good`, `--bad`, `--protect`처럼 따로 지으세요. `--accent`를 의미 색으로 쓰지 마세요.

## 3. 권장 (첫 페이지의 형식)

1. **머리:** 꼬리표(eyebrow, 강조색 알약) → `<h1>` → 한두 줄 리드 문단 → (선택) 발표자·원문 정보 카드
2. **절 제목:** 번호 배지(둥근 사각, 진한 색) + h2 + 회색 부제 한 줄
3. **목차:** 절이 4개 이상이면 `<nav>`. 데스크톱은 왼쪽 고정, 모바일은 상단 가로 스크롤이나 접기
4. **구성요소:** 카드(흰 바탕, `--line` 테두리, 14px 모서리), 인용(왼쪽 강조색 띠), 콜아웃(옅은 바탕), 표는 모바일에서 카드형이나 가로 스크롤
5. **맺음:** 본문 끝에 출처 문단 하나 ("무엇을 바탕으로 정리했는지, 원문에 없는 내용은 넣지 않았는지")
6. `<meta name="description">`에 한 줄 요약
7. 12px 미만 글자는 쓰지 않기

## 4. 페이지 전용 보정 (`archive-fix`)

자동 보정으로 부족할 때만 **아카이브 복사본** `</head>` 앞에 아래 블록을 손으로 넣습니다.
- 예: 차가운 회색 하드코딩, 작은 글씨, 다른 제목 크기
- 본문 내용과 레이아웃은 바꾸지 않습니다
- `--restyle`은 이 블록을 건드리지 않습니다

```html
<!-- archive-fix: 이 페이지 전용 보정 — 이유 한 줄 -->
<style id="archive-fix"> … </style>
```

## 5. 작성자 체크리스트 (페이지 하나 만들 때)

- [ ] lang·charset·title·viewport, h1 하나
- [ ] 외부 리소스 없음 (이미지는 data URI)
- [ ] 색은 `--bg / --ink / --muted / --line / --accent` 변수로 (의미 색은 별도 이름)
- [ ] 390px에서 가로 스크롤 없고 본문 16px 이상
- [ ] 태그는 **[공통태깅규칙.md](file:///workspace/tagging_rules/공통태깅규칙.md)**(v2.0) 준수 (`[분야 1~2개] + [주제 1~2개] + [인물 0~1개] + [형식 1개]`, 3~5개, 공백·특수문자 금지)
- [ ] 원문이 웹에 있으면 추가할 때 `--source-url` 지정
- [ ] 추가 후 `python3 add_page.py --check-style <id>` 통과

## 6. 복습 3종 컴포넌트 표준 명세 (`.flips` / `.cloze` / `#quiz`)

아카이브 요약 페이지 하단에는 본문 내용 인출(Active Recall)을 돕는 필수 복습 섹션(`<section class="sec" id="rv">`)을 구성합니다. 외부 의존성(CDN, 외부 라이브러리) 없이 순수 CSS와 인라인 바닐라 JS로만 동작해야 합니다.

### 6.1 복습 컴포넌트 표준 스타일 (CSS)

```css
/* 복습 컴포넌트 표준 스타일 (.flips / .cloze / #quiz) */
.rv-h{font-size:19px;margin:22px 0 6px}
.flips{display:grid;grid-template-columns:1fr;gap:8px;margin:10px 0}
@media(min-width:640px){.flips{grid-template-columns:1fr 1fr}}
.flip{font:inherit;text-align:left;width:100%;border:1.5px solid var(--line,#e6e1d6);background:#fdfcf9;border-radius:12px;padding:10px 14px;cursor:pointer;color:var(--ink,#1f2328);min-height:64px}
.flip b{display:block;font-size:17px}
.flip .m{display:none;font-size:16px;line-height:1.6;margin-top:4px}
.flip .hint{font-size:13px;color:var(--muted,#5b6470)}
.flip[aria-expanded="true"]{border-color:var(--new,#3d5f80);background:var(--new-soft,#eaf0f6)}
.flip[aria-expanded="true"] .m{display:block}
.flip[aria-expanded="true"] .hint{display:none}
.cloze{list-style:none;margin:10px 0;padding:0}
.cloze li{border:1px solid var(--line,#e6e1d6);border-radius:12px;padding:10px 14px;margin:8px 0;background:#fdfcf9;font-size:16px;line-height:1.8}
.blank{font:inherit;font-size:16px;border:0;border-bottom:2px dashed var(--accent,#c8553d);background:var(--accent-soft,#fbeee9);color:var(--accent,#c8553d);border-radius:6px 6px 0 0;padding:0 8px;cursor:pointer;min-width:4.5em}
.blank.shown{border-bottom-style:solid;background:var(--new-soft,#eaf0f6);color:var(--new,#3d5f80);font-weight:700}
.rv-tools{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.rv-tools button{font:inherit;font-size:15px;border:1px solid var(--line,#e6e1d6);background:#fff;border-radius:10px;padding:6px 12px;cursor:pointer;color:var(--link,#4a6b8a)}
.q{border:1px solid var(--line,#e6e1d6);border-radius:12px;padding:12px 14px;margin:10px 0;background:#fdfcf9}
.q fieldset{border:0;margin:0;padding:0}
.q legend{font-weight:700;padding:0;margin:0 0 8px;font-size:16.5px}
.q button{display:block;width:100%;text-align:left;font:inherit;font-size:16px;border:1.5px solid var(--line,#e6e1d6);background:#fff;border-radius:10px;padding:8px 12px;margin:6px 0;cursor:pointer;color:var(--ink,#1f2328)}
.q button.right{border-color:#2f6b45;background:#e6f1ea}
.q button.wrong{border-color:#a2452f;background:#fbeee9}
.q button[disabled]{cursor:default;opacity:1}
.q .ex{margin:8px 0 0;font-size:16px;padding:8px 10px;border-radius:8px;background:var(--new-soft,#eaf0f6)}
.score{font-size:17px;font-weight:800;margin:10px 0 0}
```

### 6.2 복습 섹션 표준 HTML 구조

`<main>` 내부 하단, `<section class="sources">` 바로 위에 배치합니다:

```html
<section class="sec" id="rv">
  <div class="sec-head"><span class="sec-num">✔</span><div><h2>복습</h2><p class="sub">본문 내용만으로 만든 암기·이해 점검</p></div></div>

  <h3 class="rv-h">핵심 용어 카드</h3>
  <p class="muted">카드를 누르면 뜻이 나옵니다.</p>
  <div class="flips">
    <button type="button" class="flip" aria-expanded="false"><b>용어 1</b><span class="hint">뜻 보기</span><span class="m">핵심 정의 1~2문장.</span></button>
    <!-- 총 6~10개 .flip 버튼 -->
  </div>
  <div class="rv-tools"><button type="button" data-all="flip">모두 뒤집기</button><button type="button" data-reset="flip">모두 접기</button></div>

  <h3 class="rv-h">빈칸 채우기</h3>
  <p class="muted">빈칸을 누르면 답이 나옵니다.</p>
  <ol class="cloze">
    <li>핵심 문장에서 <button type="button" class="blank" data-a="정답어" aria-label="빈칸, 눌러서 답 보기">?</button>가 중요합니다.</li>
    <!-- 총 5~8개 li 문항 -->
  </ol>
  <div class="rv-tools"><button type="button" data-all="blank">답 모두 보기</button><button type="button" data-reset="blank">빈칸 다시 가리기</button></div>

  <h3 class="rv-h">5문항 퀴즈</h3>
  <div id="quiz">
    <!-- data-a 값은 정답 버튼의 0-기반 인덱스(0, 1, 2 중 하나) -->
    <div class="q" data-a="1">
      <fieldset>
        <legend class="qt">1. 질문 내용?</legend>
        <button type="button">오답 보기 1</button>
        <button type="button">정답 보기 2</button>
        <button type="button">오답 보기 3</button>
      </fieldset>
      <p class="ex" hidden aria-live="polite" data-e="정답 해설 문장."></p>
    </div>
    <!-- 총 5개 .q 블록 -->
    <p class="score" id="score" aria-live="polite">점수: 0 / 5</p>
    <div class="rv-tools"><button type="button" id="qreset">다시 풀기</button></div>
  </div>
</section>
```

### 6.3 복습 섹션 표준 제어 스크립트 (바닐라 JS)

`</body>` 직전에 삽입합니다:

```html
<script>(function(){
function $$(q){return [].slice.call(document.querySelectorAll(q))}
$$('.flip').forEach(function(b){b.onclick=function(){b.setAttribute('aria-expanded',b.getAttribute('aria-expanded')==='true'?'false':'true')}});
function show(b){b.textContent=b.dataset.a;b.classList.add('shown');b.setAttribute('aria-label','답: '+b.dataset.a)}
function hide(b){b.textContent='?';b.classList.remove('shown');b.setAttribute('aria-label','빈칸, 눌러서 답 보기')}
$$('.blank').forEach(function(b){b.onclick=function(){show(b)}});
$$('[data-all]').forEach(function(t){t.onclick=function(){if(t.dataset.all==='flip')$$('.flip').forEach(function(b){b.setAttribute('aria-expanded','true')});else $$('.blank').forEach(show)}});
$$('[data-reset]').forEach(function(t){t.onclick=function(){if(t.dataset.reset==='flip')$$('.flip').forEach(function(b){b.setAttribute('aria-expanded','false')});else $$('.blank').forEach(hide)}});
var sc=0,done=0,qs=$$('#quiz .q'),tot=qs.length||5;
function upd(){var el=document.getElementById('score');if(el)el.textContent='점수: '+sc+' / '+tot+(done===tot?' (끝)':'')}
qs.forEach(function(q){var bs=[].slice.call(q.querySelectorAll('fieldset button')),ex=q.querySelector('.ex');
bs.forEach(function(b,i){b.onclick=function(){var a=+q.dataset.a,ok=i===a;bs.forEach(function(x){x.disabled=true});if(bs[a])bs[a].classList.add('right');if(!ok)b.classList.add('wrong');
if(ex){ex.hidden=false;ex.textContent=(ok?'맞았습니다. ':'아쉽습니다. ')+ex.dataset.e;}if(ok)sc++;done++;upd();}})});
var qr=document.getElementById('qreset');
if(qr)qr.onclick=function(){sc=0;done=0;qs.forEach(function(q){q.querySelectorAll('fieldset button').forEach(function(x){x.disabled=false;x.className=''});var ex=q.querySelector('.ex');if(ex){ex.hidden=true;ex.textContent=''}});upd()};
})();</script>
```
