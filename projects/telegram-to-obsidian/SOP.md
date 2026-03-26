# SOP: 텔레그램 → 옵시디언 저장 봇

---

## [워크플로우 이름]
텔레그램 → 옵시디언 저장 봇 (Telegram to Obsidian via OneDrive)

---

## [목적]
텔레그램으로 수신된 메시지(텍스트/사진/영상/파일)를 GPT-4o-mini로 제목·태그를 생성한 뒤,
Microsoft OneDrive를 통해 옵시디언 볼트에 `.md` 파일로 자동 저장한다.

---

## [환경 정보]

| 항목 | 값 |
|------|-----|
| n8n 인스턴스 | Railway 클라우드 (`https://primary-production-90c7.up.railway.app`) |
| OneDrive 볼트 경로 | `옵시디언/Startegy_Investment` |
| OneDrive 공유 링크 | `https://1drv.ms/f/c/f984d66bb3ffded7/...` |
| 파일 저장 방식 | n8n → OneDrive API → 로컬 PC 자동 동기화 → Obsidian 인식 |
| 날짜 기준 | KST (Asia/Seoul, UTC+9) |

> **사전 준비**: Railway n8n에서 직접 로컬 파일 쓰기가 불가하므로 OneDrive를 중간 저장소로 사용.
> OneDrive가 PC와 자동 동기화되어 Obsidian이 파일을 인식한다.

---

## [처리 메시지 타입]

| 타입 | 트리거 조건 | 첨부파일 처리 |
|------|------------|-------------|
| `text` | 일반 텍스트 메시지 | 없음 |
| `photo` | 이미지 메시지 | `.jpg` OneDrive 업로드 |
| `video` | 동영상 메시지 | 썸네일 `.jpg`만 업로드 (원본 영상 X) |
| `document` | 파일 첨부 | 원본 파일 OneDrive 업로드 (최대 20MB) |

> **허용 사용자 필터**: `ALLOWED_USERS` 환경변수(텔레그램 user_id 목록). 미설정 시 전체 허용.

---

## [전체 구조]

```
Telegram Webhook
    ↓
[STEP 1] 허용 사용자 확인 → 미허용 시 "접근 권한이 없습니다." 응답 후 종료
    ↓
[STEP 2] 메시지 타입 분기 (Switch: text / photo / video / document)
    ↓
[STEP 3] 첨부파일 다운로드 → OneDrive attachments 폴더 업로드 (photo/video/document만)
    ↓
[STEP 4] GPT-4o-mini로 제목 + 태그 생성
    ↓
[STEP 5] URL 포함 여부 확인 → HTTP Request로 링크 미리보기 생성 (조건부)
    ↓
[STEP 6] .md 파일 내용 조립 (Code 노드)
    ↓
[STEP 7] OneDrive에 날짜 폴더 경로로 .md 파일 업로드
    ↓
[STEP 8] Telegram sendMessage "저장 완료: {파일명}"
```

---

## [처리 로직 상세]

### STEP 1. 허용 사용자 확인

- **조건**: `$json.message.from.id` 값이 `ALLOWED_USERS`(쉼표 구분 문자열)에 포함되어 있는지 확인
- **미허용 시**: Telegram `sendMessage` → `"접근 권한이 없습니다."` → 워크플로우 종료
- **`ALLOWED_USERS` 미설정 시**: 전체 허용 (빈 문자열 체크)

---

### STEP 2. 메시지 타입 분기 (Switch 노드)

| 조건 | 브랜치 |
|------|--------|
| `$json.message.photo` 존재 | photo |
| `$json.message.video` 존재 | video |
| `$json.message.document` 존재 | document |
| 그 외 (fallback) | text |

> Switch 노드 조건 순서: photo → video → document → text(fallback)

---

### STEP 3. 첨부파일 다운로드 및 OneDrive 업로드

**적용 대상**: photo / video / document 브랜치

#### 3-1. Telegram 파일 다운로드
```
HTTP Request: GET https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}
→ 응답에서 file_path 추출
→ HTTP Request: GET https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}
→ 바이너리 데이터 취득
```

