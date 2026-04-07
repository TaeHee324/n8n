# 경제지표 차트 자동화 (n8n Workflow)

매일 평일 오후 5시(KST), 한국 주요 경제지표(달러-원 환율, WTI 유가, 국채 3·10·30년물)를 자동 수집하여 30일 추세 차트 5장과 AI 시황 코멘트를 텔레그램으로 전송하는 n8n 워크플로우입니다.

---

## 주요 기능

- **5개 지표 자동 수집**: 달러-원 환율(한국은행 ECOS), WTI 유가(EIA API), 국채 3·10·30년물(한국은행 ECOS)
- **뉴스 필터링**: 연합인포맥스 RSS에서 환율·채권·유가 관련 기사 최대 5건 추출
- **Google Sheets 누적**: 매일 1행씩 추가, 최근 30일 데이터 자동 관리
- **AI 시황 코멘트**: GPT-4o-mini가 지표값 + 뉴스 헤드라인 기반으로 3~4줄 코멘트 생성
- **차트 생성**: QuickChart.io로 30일 추세 라인차트 PNG 5장 생성
- **텔레그램 전송**: `sendMediaGroup`으로 코멘트 caption + 이미지 5장 한 번에 전송

---

## 전체 구조

```
Schedule Trigger (평일 17:00 KST = UTC 08:00)
  ↓
Get USD KRW Rate     ← 한국은행 ECOS OpenAPI (환율)
  ↓
Get WTI Price        ← EIA API (WTI 유가)
  ↓
Get Bond Rate 3Y     ← 한국은행 ECOS OpenAPI (국채 3년)
  ↓
Get Bond Rate 10Y    ← 한국은행 ECOS OpenAPI (국채 10년)
  ↓
Get Bond Rate 30Y    ← 한국은행 ECOS OpenAPI (국채 30년)
  ↓
Get Einfomax News    ← 연합인포맥스 RSS (전체 기사)
  ↓
Filter RSS News      ← 환율/채권/유가 키워드 필터링
  ↓
Parse and Tag Data   ← 지표값 파싱 + 날짜 태깅 + 뉴스 합산
  ↓
Append to Sheets     ← Google Sheets 오늘 데이터 1행 추가
  ↓
Read 30 Days Data    ← Google Sheets 최근 30행 읽기
  ↓
Generate Comment     ← GPT-4o-mini: 지표 + 뉴스 기반 시황 코멘트
  ↓
Build QuickChart JSON ← 차트 5개 JSON 생성
  ↓
Send to QuickChart   ← QuickChart.io POST → PNG 바이너리 (Loop)
  ↓
Send Chart to Telegram ← sendMediaGroup: 코멘트 caption + 이미지 5장
```

---

## 데이터 소스

| 지표 | API | 비고 |
|------|-----|------|
| 달러-원 환율 | 한국은행 ECOS OpenAPI | 통계코드 `731Y001`, 항목코드 `0000001` |
| WTI 유가 | EIA API v2 | `petroleum/pri/spt` 시리즈 |
| 국채 3년물 | 한국은행 ECOS OpenAPI | 통계코드 `817Y002`, 항목코드 `010200000` |
| 국채 10년물 | 한국은행 ECOS OpenAPI | 통계코드 `817Y002`, 항목코드 `010210000` |
| 국채 30년물 | 한국은행 ECOS OpenAPI | 통계코드 `817Y002`, 항목코드 `010230000` |
| 시황 뉴스 | 연합인포맥스 RSS | `https://news.einfomax.co.kr/rss/allArticle.xml` |

---

## 사전 준비

| 항목 | 설명 |
|------|------|
| 한국은행 ECOS API 키 | [ecos.bok.or.kr/api](https://ecos.bok.or.kr/api/) 에서 무료 발급 |
| EIA API 키 | [eia.gov/opendata](https://www.eia.gov/opendata/) 에서 무료 발급 |
| OpenAI API 키 | GPT-4o-mini 사용 |
| Google Sheets | OAuth2 연동 + 시트 `economic_indicators` 생성 필요 |
| Telegram Bot | BotFather에서 봇 생성 후 토큰 발급 |

---

## 설치 방법

### 1. 워크플로우 Import

1. n8n 좌측 메뉴 → **Workflows** → **Import from file**
2. `workflows/chart-automation.json` 파일 선택

### 2. n8n Variables 등록

n8n 좌측 메뉴 → **Settings** → **Variables**

| 변수명 | 설명 |
|--------|------|
| `BOK_API_KEY` | 한국은행 ECOS OpenAPI 키 |
| `EIA_API_KEY` | EIA API 키 |
| `TELEGRAM_CHAT_ID` | 텔레그램 전송 대상 채팅 ID |
| `SPREADSHEET_ID` | Google Sheets 문서 ID |

### 3. Credential 등록

n8n 좌측 메뉴 → **Credentials** → **Add Credential**

| Credential 타입 | 연결할 노드 |
|-----------------|------------|
| Google Sheets OAuth2 | Append to Sheets, Read 30 Days Data |
| OpenAI API | Generate Comment |
| Telegram API | Send Chart to Telegram |

### 4. Google Sheets 설정

1. Google Sheets에서 새 스프레드시트 생성
2. 시트 이름을 `economic_indicators`로 설정
3. 1행에 헤더 추가: `date` / `usd_krw` / `wti` / `bond_3y` / `bond_10y` / `bond_30y`
4. 스프레드시트 ID를 복사 (URL의 `/d/` 와 `/edit` 사이 값) → n8n Variables에 등록

### 5. 스케줄 확인

`Schedule Trigger` 노드의 cron 표현식: `0 8 * * 1-5` (UTC 기준 평일 08:00 = KST 17:00)

---

## 에러 처리 정책

| 실패 지점 | 처리 방식 |
|---------|---------|
| 한국은행 API 실패 | Continue on Error → 해당 값 `null`, Sheets에 빈값 기록 |
| EIA API 실패 | Continue on Error → 해당 값 `null` |
| RSS 수신 실패 | Continue on Error → 뉴스 없이 지표값만으로 코멘트 생성 |
| AI 코멘트 실패 | Continue on Error → caption 없이 차트만 전송 |
| Sheets 쓰기 실패 | Continue on Error → 차트 생성 단계 계속 진행 |

---

## 사용 서비스

| 서비스 | 역할 | 비용 |
|--------|------|------|
| 한국은행 ECOS OpenAPI | 환율·국채금리 수집 | 무료 |
| EIA API | WTI 유가 수집 | 무료 |
| 연합인포맥스 RSS | 시황 뉴스 수집 | 무료 |
| Google Sheets | 데이터 누적 저장 | 무료 |
| OpenAI GPT-4o-mini | 시황 코멘트 생성 | 소량 유료 |
| QuickChart.io | 차트 PNG 생성 | 무료 (월 500건) |
| Telegram Bot API | 차트·코멘트 전송 | 무료 |
