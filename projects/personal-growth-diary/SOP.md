# SOP.md — 개인 성장 일기 자동화 시스템

## 프로젝트 개요

자기 전 텔레그램 음성 대화로 일기를 기록하고, 목표 관리·격언·캘린더 최적화까지 연결하는 **개인 성장 자동화 시스템**.

---

## 기술 스택

| 역할 | 도구 |
|------|------|
| 자동화 허브 | n8n |
| 인터페이스 | Telegram Bot |
| STT | OpenAI Whisper |
| AI 대화·생성 | OpenAI GPT-4o |
| 데이터베이스 | Supabase (PostgreSQL) |
| 웹 앱 | Next.js (Railway 호스팅) |
| 일정 관리 | Google Calendar |

> **Notion·Google Sheets 미사용.** 일기·수치·목표 데이터 모두 Supabase 단일 DB로 관리.

---

## 전체 아키텍처

```
[Telegram Bot]
      ↓ 음성/명령어
[n8n 자동화]
      ↓ Supabase REST API
[Supabase DB] ←──────────────────→ [Web App (Next.js)]
      ↑                                     ↓ 목표 수정 시
[Google Calendar] ←─── n8n Webhook ←───────┘
```

### n8n ↔ Web 상호작용 방식

| 방향 | 방식 | 사용 시점 |
|------|------|----------|
| n8n → Supabase | HTTP Request (REST API) | 일기 저장, 목표 업데이트 |
| Web → Supabase | Supabase JS SDK (직접) | 일기 조회·수정, 목표 조회 |
| Web → n8n | HTTP Request → n8n Webhook URL | 웹에서 목표 변경 시 캘린더 재최적화 트리거 |

---

## Supabase DB 스키마

### `diaries` 테이블 (일기)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | uuid | PK |
| date | date | 일기 날짜 (unique) |
| tomorrow_priority | text | Step 1 답변 |
| todays_hardship | text | Step 2 답변 |
| gratitude | text | Step 3 답변 |
| day_summary | text | Step 4 답변 |
| todays_idea | text | Step 5 답변 |
| ai_draft | text | GPT-4o 생성 일기 초안 |
| mood_energy | int2 | 기분/에너지 (1~10) |
| sleep_hours | float4 | 수면 시간 |
| exercised | bool | 운동 여부 |
| goal_achievement | int2 | 목표 달성률 (0~100) |
| created_at | timestamptz | 생성 시각 |

### `goals` 테이블 (목표 관리)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | uuid | PK |
| title | text | 목표명 |
| level | text | `year` / `month` / `day` |
| period | text | 예: `2026`, `2026-03`, `2026-03-22` |
| status | text | `active` / `done` / `paused` |
| category | text | 건강 / 커리어 / 관계 / 재정 / 자기계발 / 기타 |
| description | text | 세부 내용 |
| created_at | timestamptz | 생성 시각 |
| updated_at | timestamptz | 수정 시각 |

### `diary_sessions` 테이블 (대화 세션)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| chat_id | text | PK (Telegram chat_id) |
| step | int2 | 현재 대화 단계 (1~6) |
| answers | jsonb | 각 단계 답변 누적 |
| metrics | jsonb | 수치 데이터 |
| updated_at | timestamptz | 마지막 업데이트 |

---

## 워크플로우 목록 (3개)

| 파일명 | 역할 | 트리거 |
|--------|------|--------|
| `01-telegram-bot.json` | 음성 일기 + 만다라트 목표 관리 | Telegram Webhook |
| `02-daily-quote.json` | 매일 격언 + AI 해설 전송 | 매일 오전 7시 스케줄 |
| `03-calendar-optimizer.json` | 목표 기반 빈 일정 자동 제안 | 매일 저녁 9시 스케줄 + n8n Webhook |

---

## WF-01 | Telegram Bot (음성 일기 + 목표 관리)

### 트리거
- Telegram Webhook (봇으로 메시지 수신 시 실행)

### 분기 로직 (Switch 노드)
```
Telegram Webhook 수신
    ↓
Switch
    ├── 음성 파일(voice) → [Voice Diary 흐름]
    └── 텍스트 "/goals" → [Mandala Goals 흐름]
```

---

### [Voice Diary 흐름]

#### 개요
사용자가 Telegram으로 음성 메시지를 보내면, AI가 순서대로 질문하며 일기를 완성한다.
대화 세션은 Supabase `diary_sessions` 테이블로 관리한다.

#### 대화 세션 관리
- 세션 저장소: Supabase `diary_sessions` 테이블
- 세션 키: `telegram_chat_id`
- 세션 데이터 구조:
```json
{
  "step": 1,
  "answers": {
    "tomorrow_priority": "",
    "todays_hardship": "",
    "gratitude": "",
    "day_summary": "",
    "todays_idea": ""
  },
  "metrics": {
    "mood_energy": null,
    "sleep_hours": null,
    "exercised": null,
    "goal_achievement": null
  }
}
```

#### 질문 순서 (총 6단계)