| 타입 | file_id 소스 | 저장 파일명 |
|------|-------------|-----------|
| photo | `photo[-1].file_id` (최대 해상도) | `{file_unique_id}.jpg` |
| video | `video.thumb.file_id` (썸네일) | `{file_unique_id}_thumb.jpg` |
| document | `document.file_id` | `document.file_name` (원본 파일명) |

> **video.thumb 부재 시**: 썸네일 다운로드 생략, .md 파일에 `🎬 썸네일 없음` 텍스트만 기재

> **20MB 초과 시**: 파일 다운로드 생략, .md 파일에 `⚠️ 파일 크기 초과로 저장 불가` 기재

#### 3-2. OneDrive 업로드
- **업로드 경로**: `옵시디언/Startegy_Investment/Telegram/attachments/{파일명}`
- **노드**: Microsoft OneDrive 노드 (OAuth2 인증)
- **실패 시**: 파일 첨부 없이 텍스트만 저장 진행 (전체 중단 X)

---

### STEP 4. GPT-4o-mini 제목/태그 생성

- **모델**: `gpt-4o-mini`
- **호출 방식**: HTTP Request 노드 → OpenAI Chat Completions API
- **입력**: 메시지 본문 또는 캡션 (최대 800자)

**프롬프트** (user 메시지만):
```
아래 텔레그램 메시지를 분석해서 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

규칙:
- title: 파일명으로 쓸 한국어 제목 (15자 이내, 공백 없이 언더스코어 사용, 특수문자 제외)
- tags: 핵심 키워드 3~5개 (한국어 단어)

응답 예시:
{"title": "삼성전자_실적분석", "tags": ["삼성전자", "실적", "주식", "투자"]}

메시지:
{메시지 내용 최대 800자}
```

**파싱 규칙**:
- JSON에서 `title`, `tags` 추출
- 마크다운 코드블록(` ```json ``` `)으로 감싸진 경우 제거 후 파싱
- **title 정제**: `\/:*?"<>|` 제거, 공백→`_`, 최대 40자

**Fallback** (API 실패 시):
```json
{"title": "메모", "tags": ["telegram"]}
```

---

### STEP 5. URL 링크 미리보기 (조건부)

**조건**: 메시지 본문에 `https://` 포함 여부 확인 (IF 노드)

**처리**:
```
본문에서 https://... URL 추출 (정규식)
→ HTTP Request: GET {URL}
   - timeout: 3000ms
   - User-Agent: Mozilla/5.0
→ HTML에서 파싱:
   - <title> 태그
   - <meta name="description"> 또는 <meta property="og:description">
```

**실패 시**: 해당 섹션 생략하고 전체 플로우 계속 진행

---

### STEP 6. .md 파일 내용 조립 (Code 노드)

**날짜 처리** (KST 변환):
```javascript
const now = new Date();
const kstDate = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = kstDate.toISOString().split('T')[0]; // YYYY-MM-DD
const dateTimeStr = kstDate.toISOString().replace('Z', '+09:00');
```

**파일명 생성**:
```
{YYYY-MM-DD}_{title}.md
예: 2026-03-25_삼성전자_실적분석.md
```

**파일명 충돌 방지**: 동일 파일 존재 시 `_1`, `_2` 접미사 추가

---

### STEP 7. OneDrive .md 파일 업로드

- **저장 경로**: `옵시디언/Startegy_Investment/Telegram/{YYYY-MM-DD}/{파일명}.md`
- **노드**: Microsoft OneDrive 노드 (OAuth2 인증)
- **실패 시**: Telegram으로 `"저장 실패: {에러 내용}"` 전송

---

### STEP 8. Telegram 응답

- **노드**: Telegram 노드 (`sendMessage`)
- **메시지**: `"저장 완료\n{파일명}"`

---

## [.md 파일 포맷]

### 텍스트 메시지
```markdown
---
date: 2026-03-25T14:30:00+09:00
source: telegram
type: text
from: "홍길동 (@honggildong)"
tags:
  - 삼성전자
  - 실적
  - 주식
---

메시지 본문 전체

## 링크 미리보기

**제목**: 삼성전자 실적 발표
**설명**: 1분기 영업이익 6조원 달성
**URL**: https://example.com/news/123
```

