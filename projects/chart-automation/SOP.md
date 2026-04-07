# SOP: 한국 경제지표 차트 자동화 워크플로우

## 워크플로우 이름
`chart-automation`

## 목적
매일 평일 오후 5시(KST), 한국 주요 경제지표(달러-원 환율, WTI 유가, 국채 3·10·30년물)를 자동 수집하여 30일 추세 차트(PNG) 5장과 연합인포맥스 RSS 기반 AI 시황 코멘트를 텔레그램으로 전송한다.

---

## 전체 구조

```
Schedule Trigger (평일 17:00 KST = UTC 08:00)
  ↓
Get USD KRW Rate     ← 한국은행 OpenAPI (환율)
  ↓
Get WTI Price        ← EIA API (WTI 유가)
  ↓
Get Bond Rate 3Y     ← 한국은행 OpenAPI (국채 3년)
  ↓
Get Bond Rate 10Y    ← 한국은행 OpenAPI (국채 10년)
  ↓
Get Bond Rate 30Y    ← 한국은행 OpenAPI (국채 30년)
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

## API 엔드포인트 상세

### 한국은행 ECOS OpenAPI
```
GET https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/1/{통계코드}/D/{YYYYMMDD}/{YYYYMMDD}/{항목코드}
```
- `{YYYYMMDD}`: 오늘 날짜 (당일 데이터 조회)
- 응답 경로: `StatisticSearch.row[0].DATA_VALUE`

### EIA API
```
GET https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key={EIA_API_KEY}&frequency=daily&data[0]=value&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1
```
- 응답 경로: `response.data[0].value`

---

## 처리 로직 상세

### STEP 1-5: 지표 수집 (HTTP Request × 5)
- 각 API를 순차 호출
- 응답 실패 시 해당 노드의 Continue on Error 옵션 활성화 → `null` 값으로 진행

### STEP 6: RSS 수집 (RSS Feed Read)
- URL: `https://news.einfomax.co.kr/rss/allArticle.xml`
- 가져올 항목 수: 50건 (최신순)

### STEP 7: 뉴스 필터링 (Code 노드)
- **필터 키워드** (사용자가 수정할 것):
  ```
  ['환율', '달러', '원화', '국채', '채권', '금리', '유가', 'WTI', '원유', 'OPEC']
  ```
- 최대 5건 선택 (최신순)
- 출력: `{ title, link, pubDate }` 배열

### STEP 8: 데이터 파싱 (Code 노드)
```javascript
// 한국은행 응답: StatisticSearch.row[0].DATA_VALUE
// EIA 응답: response.data[0].value
// 날짜: KST 기준 오늘 날짜 (UTC+9)
```
- 모든 지표값을 float으로 변환
- 뉴스 제목 5건을 줄바꿈으로 연결하여 `news_summary` 생성

### STEP 9: Sheets 기록 (Google Sheets Append)
- 시트명: `economic_indicators`
- 컬럼: A(date) B(usd_krw) C(wti) D(bond_3y) E(bond_10y) F(bond_30y)
- 중복 날짜 처리: 미구현 (동일 날짜 재실행 시 2행 생성될 수 있음)

### STEP 10: Sheets 읽기 (Google Sheets Read)
- 최근 30행 읽기
- Code 노드에서 날짜순 정렬 후 labels/datasets 추출

### STEP 11: AI 코멘트 생성 (OpenAI 노드)
- 모델: `gpt-4o-mini`
- **System Prompt** (사용자가 수정할 것):
  ```
  당신은 한국 금융시장 애널리스트입니다.
  아래 오늘의 경제지표와 관련 뉴스 헤드라인을 바탕으로
  환율, 유가, 국채금리 움직임에 대한 간결한 시황 코멘트를 3~4줄로 작성하세요.
  숫자를 반드시 포함하고, 시장 함의를 한 문장으로 마무리하세요.
  ```
- User Message: 오늘 지표값 + `news_summary` 텍스트 전달

### STEP 12: QuickChart JSON 생성 (Code 노드)
- 차트 5개를 별도 item으로 반환 → Loop Over Items에서 순차 처리
- 각 차트: line chart, 30일 데이터, 날짜 label
- QuickChart POST URL: `https://quickchart.io/chart`
- Content-Type: `application/json`
- 응답: PNG 바이너리 (`binaryData`)

### STEP 13: Telegram 전송 (Telegram 노드)
- Operation: `sendMediaGroup`
- 첫 번째 이미지 caption에 AI 코멘트 삽입
- 이미지 5장 한 묶음 전송
- Parse mode: `Markdown`

---

## Google Sheets 구조

**스프레드시트 ID**: `SPREADSHEET_ID` (환경변수)
**시트명**: `economic_indicators`

