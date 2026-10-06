# 요약 아카이브

다른 어시스턴트가 만든 한국어 HTML 요약 페이지를 한곳에 모아 두는 **오프라인 정적 아카이브**입니다.
외부 CDN·폰트·스크립트를 쓰지 않아 인터넷 없이도, `index.html`을 더블클릭(`file://`)해도 그대로 동작합니다.

## 구성

```
archive/
├── index.html      목록 페이지 (검색·태그 필터·날짜 정렬)
├── catalog.json    항목 메타데이터 — 원본 데이터(source of truth)
├── catalog.js      catalog.json에서 자동 생성 (index.html이 <script>로 읽음, 직접 수정 금지)
├── add_page.py     추가/재생성/삭제 도구 (python3 표준 라이브러리만 사용)
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
  --date 2026-10-06
```

- 원본 파일은 **복사만** 하고 절대 수정하지 않습니다. 복사 후 sha256으로 검증합니다.
- 저장 이름: `pages/<날짜>-<원본파일명>.html` (같은 이름이 있으면 `-2`, `-3` …). `--name 이름`으로 바꿀 수 있습니다.
- `--date` 생략 시 오늘(Asia/Seoul), `--title` 생략 시 HTML `<title>`을 씁니다.
- 태그는 쉼표로 구분합니다. 대소문자만 다른 기존 태그가 있으면 기존 표기로 맞춥니다 (`ai` → `AI`).
- **중복 방지**: 같은 내용(해시)·같은 원본 경로·같은 제목이 이미 있으면 추가를 거부합니다. 그래도 넣으려면 `--force`.
- `--dry-run`: 실제로 복사하지 않고 결과만 미리 봅니다.
- 추가하면 `catalog.json`이 갱신되고 `catalog.js`가 자동으로 다시 만들어집니다.

## 그 밖의 명령

```bash
python3 add_page.py --list                    # 항목 목록 (id 확인)
python3 add_page.py --rebuild                 # catalog.json을 손으로 고친 뒤 검증 + catalog.js 재생성
python3 add_page.py --remove 20261006-01      # 카탈로그에서 제거 (복사본 파일은 남김)
python3 add_page.py --remove 20261006-01 --delete-file   # 복사본까지 삭제
```

### git 커밋/푸시 (`--commit`)

이 폴더는 git 저장소(GitHub `YgHnSIM/Archive`)입니다. 추가·`--rebuild`·`--remove` 명령에 `--commit`을 붙이면
작업 후 `pages/`, `catalog.json`, `catalog.js` 변경분을 `git add` → `git commit` 하고, 원격(origin)이 있으면 `git push`까지 합니다.

```bash
python3 add_page.py /경로/요약.html --title "제목" --summary "요약" --tags AI --commit
python3 add_page.py /경로/요약.html --title "제목" --commit --no-push   # 커밋만, push는 나중에
```

push가 실패해도 커밋은 로컬에 남아 있으니 나중에 `git push`로 올리면 됩니다.
`index.html`·`README.md`·`add_page.py` 자체를 고쳤을 때는 평소처럼 직접 `git commit` 하세요.

`--rebuild`는 필수 필드, 날짜 형식, id 중복, 파일 존재 여부를 검사하고, `pages/`에 있지만 카탈로그에 없는 파일도 알려 줍니다.

## catalog.json 항목 형식

```json
{
  "id": "20261006-01",
  "title": "이해의 종말: 좋은 추상화가 중요한 이유",
  "summary": "…",
  "tags": ["AI", "소프트웨어", "강연"],
  "date": "2026-10-06",
  "file": "pages/2026-10-06-좋은추상화_정리.html",
  "added": "2026-10-06T12:40:32+09:00",
  "source": "/workspace/abstraction/좋은추상화_정리.html",
  "source_sha256": "…"
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