| Step | 질문 | 저장 필드 | 입력 형식 |
|------|------|----------|----------|
| 1 | "내일 가장 중요한 한 가지는?" | `tomorrow_priority` | 음성 |
| 2 | "오늘 힘들었거나 아쉬웠던 점은?" | `todays_hardship` | 음성 |
| 3 | "오늘 감사했던 일은?" | `gratitude` | 음성 |
| 4 | "오늘 하루를 한 마디로 표현하면?" | `day_summary` | 음성 |
| 5 | "오늘의 아이디어는?" | `todays_idea` | 음성 |
| 6 | 수치 입력 (아래 참고) | `metrics` | 텍스트 |

#### Step 6 수치 입력 방식
Bot이 아래 메시지를 전송하고, 사용자가 텍스트로 답변:
```
마지막으로 오늘의 수치를 입력해주세요!

1️⃣ 기분/에너지 점수 (1~10)
2️⃣ 수면 시간 (예: 7.5)
3️⃣ 운동 여부 (O / X)
4️⃣ 오늘 목표 달성률 (0~100%)

예시: 7 / 6.5 / O / 80
```
파싱: `/`로 split하여 각 필드에 저장.

#### 노드 흐름 (Voice Diary)
```
Telegram Webhook
    ↓
Switch (음성 vs 텍스트)
    ↓ [음성]
Download Voice File (Telegram API)
    ↓
OpenAI Whisper (STT → 텍스트 변환)
    ↓
Supabase GET diary_sessions (현재 step 확인)
    ↓
Save Answer to Session (현재 step 답변 → diary_sessions UPSERT)
    ↓
Increment Step
    ↓
Switch (다음 step이 있는가?)
    ├── step 1~5: Send Next Question (Telegram 질문 전송)
    ├── step 6: Send Metrics Request (수치 입력 요청 텍스트 전송)
    └── 완료: Finalize Diary
              ↓
         OpenAI GPT-4o (일기 초안 생성)
              ↓
         Supabase INSERT diaries (일기 저장)
              ↓
         Supabase DELETE diary_sessions (세션 정리)
              ↓
         Telegram (완료 메시지 + 웹 앱 링크 전송)
```

#### AI 일기 초안 생성 프롬프트
```
당신은 따뜻하고 성찰적인 일기 작가입니다.
아래 사용자의 답변을 바탕으로 자연스러운 일기 초안을 한국어로 작성해주세요.
200~300자 분량으로, 1인칭 서술 형식으로 작성하세요.

- 내일의 우선순위: {tomorrow_priority}
- 오늘의 어려움: {todays_hardship}
- 감사한 일: {gratitude}
- 오늘 하루 한 마디: {day_summary}
- 오늘의 아이디어: {todays_idea}
```

#### 에러 처리
| 상황 | 처리 방법 |
|------|----------|
| 음성 파일 다운로드 실패 | "음성 파일을 받지 못했어요. 다시 보내주세요." 전송 |
| Whisper STT 실패 | "음성 인식에 실패했어요. 다시 보내주세요." 전송 |
| 수치 입력 파싱 실패 | "입력 형식이 맞지 않아요. 예시: 7 / 6.5 / O / 80" 전송 |
| Supabase 저장 실패 | Telegram에 에러 알림 전송, 재시도 1회 |

---

### [Mandala Goals 흐름]

#### 개요
`/goals` 명령어로 만다라트 목표를 조회·설정·업데이트한다.
데이터는 Supabase `goals` 테이블에 저장되며, 웹 앱에서도 동일하게 조회·수정 가능.

#### 지원 명령어
| 명령어 | 기능 |
|--------|------|
| `/goals` | 현재 목표 조회 (연/월/일) |
| `/goals set year` | 연간 목표 설정 |
| `/goals set month` | 월간 목표 설정 |
| `/goals set day` | 오늘 목표 설정 |
| `/goals update` | 목표 달성 상태 업데이트 |

#### 노드 흐름 (Mandala Goals)
```
Telegram Webhook (/goals 명령어)
    ↓
Parse Command (set year / set month / set day / update / 조회)
    ↓
Switch (명령어 종류)
    ├── 조회: Supabase GET goals → Format → Telegram 전송
    ├── set: Telegram 질문 → 답변 수신 → Supabase INSERT goals
    └── update: Supabase PATCH goals (status 변경) → 확인 메시지 전송
```

---

## WF-02 | Daily Quote (매일 격언)

### 트리거
- Schedule: 매일 오전 7:00 (KST)

### 노드 흐름
```
Schedule Trigger (07:00)
    ↓
OpenAI GPT-4o (격언 생성)
    ↓
Telegram (메시지 전송)
```

### GPT-4o 격언 생성 프롬프트
```
세계적으로 유명한 인물의 격언을 하나 선택하고,
아래 형식으로 한국어로 작성해주세요.

형식:
💬 "{격언 원문}"
— {인물 이름}

📖 오늘의 해설:
{이 격언이 오늘 하루를 시작하는 사람에게 주는 의미를 2~3문장으로 따뜻하게 풀어주세요.}
```