| 컬럼 | 필드명 | 예시 |
|------|--------|------|
| A | date | 2026-04-05 |
| B | usd_krw | 1380.5 |
| C | wti | 68.2 |
| D | bond_3y | 2.85 |
| E | bond_10y | 3.45 |
| F | bond_30y | 3.90 |

---

## 변수 생존 검증표

| 변수명 | 생성 노드 | 사용 노드 | 소실 여부 | 해결 방식 |
|--------|---------|---------|----------|---------|
| `usd_krw` | Parse and Tag Data | Append to Sheets | ✅ 유지 | 동일 노드 처리 |
| `wti` | Parse and Tag Data | Append to Sheets | ✅ 유지 | 동일 노드 처리 |
| `bond_3y` | Parse and Tag Data | Append to Sheets | ✅ 유지 | 동일 노드 처리 |
| `bond_10y` | Parse and Tag Data | Append to Sheets | ✅ 유지 | 동일 노드 처리 |
| `bond_30y` | Parse and Tag Data | Append to Sheets | ✅ 유지 | 동일 노드 처리 |
| `today` | Parse and Tag Data | Append to Sheets | ✅ 유지 | `$json.today` |
| `news_summary` | Filter RSS News → Parse | Generate Comment | ✅ 유지 | `$json.news_summary` |
| `ai_comment` | Generate Comment | Send to Telegram | ✅ 유지 | `$json.ai_comment` |
| `sheet_rows[]` | Read 30 Days Data | Build QuickChart JSON | ✅ 유지 | `$input.all()` |
| PNG binary × 5 | Send to QuickChart | Send Chart to Telegram | ✅ 유지 | `binaryData` (Loop) |

→ **분기 없음**: 선형 파이프라인 — Merge 노드 불필요

---

## 에러 처리 규칙

| 실패 지점 | 처리 방식 |
|---------|---------|
| 한국은행 API 실패 | Continue on Error → 해당 값 `null`, Sheets에 빈값 기록 |
| EIA API 실패 | Continue on Error → 해당 값 `null` |
| RSS 수신 실패 | Continue on Error → 뉴스 없이 지표값만으로 코멘트 생성 |
| AI 코멘트 실패 | Continue on Error → caption 없이 차트만 전송 |
| QuickChart 실패 | 텔레그램에 "차트 생성 실패" 텍스트 전송 |
| Sheets 쓰기 실패 | Continue on Error → 차트 생성 단계 계속 진행 |

---

## 환경변수 및 Credential 설정

### n8n Variables (워크플로우 내 `$vars` 로 참조)
| 변수명 | 설명 |
|--------|------|
| `BOK_API_KEY` | 한국은행 ECOS OpenAPI 키 (ecos.bok.or.kr/api/) |
| `EIA_API_KEY` | EIA API 키 (eia.gov) |
| `TELEGRAM_CHAT_ID` | 텔레그램 전송 대상 채팅 ID |
| `SPREADSHEET_ID` | Google Sheets 문서 ID |

### 필요 Credential
| Credential 타입 | 연결 노드 |
|----------------|---------|
| `googleSheetsOAuth2Api` | Append to Sheets, Read 30 Days Data |
| `openAiApi` | Generate Comment |
| `telegramApi` | Send Chart to Telegram |

---

## 스케줄
- 실행 주기: 평일(월~금) 오후 5시 KST
- Cron: `0 8 * * 1-5` (UTC 기준)

---

## 사용 서비스

| 서비스 | 용도 | 비용 |
|--------|------|------|
| 한국은행 ECOS OpenAPI | 환율·국채금리 수집 | 무료 |
| EIA API | WTI 유가 수집 | 무료 |
| 연합인포맥스 RSS | 시황 뉴스 수집 | 무료 |
| Google Sheets | 데이터 누적 저장 | 무료 |
| OpenAI GPT-4o-mini | 시황 코멘트 생성 | 소량 유료 |
| QuickChart.io | 차트 PNG 생성 | 무료 (월 500건) |
| Telegram Bot API | 차트·코멘트 전송 | 무료 |
| Railway n8n | 워크플로우 실행 환경 | 기존 인스턴스 |

---

## 사전 준비 체크리스트

- [ ] 한국은행 ECOS OpenAPI 키 발급 (https://ecos.bok.or.kr/api/)
- [ ] EIA API 키 발급 (https://www.eia.gov/opendata/)
- [ ] n8n Variables 등록: `BOK_API_KEY`, `EIA_API_KEY`, `TELEGRAM_CHAT_ID`, `SPREADSHEET_ID`
- [ ] Google Sheets 문서 생성 + 시트명 `economic_indicators` + 헤더 1행 입력
- [ ] n8n Credential 연결: Google Sheets OAuth2, OpenAI API, Telegram API
