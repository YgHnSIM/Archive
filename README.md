# 요약 아카이브

다른 어시스턴트가 만든 한국어 HTML 요약 페이지를 한곳에 모아 두는 **정적 아카이브**입니다.

- 공개 사이트: **https://yghnsim.github.io/Archive/** (GitHub Pages, `main` 브랜치 루트에서 자동 배포)
- 외부 CDN·폰트·스크립트를 쓰지 않아 인터넷 없이도, `index.html`을 더블클릭(`file://`)해도 그대로 동작합니다.
- 모든 페이지는 모바일(360~390px 폭)에서 가로 스크롤 없이 읽히도록 보정·검사합니다.
- 페이지마다 공통 머리띠·꼬리말·기본 토큰을 넣어 형식을 맞춥니다 → **[STYLE_GUIDE.md](STYLE_GUIDE.md)**

## 구성

```
archive/
├── index.html      목록 페이지 (검색·태그 필터·날짜 정렬)
├── catalog.json    항목 메타데이터 — 원본 데이터(source of truth)
├── catalog.js      catalog.json에서 자동 생성 (index.html이 <script>로 읽음, 직접 수정 금지)
├── add_page.py     추가/수정/삭제/재생성/형식 적용 도구 (python3 표준 라이브러리만 사용)
├── STYLE_GUIDE.md  페이지 형식 표준 (필수/권장)
├── assets/
│   ├── archive-page.css    공통 머리띠·꼬리말 스타일
│   └── archive-tokens.css  공통 기본 토큰 (첫 페이지 기준 색·글꼴·본문 크기)
├── .nojekyll       GitHub Pages가 Jekyll 처리를 하지 않도록 (한글 파일명 그대로 제공)
├── pages/          보관된 HTML 페이지 복사본
└── preview/        미리보기 스크린샷
```

> `file://`에서는 브라우저가 `fetch('catalog.json')`을 막기 때문에, 같은 내용을 `catalog.js`(`window.ARCHIVE_CATALOG = [...]`)로 만들어 읽습니다.

## 새 페이지 추가

```bash
cd /workspace/archive
python3 add_page.py /경로/요약.html \
  --title "제목" \
  --summary "한두 줄 요약" \
  --tags AI,소프트웨어,강연 \
  --date 2026-10-06 \
  --source-url https://원문주소   # 선택: 머리띠·꼬리말에 '원문 ↗' 링크
```

- 원본 파일은 **복사만** 하고 절대 수정하지 않습니다. 복사 후 sha256으로 검증합니다.
- 복사본에는 **모바일 보정**이 자동으로 들어갑니다 (아래 "모바일 최적화" 참고). 끄려면 `--no-mobile`.
- 복사본에는 **공통 형식**(머리띠·꼬리말·공통 CSS)도 자동으로 들어가고, 형식 검사 결과를 보여 줍니다 (아래 "공통 형식" 참고). 끄려면 `--no-restyle`.
- 저장 이름: `pages/<날짜>-<원본파일명>.html` (같은 이름이 있으면 `-2`, `-3` …). `--name 이름`으로 바꿀 수 있습니다.
- `--date` 생략 시 오늘(Asia/Seoul), `--title` 생략 시 HTML `<title>`을 씁니다.
- 태그는 쉼표로 구분합니다. 대소문자만 다른 기존 태그가 있으면 기존 표기로 맞춥니다 (`ai` → `AI`).
- **중복 방지**: 같은 내용(해시)·같은 원본 경로·같은 제목이 이미 있으면 추가를 거부합니다. 그래도 넣으려면 `--force`.
- `--dry-run`: 실제로 복사하지 않고 결과만 미리 봅니다.
- 추가하면 `catalog.json`이 갱신되고 `catalog.js`가 자동으로 다시 만들어집니다.

## 페이지 교체 (`--replace`) — 같은 id·같은 주소 유지

검수본 등으로 내용을 바꿀 때 씁니다. 공개 주소(`pages/…html`)와 id가 그대로라 기존 링크가 깨지지 않습니다.

```bash
python3 add_page.py --replace 20261006-02 /경로/새버전.html \
  --summary "새 요약" [--title …] [--tags …] [--date …] [--source-url …] [--commit]
```

- 원본은 읽기만 합니다. 임시 파일에서 복사·검증·보정을 모두 마친 뒤 보관본을 한 번에 바꿔치기합니다(중간에 실패하면 기존 보관본 유지).
- 다시 실행하는 것:
  - 모바일 보정 (viewport·CSS)
  - 공통 머리띠·꼬리말·CSS (`--restyle`)
  - 형식 검사
  - 390/360px 모바일 검사
