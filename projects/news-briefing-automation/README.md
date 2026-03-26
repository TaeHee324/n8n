# 뉴스 브리핑 자동화 (n8n Workflow)

경제·증시 뉴스를 매일 자동으로 수집·분류·요약하여 텔레그램으로 전송하는 n8n 워크플로우입니다.

<img width="2800" height="847" alt="image" src="https://github.com/user-attachments/assets/4746dbba-3878-4c73-9808-a4968b81144a" />

---

## 주요 기능

- **4개 소스 병렬 수집**: 연합뉴스(경제·세계), CNBC, Yahoo Finance RSS
- **AI 3단계 분석**: 국가 분류 → 주제 분류 → 한국 증시 영향도 점수
- **중복 제거**: Google Sheets 아카이브와 비교해 신규 기사만 처리
- **AI 요약**: GPT-4o로 기사 본문 크롤링 후 한국어 요약
- **텔레그램 전송**: 국가별(미국/중국/한국/기타) 브리핑 + 시장 데이터(주요 지수, M7, 매크로)
- **실시간 속보 알림**: 연합뉴스 [속보], [특징주], [외환] 태그 기사를 5분 간격으로 감지

---

## 전체 구조

```
[트리거: 매일 07:30 UTC / 수동]
        ↓
[뉴스 수집 — 4소스 병렬]
연합뉴스 세계·경제 / CNBC / Yahoo Finance RSS
        ↓
[정규화 → 시간 필터(15시간) → 속보·영상·쇼츠 제거]
        ↓
[중복 제거 — Google Sheets 아카이브 비교]
        ↓
[AI ①: 국가 분류] — gpt-4o-mini
미국 / 중국 / 한국 / 기타
        ↓
[AI ②: 주제 분류] — gpt-4o-mini
정치/외교 / 통화/경제 / 산업/종목
        ↓
[AI ③: 한국 증시 영향도 점수] — gpt-4o-mini
relevance(1~10) × urgency(1~10) = score
        ↓
[국가+주제별 Switch → 상위 N건 선별]
미국(3건) / 중국(1건) / 한국(3건) / 기타(1건)
        ↓
[본문 크롤링 — 소스별 CSS Selector]
연합뉴스 / CNBC / Yahoo Finance
        ↓
[AI ④: 요약 생성] — gpt-4o
한국어 2~3문장, 수치·고유명사 포함
        ↓
[Google Sheets 아카이빙]
        ↓
[시장 데이터 조회] — Yahoo Finance API
다우 / S&P500 / 나스닥 / M7 / WTI / 미10년물 / 달러-원
        ↓
[텔레그램 전송 — MarkdownV2]

[속보 서브플로우 — 별도 트리거]
연합뉴스 RSS 5분 폴링 → [속보]/[특징주]/[외환] 감지 → 텔레그램 즉시 발송
```

---

## 사전 준비

| 항목 | 설명 |
|------|------|
| n8n 인스턴스 | self-hosted 또는 n8n Cloud |
| OpenAI API Key | gpt-4o-mini (분류·점수), gpt-4o (요약) 사용 |
| Google Sheets | OAuth2 연동 + 아카이브 시트 생성 필요 |
| Telegram Bot | BotFather에서 봇 생성 후 토큰 발급 |

---

## 설치 방법

### 1. 워크플로우 Import

1. n8n 좌측 메뉴 → **Workflows** → **Import from file**
2. `workflows/news-briefing-automation.json` 파일 선택

### 2. Credential 등록

n8n 좌측 메뉴 → **Credentials** → **Add Credential**

| Credential 타입 | 연결할 노드 |
|-----------------|------------|
| OpenAI API | AI Country Classifier, AI subject Classifier, AI Scoring, AI Summarizer |
| Google Sheets OAuth2 | Read Archive URLs, Archive To Sheets1 |
| Telegram API | Send Telegram, 텔레그램 전송, 텔레그램 속보 알림 |

### 3. Google Sheets 설정

1. Google Sheets에서 새 스프레드시트 생성
2. 시트 이름을 `뉴스 아카이브`로 설정
3. 1행에 헤더 추가: `date` / `title` / `url` / `source` / `country` / `subject` / `score`
4. 스프레드시트 ID를 복사 (URL의 `/d/` 와 `/edit` 사이 값)

### 4. 워크플로우 내 값 교체

아래 `YOUR_*` 값을 실제 값으로 교체하세요.

| 위치 | 변수 | 설명 |
|------|------|------|
| Read Archive URLs 노드 | `YOUR_SPREADSHEET_ID` | Google Sheets 스프레드시트 ID |
| Archive To Sheets1 노드 | `YOUR_SPREADSHEET_ID` | 동일한 스프레드시트 ID |
| Send Telegram 노드 | `YOUR_TELEGRAM_CHAT_ID` | 텔레그램 채널 ID 또는 @username |
| 텔레그램 전송 노드 | `YOUR_TELEGRAM_CHAT_ID` | 동일한 채널 ID |
| 텔레그램 속보 알림 노드 | `YOUR_TELEGRAM_CHAT_ID` | 동일한 채널 ID |

> **Telegram Chat ID 확인 방법**: 봇을 채널에 초대 후 `https://api.telegram.org/bot<TOKEN>/getUpdates` 호출

### 5. 스케줄 확인

`Schedule Trigger` 노드의 cron 표현식: `30 07 * * *` (UTC 기준 매일 07:30 = KST 16:30)

원하는 시간으로 변경하세요.

---

## 텔레그램 출력 예시

```
[3월 22일 모닝 브리핑]

📊 시장 데이터
다우  +0.3%  42,500
S&P500  +0.1%  5,800
나스닥  -0.2%  18,200
...

[주요국 이슈]

# 미국
트럼프, 반도체 관세 60일 유예 발표, 시장 환호
반도체·IT 섹터 일제히 상승, 엔비디아 4% 급등
https://...

# 한국
한국은행, 기준금리 3.0% 동결 결정
...
```

---

## 커스터마이징

- **AI 프롬프트 수정**: `AI Country Classifier`, `AI subject Classifier`, `AI Scoring`, `AI Summarizer` 노드의 System Message 편집
- **수집 소스 추가**: RSS Read 노드 추가 후 `Merge News Sources`에 연결
- **선별 기사 수 조정**: `Top N USA1/2/3`, `Top N Korea1/2/3` 노드의 `const N = 1` 값 변경
- **속보 감지 키워드 추가**: `[속보], [특징주] 탐색` IF 노드의 조건에 키워드 추가

---

## 사용 서비스

| 서비스 | 역할 | 비용 |
|--------|------|------|
| OpenAI API | 뉴스 분류 (gpt-4o-mini) + 요약 (gpt-4o) | 유료 (사용량 기반) |
| Google Sheets | 중복 제거 + 아카이빙 | 무료 |
| Telegram Bot API | 브리핑 전송 | 무료 |
| 연합뉴스 / CNBC / Yahoo Finance RSS | 뉴스 수집 | 무료 |