### 사진 메시지
```markdown
---
date: 2026-03-25T14:30:00+09:00
source: telegram
type: photo
from: "홍길동 (@honggildong)"
tags:
  - 차트
  - 주식
---

![[attachments/AbCdEf123.jpg]]

캡션 텍스트 (있을 경우)
```

### 영상 메시지
```markdown
---
date: 2026-03-25T14:30:00+09:00
source: telegram
type: video
from: "홍길동 (@honggildong)"
tags:
  - 영상
---

![[attachments/XyZ789_thumb.jpg]]

🎬 영상 길이: 120초

캡션 텍스트 (있을 경우)
```

> 썸네일 없는 경우: `![[...]]` 대신 `🎬 썸네일 없음` 텍스트 삽입

### 문서/파일 메시지
```markdown
---
date: 2026-03-25T14:30:00+09:00
source: telegram
type: document
from: "홍길동 (@honggildong)"
tags:
  - 보고서
---

[[attachments/report.pdf|report.pdf]]

캡션 텍스트 (있을 경우)
```

---

## [환경변수 및 Credential 설정]

| 변수명 | 설명 | 관리 방식 |
|--------|------|---------|
| `BOT_TOKEN` | 텔레그램 봇 토큰 | n8n Variables |
| `OPENAI_API_KEY` | OpenAI API 키 | n8n Credentials (HTTP Header Auth) |
| `ALLOWED_USERS` | 허용 user_id 목록 (쉼표 구분, 빈 문자열이면 전체 허용) | n8n Variables |
| OneDrive OAuth2 | Microsoft Graph API 인증 | n8n Credentials (OAuth2) |

> **OneDrive OAuth2 설정**: Microsoft Azure Portal에서 앱 등록 후 Client ID / Client Secret 발급 필요.
> 권한 범위: `Files.ReadWrite`, `offline_access`

---

## [에러 처리 규칙]

| 노드 | 실패 시 처리 |
|------|------------|
| 허용 사용자 확인 | "접근 권한이 없습니다." 응답 후 종료 |
| GPT-4o-mini API | fallback: `title="메모"`, `tags=["telegram"]` |
| URL 링크 미리보기 | 해당 섹션 생략, 전체 플로우 계속 진행 |
| 첨부파일 다운로드 | 파일 첨부 없이 텍스트만 저장 진행 |
| OneDrive 업로드 (.md) | Telegram으로 "저장 실패: {에러}" 전송 |

---

## [사용 서비스]

| 서비스 | 역할 | 연동 방식 |
|--------|------|---------|
| Telegram Bot API | Webhook 수신 + 응답 전송 | Bot Token |
| OpenAI API | GPT-4o-mini 제목/태그 생성 | API Key (HTTP Header Auth) |
| Microsoft OneDrive | .md 및 첨부파일 저장 | OAuth2 (Microsoft Graph) |
| HTTP Request | URL 링크 미리보기 HTML 파싱 | 없음 |

---

## [OneDrive 폴더 구조]

```
OneDrive/
└── 옵시디언/
    └── Startegy_Investment/
        └── Telegram/
            ├── attachments/          ← 사진·영상 썸네일·문서 파일
            ├── 2026-03-25/
            │   ├── 2026-03-25_삼성전자_실적분석.md
            │   └── 2026-03-25_메모.md
            └── 2026-03-26/
                └── 2026-03-26_차트_분석.md
```

---

## [워크플로우 파일 구조]

```
projects/telegram-to-obsidian/
├── SOP.md
└── workflows/
    └── telegram-to-obsidian.json
```

---

## [사전 준비 체크리스트]

- [ ] Telegram Bot 생성 및 BOT_TOKEN 확인 (BotFather)
- [ ] 기존 Python 봇 Webhook 제거 후 n8n Webhook으로 교체
  - `https://api.telegram.org/bot{TOKEN}/deleteWebhook`
  - `https://api.telegram.org/bot{TOKEN}/setWebhook?url={n8n_url}`
- [ ] Microsoft Azure Portal 앱 등록 → Client ID / Secret 발급
- [ ] n8n에 OneDrive OAuth2 Credential 등록
- [ ] n8n Variables에 `BOT_TOKEN`, `ALLOWED_USERS` 등록
- [ ] OpenAI API Key n8n Credential 등록