- 카탈로그 갱신:
  - `source_sha256`(내용 해시)와 `source_name` 갱신
  - `updated`(교체 시각) 추가
  - 지정한 필드만 바뀌고 `added`는 유지
- **이전 보관본의 `archive-fix` 블록은 옮기지 않습니다.** 예전 페이지에 맞춘 보정이었기 때문입니다. `--check-style` 결과를 보고 필요할 때만 새로 넣으세요.
- 이미 보관된 것과 내용이 같으면 거부합니다(다른 항목과 같아도 거부). 그래도 하려면 `--force`.
- `--dry-run`으로 미리 보기.

## 그 밖의 명령

```bash
python3 add_page.py --list                    # 항목 목록 (id 확인)
python3 add_page.py --rebuild                 # catalog.json을 손으로 고친 뒤 검증 + catalog.js 재생성
python3 add_page.py --remove 20261006-01      # 카탈로그에서 제거 (복사본 파일은 남김)
python3 add_page.py --remove 20261006-01 --delete-file   # 복사본까지 삭제
```

### 공통 형식 (머리띠·꼬리말·기본 토큰)

규칙은 [STYLE_GUIDE.md](STYLE_GUIDE.md)에 있습니다. 도구는 **복사본에** 표식 주석 사이로 세 가지를 넣거나 갱신합니다. 여러 번 실행해도 안전합니다.

| 표식 | 위치 | 내용 |
|------|------|------|
| `<!-- archive-head:start … end -->` | `</head>` 앞 (`archive-fix` 블록보다 앞) | `../assets/archive-page.css`, `../assets/archive-tokens.css` 연결 |
| `<!-- archive-header:start … end -->` | `<body>` 바로 뒤 | `← 요약 아카이브`, 제목(데스크톱), 날짜, #태그(누르면 목록이 그 태그로 걸러짐), 원문 ↗ |
| `<!-- archive-footer:start … end -->` | `</body>` 앞 | 아카이브 표시, 제목, 날짜, 태그, 원문, 목록으로/맨 위로 |

내용은 `catalog.json`에서 가져오므로, 제목·태그·원문 주소를 바꾸면 `--edit`가 머리띠·꼬리말도 함께 고칩니다.
상대 경로(`../`)라서 `file://`로 열어도, GitHub Pages에서도 똑같이 동작합니다.

```bash
python3 add_page.py --restyle all                  # 전체 페이지에 공통 형식 적용/갱신
python3 add_page.py --check-style                  # 형식 표준 검사 (+ 390/360px 모바일 검사)
python3 add_page.py --check-style 20261006-02 --no-check   # 정적 검사만
python3 add_page.py --edit 20261006-02 --source-url https://… # 항목 수정 → 머리띠·꼬리말 자동 갱신
python3 add_page.py --edit 20261006-02 --tokens off  # 이 페이지만 공통 토큰(색·글꼴) 적용 안 함
```

`--check-style`의 **필수** 항목:
- lang·charset·title·viewport
- h1이 1개
- 공통 머리띠·꼬리말·CSS가 있고 카탈로그와 일치
- 모바일 보정 CSS
- 외부 리소스 없음
- 모바일 가로 넘침 없음, 본문 16px 이상

**권장** 항목(안내만): description, 공통 CSS 변수 사용, 12px 미만 글자, 목차, 출처 표기.

자동 보정으로 부족한 부분은 복사본에 `<!-- archive-fix -->` 블록을 손으로 넣어 보정합니다(STYLE_GUIDE 4절). 지금 두 페이지에 모두 들어 있습니다.

### git 커밋/푸시 (`--commit`)

이 폴더는 git 저장소(GitHub `YgHnSIM/Archive`)입니다. 추가·`--rebuild`·`--remove` 명령에 `--commit`을 붙이면
작업 후 `pages/`, `catalog.json`, `catalog.js` 변경분을 `git add` → `git commit` 하고, 원격(origin)이 있으면 `git push`까지 합니다.

```bash
python3 add_page.py /경로/요약.html --title "제목" --summary "요약" --tags AI --commit
python3 add_page.py /경로/요약.html --title "제목" --commit --no-push   # 커밋만, push는 나중에
```

push하면 1~2분 뒤 공개 사이트에 반영됩니다. push가 실패해도 커밋은 로컬에 남아 있으니 나중에 `git push`로 올리면 됩니다.
`index.html`·`README.md`·`add_page.py`·`STYLE_GUIDE.md` 자체를 고쳤을 때는 평소처럼 직접 `git commit` 하세요.

### 모바일 최적화

