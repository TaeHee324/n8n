# Telegram to Obsidian — 자동 메모 저장 봇

텔레그램으로 보낸 메시지(텍스트/사진/영상/파일)를 GPT로 제목·태그를 생성하고,
OneDrive를 통해 Obsidian 볼트에 `.md` 파일로 자동 저장하는 n8n 워크플로우입니다.

---

## 어떻게 작동하나요?

```
텔레그램에서 메시지 전송
        ↓
허용된 사용자인지 확인
        ↓
첨부파일 있으면 → Telegram API로 다운로드 → OneDrive 업로드
        ↓
GPT-4o-mini로 제목·태그 자동 생성
        ↓
URL 포함 시 → 링크 미리보기 자동 추출 (title, description)
        ↓
Obsidian frontmatter 형식으로 .md 파일 조립
        ↓
OneDrive에 날짜별 폴더로 저장
        ↓
텔레그램으로 "저장 완료" 응답
```

**결과물 예시** (`2026-03-26_이란의_아랍에미리트_공격.md`):
```markdown
---
date: 2026-03-26T09:44:00+09:00
source: telegram
type: text
from: "홍길동 (@honggildong)"
tags:
  - 이란
  - 아랍에미리트
  - 국제정세
---

이란이 아랍에미리트를 공격했다는 소식...

## 링크 미리보기

**제목**: 이란, 아랍에미리트 공격 축소 발표
**설명**: 이란 외무부는 공격 규모를 ...
**URL**: https://example.com/news/123
```

---

## 지원 메시지 타입

| 타입 | 처리 방식 |
|------|---------|
| 텍스트 | 본문 그대로 저장 |
| 사진 | 최고 해상도 `.jpg` → OneDrive 업로드 → `.md`에 `![[]]` 삽입 |
| 동영상 | 썸네일 `.jpg`만 업로드 + 영상 길이 기록 |
| 파일 | 원본 파일 업로드 + `.md`에 링크 삽입 |

---

## 사전 준비

| 항목 | 설명 |
|------|------|
| n8n 인스턴스 | self-hosted 또는 n8n Cloud |
| Telegram Bot | BotFather에서 봇 생성 후 토큰 발급 |
| OpenAI API Key | `gpt-4o-mini` 사용 (분류·제목·태그) |
| Microsoft OneDrive | Azure Portal 앱 등록 → OAuth2 인증 필요 |
| Obsidian | OneDrive 동기화 폴더를 볼트로 지정 |

---

## 설치 방법

### 1. 워크플로우 Import

1. n8n 좌측 메뉴 → **Workflows** → **Import from file**
2. `workflows/telegram-to-obsidian.json` 선택

### 2. Credential 등록

n8n → **Credentials** → **Add Credential**

| Credential 타입 | 사용 노드 |
|----------------|---------|
| Telegram API | Telegram Trigger, Send No Access, Send Success |
| OpenAI API (HTTP Header Auth) | Generate Title Tags |
| Microsoft OneDrive OAuth2 | Upload Attachment, Upload MD to OneDrive |

> **OneDrive OAuth2 설정**: Azure Portal → 앱 등록 → API 권한 `Files.ReadWrite` + `offline_access` 추가

### 3. n8n Variables 등록

n8n → **Settings** → **Variables**

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `BOT_TOKEN` | 텔레그램 봇 토큰 | `1234567890:AAF...` |
| `ALLOWED_USERS` | 허용할 텔레그램 user_id (쉼표 구분) | `123456789,987654321` |

> `ALLOWED_USERS`를 빈 문자열로 두면 누구나 사용 가능

### 4. OneDrive 경로 수정

`Upload Attachment` 노드와 `Upload MD to OneDrive` 노드의 URL에서
`옵시디언/Startegy_Investment` 부분을 본인의 Obsidian 볼트 경로로 교체하세요.

### 5. Telegram Webhook 연결

n8n에서 `Telegram Trigger` 노드를 활성화하면 자동으로 Webhook이 등록됩니다.
기존에 Python 봇 등 다른 Webhook이 있으면 먼저 제거하세요:
```
https://api.telegram.org/bot{TOKEN}/deleteWebhook
```

---

## OneDrive 폴더 구조

```
OneDrive/
└── 옵시디언/
    └── Startegy_Investment/
        └── Telegram/
            ├── attachments/          ← 사진·썸네일·파일
            ├── 2026-03-25/
            │   └── 2026-03-25_삼성전자_실적분석.md
            └── 2026-03-26/
                └── 2026-03-26_이란_아랍에미리트_공격.md
```

---

## 에러 처리

| 상황 | 동작 |
|------|------|
| 허용되지 않은 사용자 | "접근 권한이 없습니다." 응답 후 종료 |
| GPT API 실패 | 제목 `메모`, 태그 `["telegram"]`로 대체 |
| 첨부파일 다운로드 실패 | 텍스트만 저장하고 계속 진행 |
| URL 미리보기 실패 | 해당 섹션 생략하고 계속 진행 |

---

## 사용 서비스 및 비용

