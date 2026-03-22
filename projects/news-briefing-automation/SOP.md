# SOP: 뉴스 자동화 브리핑 워크플로우

---

## [워크플로우 이름]
뉴스 자동화 브리핑 — 경제·증시 뉴스 수집·분석·텔레그램 전송 파이프라인

---

## [목적]
매일 아침(또는 수동 실행 시) 경제·증시 관련 뉴스를 수집·분석하여 텔레그램으로 브리핑을 전송한다.

---

## [전체 구조]

```
트리거 → 뉴스 수집(4소스 병렬) → Merge → 정규화(Set)
→ 시간 필터(최근 15시간) → 중복 제거(Google Sheets)
→ AI Agent ①: 국가 분류 + 경제 무관 기사 제외
→ AI Agent ②: 한국 증시 영향도 점수(1~5)
→ Switch 라우팅(국가별) → 국가별 상위 N건 선별
→ AI Agent ③: 요약(placeholder)
→ Google Sheets 아카이빙
→ 메시지 조립(Code) → 텔레그램 전송
```

---

## [처리 로직]

### STEP 1. 트리거

- `Manual Trigger` + `Schedule Trigger(매일 08:00 KST, 크론: 0 23 * * *)` → **Merge(Append)**
- 두 트리거 모두 동일한 플로우 실행

---

### STEP 2. 뉴스 수집 (4소스 병렬)

| 우선순위 등급 | 소스 | 노드 |
|---|---|---|
| A | 연합뉴스 | RSS Read |
| B | CNBC | RSS Read |
| B | 야후 파이낸스 | HTTP Request (API 또는 RSS) |
| C | Google / Naver News | RSS Read |

- 각 노드에 `source` 필드 추가 (예: `"yonhap"`, `"cnbc"`, `"yahoo"`, `"google_naver"`)
- 소스 우선순위는 동점 타이브레이커에 사용

---

### STEP 3. 데이터 정규화 (Set 노드)

- 날짜 필드 통일: `pubDate` / `publishedAt` / `published` → `article_date` (ISO 8601, UTC)
- 공통 필드: `title`, `article_url`, `source`, `article_date`

---

### STEP 4. 시간 필터 (Code 노드)

```javascript
const now = new Date();
const cutoff = new Date(now.getTime() - 15 * 60 * 60 * 1000);
// article_date >= cutoff 인 기사만 통과
```

---

### STEP 5. 중복 제거 (Google Sheets)

- 시트명: `뉴스 아카이브`
- `url` 컬럼과 비교 → 이미 존재하면 제거, 신규만 통과
- 워크플로우 말미에 7일 이상 된 행 자동 삭제

---

### STEP 6. AI Agent ① : 국가 분류

- 입력: 기사 제목 + 본문 일부
- 출력 JSON: `{ "country": "미국|중국|한국|기타|제외" }`
- `제외`: 경제·증시 무관 기사 (스포츠, 연예 등)

---

### STEP 7. AI Agent ② : 한국 증시 영향도

- 입력: 기사 제목 + 본문 + country
- 출력 JSON: `{ "impact_score": 1~5 }`
- 점수 기준은 현재 placeholder (추후 기준 데이터 교체 예정)

---

### STEP 8. Switch 라우팅 + 국가별 선별

- `country` 값 기준 4개 브랜치
- 각 브랜치에서 `impact_score` 내림차순 → 슬라이싱

| 국가 | 상한 |
|---|---|
| 미국 | 2~3건 |
| 중국 | 1~2건 |
| 한국 | 2~3건 |
| 기타 | 1~2건 |

- 동점 시 소스 우선순위 A → B → C 적용

---

### STEP 9. AI Agent ③ : 요약

- 입력: 기사 본문
- 출력: `summary` (문자열)
- 프롬프트 내용은 **placeholder** ("기사를 3문장 이내로 요약하라"로 임시 설정), 추후 교체 예정

---

### STEP 10. Google Sheets 아카이빙

- 시트명: `뉴스 아카이브`
- 컬럼: `date`, `title`, `url`, `source`, `country`, `impact_score`, `summary`

---

### STEP 11. 메시지 조립 (Code 노드)

출력 형식 (이모지 없음, 모든 국가에 출처 URL 명시):

```
[주요국 이슈]

# 미국
기사 요약 1
https://출처

기사 요약 2
https://출처

# 중국
기사 요약 1
https://출처

# 한국
기사 요약 1
https://출처

# 기타
기사 요약 1
https://출처
```

---

### STEP 12. 텔레그램 전송

- `Telegram` 노드
- Chat ID 목록(배열) → `Split In Batches`로 순회 전송
- 봇 토큰 / Chat ID는 n8n Credential에 직접 등록

---

## [보류 항목 (placeholder)]

| 항목 | 현재 처리 |
|---|---|
| 요약 프롬프트 | "3문장 이내 요약"으로 임시 설정 |
| 한국 증시 영향도 기준 | 기본 1~5점 척도 |
| 텔레그램 봇 토큰 / Chat ID | 직접 등록 |

---

## [사용 서비스]

| 서비스 | 역할 | 연동 방식 |
|---|---|---|
| 연합뉴스 RSS | 뉴스 수집 (우선순위 A) | RSS Read |
| CNBC RSS | 뉴스 수집 (우선순위 B) | RSS Read |
| 야후 파이낸스 | 뉴스 수집 (우선순위 B) | HTTP Request |
| Google / Naver News RSS | 뉴스 수집 (우선순위 C) | RSS Read |
| Google Sheets | 중복 제거 및 아카이빙 | OAuth2 |
| AI Agent (LLM) | 국가 분류, 영향도 평가, 요약 | API Key |
| Telegram Bot API | 브리핑 전송 | Bot Token |