페이지를 추가하면 `pages/` 안의 **복사본에만** 다음을 자동으로 넣습니다 (본문 내용은 건드리지 않음).

1. `<meta name="viewport" content="width=device-width, initial-scale=1">` — 없으면 추가, `width=device-width`가 아니면 교체
2. `<!-- archive-mobile-css v1 -->` 주석이 붙은 작은 `<style id="archive-mobile-css">` 블록 — `</head>` 바로 앞
   - 이미지·영상·SVG·iframe `max-width:100%`
   - 640px 이하에서 표(`table`)와 코드 블록(`pre`)은 자기 상자 안에서 가로 스크롤, 긴 단어·URL 줄바꿈
   - 모든 규칙을 `:where()`로 감싸 명시도 0 → 원래 페이지 스타일과 겹치면 **항상 원래 스타일이 우선** (데스크톱 화면은 그대로)
   - 주석 표식이 있으면 다시 넣지 않으므로 여러 번 실행해도 안전

추가 직후 Playwright가 설치되어 있으면 390px·360px 폭으로 열어 **가로 넘침, 화면 밖 요소, viewport, 본문 글자 크기(16px 이상)** 를 검사합니다 (`--no-check`로 생략). Playwright가 없으면 경고만 내고 넘어갑니다.

```bash
python3 add_page.py --check            # 전체 페이지 + index.html 모바일 검사
python3 add_page.py --check 20261006-01
python3 add_page.py --fix-mobile all   # 예전에 추가한 페이지에 보정 주입
```

자동 보정으로 부족한 페이지(작은 글씨, 좁은 버튼 등)는 해당 복사본 `</head>` 앞에 `<!-- archive-fix -->` 블록을 손으로 추가합니다.
예: `pages/2026-10-06-좋은추상화.html`에는 캡션·목록 글자를 16px로, 용어 카드의 "바로가기" 링크 터치 영역을 44px로 키우는 블록이 들어 있습니다.

> Playwright 설치: `pip install --user playwright` (브라우저는 `/usr/bin/google-chrome` 등 시스템 Chrome을 자동으로 사용, 없으면 `python3 -m playwright install chromium`)

### 공개 저장소와 개인정보

`catalog.json`/`catalog.js`는 공개 사이트에 그대로 올라가므로 원본의 **전체 경로는 저장하지 않습니다.**
파일명(`source_name`)과 내용 해시(`source_sha256`), 경로 해시(`source_path_sha256`)만 남기며, 중복 감지는 이 해시들로 합니다.

`--rebuild`는 필수 필드, 날짜 형식, id 중복, 파일 존재 여부를 검사하고, `pages/`에 있지만 카탈로그에 없는 파일도 알려 줍니다.

## catalog.json 항목 형식

```json
{
  "id": "20261006-01",
  "title": "이해의 종말: 좋은 추상화가 중요한 이유",
  "summary": "…",
  "tags": ["AI", "소프트웨어", "강연"],
  "date": "2026-10-06",
  "file": "pages/2026-10-06-좋은추상화.html",
  "added": "2026-10-06T12:40:32+09:00",
  "source_name": "좋은추상화_정리.html",
  "source_sha256": "…",
  "source_path_sha256": "…",
  "source_url": "https://… (선택)",
  "updated": "2026-10-06T13:32:00+09:00",  // (--replace 했을 때만)
  "tokens": false            // (선택) 공통 토큰을 빼고 싶을 때만
}
```

## 목록 페이지 사용법

- **검색**: 제목·요약·태그에서 찾습니다. 대소문자 구분 없음, 띄어쓰기로 여러 단어를 넣으면 모두 포함된 항목만 보여 줍니다. `Esc`로 지우기.
- **태그**: 칩을 눌러 거릅니다. 여러 개 고르면 모두 가진 항목만(AND) 남고, `전체`를 누르면 초기화됩니다. 카드 안의 태그를 눌러도 됩니다.
- **정렬**: `↓ 최신순` / `↑ 오래된순` 버튼으로 전환 (기본 최신순).
- 검색·필터 상태는 주소의 `#` 뒤에 저장되어, 페이지를 열었다 돌아와도 유지됩니다.
- 시스템 설정에 따라 라이트/다크 모드가 자동 적용됩니다.

## 주의

- 보관할 HTML이 옆에 있는 이미지/CSS를 상대 경로로 참조한다면 그 파일도 `pages/` 안에 같은 구조로 함께 복사해야 합니다(도구는 HTML 파일 하나만 복사합니다). 이미지가 data URI로 내장된 단일 파일이라면 신경 쓰지 않아도 됩니다.