| 서비스 | 역할 | 비용 |
|--------|------|------|
| Telegram Bot API | Webhook 수신 + 응답 | 무료 |
| OpenAI API (gpt-4o-mini) | 제목·태그 생성 | 유료 (매우 저렴) |
| Microsoft OneDrive | 파일 저장 | 무료 (5GB) |
| n8n | 워크플로우 실행 | self-hosted 무료 |

> 메시지 1건당 OpenAI 비용: 약 $0.0001 미만 (gpt-4o-mini 기준)

---

## 이 프로젝트에서 배운 것들

> AI 개발자·자동화 전문가로 성장하기 위해 이 프로젝트를 통해 얻은 실전 인사이트

### 1. AI는 "대화 상대"가 아니라 "변환 함수"다

GPT를 챗봇으로만 생각하면 활용 범위가 좁아진다.
이 프로젝트에서 GPT는 **텍스트 → JSON(제목+태그)** 변환 함수로 쓰였다.
AI를 `input → structured output`의 도구로 볼 때 자동화의 가능성이 폭발적으로 넓어진다.

```
// AI를 변환 함수로 쓰는 패턴
prompt: "아래 텍스트를 분석해서 JSON으로만 응답: {\"title\": ..., \"tags\": [...]}"
→ 파싱 가능한 구조화된 출력
```

### 2. 좋은 자동화는 "실패를 허용"한다

완벽한 성공보다 **우아한 실패(graceful degradation)** 가 더 중요하다.
- 첨부파일 다운로드 실패 → 텍스트만 저장하고 계속 진행
- GPT API 실패 → 기본값으로 대체
- URL 미리보기 실패 → 해당 섹션만 건너뜀

파이프라인의 한 단계가 실패해도 전체가 멈추지 않도록 설계하는 것이 자동화의 핵심이다.

### 3. 플랫폼 제약을 창의적으로 우회한다

n8n이 Railway 클라우드에서 실행되므로 로컬 파일 시스템에 직접 쓸 수 없다.
해결책: **n8n → OneDrive API → OneDrive 로컬 동기화 → Obsidian 인식**
제약을 제약으로 보지 않고 "어떤 중간 저장소를 쓸 수 있는가"로 재정의했다.

### 4. API 연동의 99%는 인증과 포맷이다

기능 구현보다 **OAuth2 설정, API 키 관리, 요청 포맷** 맞추는 데 더 많은 시간이 걸린다.
특히 배웠던 것:
- Microsoft Graph API URL에 한글이 있으면 반드시 URL 인코딩 필요
- Telegram 메시지에 `_`(언더스코어)가 있으면 Parse Mode에 따라 마크다운으로 해석됨
- n8n의 `$vars`, `$json`, `$('노드명').first().json` 데이터 참조 패턴

### 5. 디버깅은 노드 단위로 한다

전체 플로우를 한 번에 실행하지 말고, **의심되는 노드 하나만 테스트**한다.
n8n의 "노드 개별 실행" 기능은 이를 위한 핵심 도구다.
에러 메시지 전문을 읽는 습관 — `Bad Request: can't parse entities` 같은 메시지가
정확히 무엇을 의미하는지 파악하는 능력이 자동화 전문가의 핵심 역량이다.

### 6. 시크릿은 절대 코드에 넣지 않는다

`BOT_TOKEN`, `API_KEY`, `SUPABASE_KEY` 같은 값을 코드에 하드코딩하면
git push 한 번으로 GitHub 전체에 노출된다.
**n8n Variables / Credentials** 기능을 쓰거나, 코드에는 반드시 플레이스홀더(`YOUR_API_KEY`)를 넣자.

### 7. 워크플로우는 글쓰기처럼 설계한다

좋은 자동화 워크플로우는 좋은 글처럼 **흐름이 자연스럽고 읽기 쉬워야 한다**.
- 각 노드에 명확한 이름 (`Check Access`, `Generate Title Tags`)
- 분기가 생기면 true/false의 의미를 명확히 (허용 사용자인가? → true: 계속, false: 거절)
- 복잡한 로직은 Code 노드에 주석 포함

### 8. AI 시대의 지식 관리 = 구조화된 캡처

이 봇의 진짜 가치는 **"나중에 찾을 수 있는 형태로 저장"**하는 것이다.
단순히 텔레그램에 링크를 저장하는 것과,
`2026-03-26_이란_아랍에미리트_공격.md`로 태그와 함께 저장하는 것은 전혀 다르다.
AI를 활용한 자동 태깅과 제목 생성이 "나중의 나"를 위한 인덱스를 만든다.

---

## 파일 구조

```
projects/telegram-to-obsidian/
├── README.md              ← 이 파일
├── SOP.md                 ← 워크플로우 상세 설계 문서
├── build_workflow.py      ← 워크플로우 JSON 생성 스크립트
├── patch_workflow.py      ← n8n API를 통한 워크플로우 패치 스크립트
└── workflows/
    └── telegram-to-obsidian.json  ← n8n 워크플로우 파일
```