### 출력 예시
```
💬 "성공은 준비와 기회가 만날 때 이루어진다."
— 세네카

📖 오늘의 해설:
아무리 기회가 찾아와도 준비되지 않으면 잡을 수 없습니다.
오늘 하루 작은 준비 하나가 언젠가의 기회를 만드는 씨앗이 됩니다.
오늘도 조금씩 쌓아가는 하루 되세요. 🌱
```

---

## WF-03 | Calendar Optimizer (일정 최적화)

### 트리거
- Schedule: 매일 저녁 21:00 (KST)
- n8n Webhook: 웹 앱에서 목표 수정 시 수동 트리거 가능

### 노드 흐름
```
Schedule Trigger (21:00) 또는 Webhook (웹 앱 목표 변경)
    ↓
Google Calendar (내일 일정 조회)
    ↓
Supabase GET goals (이번 달 active 목표 조회)
    ↓
OpenAI GPT-4o (빈 시간 분석 + 목표 기반 일정 제안)
    ↓
Telegram (제안 메시지 전송 + 승인 버튼)
    ↓
[사용자 승인 시]
Google Calendar (일정 자동 등록)
    ↓
Telegram (등록 완료 메시지)
```

### 일정 제안 GPT-4o 프롬프트
```
사용자의 내일 일정과 이번 달 목표를 분석하여,
빈 시간에 넣을 수 있는 목표 달성 활동을 제안해주세요.

내일 기존 일정:
{calendar_events}

이번 달 목표:
{monthly_goals}

규칙:
- 30분~2시간 단위로 제안
- 무리하지 않는 현실적인 계획
- 제안은 최대 3개
- 각 제안에 목표와의 연관성 명시

출력 형식 (JSON):
[
  {
    "title": "일정 제목",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "goal": "연관 목표",
    "reason": "추천 이유 한 줄"
  }
]
```

### Telegram 승인 메시지 형식
```
📅 내일 일정 최적화 제안이에요!

⏰ 09:00~10:00 | 독서 30분
   → 목표: 자기계발 / "매일 독서하기"와 연결돼요.

⏰ 19:00~20:00 | 운동 (홈트)
   → 목표: 건강 / 이번 달 운동 목표 달성에 도움이 돼요.

✅ 수락하려면 아래 버튼을 누르세요.
[✅ 모두 수락] [❌ 건너뛰기]
```

---

## 웹 앱 명세 (Next.js)

### 페이지 구성

| 경로 | 기능 |
|------|------|
| `/` | 일기 목록 (달력 뷰) |
| `/diary/:date` | 일기 상세 조회 + 수정 |
| `/goals` | 만다라트 목표 (9×9 시각화) |
| `/stats` | 수치 차트 (기분/수면/운동/달성률 트렌드) |

### 웹 → n8n 상호작용

| 상황 | 처리 방식 |
|------|----------|
| 일기 수정 | Supabase JS SDK로 직접 PATCH |
| 목표 추가·수정 | Supabase JS SDK로 직접 UPSERT → n8n Webhook 호출 (캘린더 재최적화) |
| 목표 삭제 | Supabase JS SDK로 직접 DELETE |

### 만다라트 시각화 구조
```
[핵심 목표]
    ↓
[8개 주요 목표 (카테고리)]
    ↓
[각 주요 목표별 8개 세부 목표]
```
웹에서 9×9 그리드로 렌더링. 클릭 시 상세 편집 모달.

---

## 공통 설정

### Telegram Bot 설정
- Bot Token: Telegram BotFather에서 발급
- Webhook URL: `https://primary-production-90c7.up.railway.app/webhook/{token}`
- 대화 언어: 한국어

### n8n Credential 목록
| Credential | 사용 워크플로우 |
|-----------|--------------|
| Telegram Bot API | WF-01, WF-02, WF-03 |
| OpenAI API | WF-01, WF-02, WF-03 |
| Supabase API (HTTP Header Auth) | WF-01, WF-03 |
| Google Calendar OAuth2 | WF-03 |

### Supabase 연동 방식 (n8n)
- 노드: HTTP Request
- Base URL: `https://{project-id}.supabase.co/rest/v1`
- Headers:
  - `apikey`: Supabase anon key
  - `Authorization`: `Bearer {service_role_key}`
  - `Content-Type`: `application/json`

---

## 제작 순서

1. Supabase 프로젝트 생성 + 테이블 3개 생성 (`diaries`, `goals`, `diary_sessions`)
2. Telegram Bot 생성 (BotFather)
3. Google Calendar API 연동 (OAuth2)
4. n8n Credential 등록
5. WF-01 Telegram Bot 워크플로우 제작 및 테스트
6. WF-02 Daily Quote 워크플로우 제작 및 테스트
7. WF-03 Calendar Optimizer 워크플로우 제작 및 테스트
8. Next.js 웹 앱 제작 + Railway 배포
