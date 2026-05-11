# Step 4 — Agent D: `docs/` 영역

## 역할 및 규칙
- **담당 영역: `docs/` 폴더만 (신규 파일만 생성)**
- `.claude/`, `scripts/`, `templates/`, `projects/` 등 다른 폴더 건드리지 않음
- 아래 프로젝트 컨텍스트를 바탕으로 실제 내용으로 채워 작성 (템플릿 아님)

## 작업 디렉토리
`C:\Users\PC\Desktop\n8n`

## 프로젝트 컨텍스트 (문서 작성에 활용)

### 운영 중인 워크플로우 3개

| 이름 | ID | 파일 경로 |
|------|----|---------|
| Telegram to Obsidian | `a5RvxdkYFp9VLw5A` | `projects/telegram-to-obsidian/workflows/telegram-to-obsidian.json` |
| 뉴스 브리핑 자동화 | (확인 필요) | `projects/news-briefing-automation/workflows/news-briefing-automation.json` |
| 경제지표 차트 자동화 | `WW51yZ7oEmyp01kW` | `projects/chart-automation/workflows/chart-automation.json` |

### 인프라
- n8n 인스턴스: Railway 배포 (`https://primary-production-90c7.up.railway.app`)
- 외부 서비스: Telegram, OpenAI GPT-4o/4o-mini, OneDrive (Microsoft Graph API), Google Sheets, QuickChart.io, 연합인포맥스 RSS

### 핵심 설계 결정
- **MCP 대신 REST API**: 안정성·재현성·Claude Code 의존성 최소화
- **AI Agent 노드 vs HTTP Request 직접 호출**: 복잡한 reasoning은 AI Agent, 단순 JSON 생성은 HTTP Request
- **Merge 노드 우선 원칙**: 분기 후 데이터 재연결 시 `$('노드명')` 참조 대신 Merge 노드 사용
- **OneDrive**: Obsidian vault가 OneDrive에 동기화되어 있어 파일 저장 목적지로 사용

---

## 생성할 파일 (3개)

---

### 1. `docs/ARCHITECTURE.md`

전체 자동화 시스템 구조와 워크플로우 간 관계를 실제 운영 내용 기반으로 작성.

포함할 내용:
- 전체 시스템 개요 (어떤 문제를 해결하는가)
- 각 워크플로우의 데이터 흐름 (트리거 → 처리 → 출력)
- 외부 서비스 의존 관계 다이어그램 (텍스트 형식)
- 공통 패턴 설명 (RSS 파싱 패턴, AI 코멘트 생성 패턴, 텔레그램 전송 패턴)
- 인프라 구성 (Railway n8n 인스턴스, OneDrive, Google Sheets)

---

### 2. `docs/ADR.md`

주요 아키텍처 결정 기록. 아래 결정들을 포함하여 작성.

**결정 목록 (각각 배경 / 결정 / 이유 / 트레이드오프 형식으로 작성):**

1. **ADR-001: MCP 대신 REST API 사용**
   - 배경: n8n MCP 도구 존재하나 불안정 이슈
   - 결정: 모든 n8n 작업을 REST API로만 처리
   - 이유: 재현성, 디버깅 용이성, Claude Code 버전에 무관한 안정성

2. **ADR-002: AI Agent 노드 vs HTTP Request 직접 호출**
   - 배경: OpenAI 호출 방식 두 가지
   - 결정: 복잡한 프롬프팅/도구 사용은 AI Agent 노드, 단순 JSON 응답은 HTTP Request
   - 이유: AI Agent는 오버헤드 있으나 tool use·retry 내장

3. **ADR-003: Merge 노드 우선 원칙**
   - 배경: IF/Switch 분기 후 원본 데이터 소실 문제 반복 발생
   - 결정: `$('노드명')` 참조보다 Merge 노드로 재연결 우선
   - 이유: 런타임 에러 방지, 실행 경로 명시성

4. **ADR-004: Credential 직접 연결 금지**
   - 배경: Claude Code가 Credential ID를 알 수 없는 구조
   - 결정: 워크플로우 생성 시 노드 타입만 지정, 연결은 사용자에게 위임
   - 이유: 보안 및 Claude Code 권한 범위 준수

5. **ADR-005: OneDrive → Obsidian 동기화**
   - 배경: Obsidian vault가 OneDrive에 위치
   - 결정: n8n에서 Microsoft Graph API로 직접 파일 업로드
   - 이유: Obsidian 플러그인 없이 자동 동기화 가능

---

### 3. `docs/ERRORS.md`

지금까지 발생한 n8n 에러 패턴과 해결법 지식베이스. 아래 내용을 포함하여 작성.

**포함할 에러 패턴:**

1. **`$('노드명')` 런타임 에러**
   - 증상: 실행 경로에 없는 노드 참조 시 에러
   - 원인: IF/Switch 분기 후 원본 데이터에 접근하려 할 때
   - 해결: Merge 노드로 분기 전 데이터 재연결

2. **Credential 연결 안 됨 에러**
   - 증상: 노드 실행 시 "Credential not found"
   - 원인: 워크플로우 생성 시 Credential ID가 없거나 다른 계정 ID
   - 해결: n8n UI에서 해당 노드 클릭 → Credential 재연결

3. **OneDrive PUT 403 에러**
   - 증상: 파일 업로드 시 403 Forbidden
   - 원인: OAuth2 토큰 만료 또는 경로의 특수문자(한글 등) URL 인코딩 누락
   - 해결: Credential 재인증 또는 경로를 `encodeURIComponent`로 처리

4. **OpenAI JSON Schema 파싱 실패**
   - 증상: `response_format: json_schema` 사용 시 빈 응답 또는 파싱 에러
   - 원인: `additionalProperties: false` 누락 또는 schema 구조 오류
   - 해결: `strict: true` + `additionalProperties: false` 확인

5. **RSS 트리거 중복 실행**
   - 증상: 같은 기사가 여러 번 처리됨
   - 원인: RSS 트리거의 `pollTimes`가 너무 짧거나 기사 GUID가 변경됨
   - 해결: 폴링 간격 늘리기 또는 중복 체크 코드 노드 추가

6. **n8n API PUT 400 에러 (허용되지 않는 필드)**
   - 증상: 워크플로우 수정 시 400 Bad Request
   - 원인: `settings` 필드에 `executionOrder`, `timezone`, `callerPolicy` 외 다른 키 포함
   - 해결: `settings`에서 허용 필드만 남기고 나머지 제거

7. **Webhook 응답 없음**
   - 증상: 텔레그램 메시지가 와도 워크플로우가 트리거 안 됨
   - 원인: 워크플로우 비활성화 상태 또는 Webhook URL 변경됨
   - 해결: 워크플로우 활성화 확인, 텔레그램 봇 Webhook 재설정

---

## 완료 기준
- [ ] `docs/ARCHITECTURE.md` 생성됨 (실제 운영 내용 반영, 템플릿 아님)
- [ ] `docs/ADR.md` 생성됨 (5개 이상 결정 기록)
- [ ] `docs/ERRORS.md` 생성됨 (7개 이상 에러 패턴 포함)
- [ ] 다른 폴더 건드리지 않음
