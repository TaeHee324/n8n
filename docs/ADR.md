# Architecture Decision Records

## ADR-001: MCP 대신 REST API 사용

### 배경

n8n MCP 도구가 존재하지만, 운영 작업에서 도구 버전과 Claude Code 실행 환경에 따라 안정성이 흔들릴 수 있다. 워크플로우 조회, 수정, 배포가 비결정적으로 실패하면 실제 운영 중인 Railway n8n 인스턴스의 상태를 신뢰하기 어렵다.

### 결정

n8n 워크플로우 작업은 MCP를 기본 경로로 사용하지 않고 REST API를 기준으로 처리한다. 로컬 JSON 파일은 변경 이력과 리뷰 기준으로 사용하고, 실제 인스턴스 반영은 n8n REST API의 명시적 요청/응답으로 확인한다.

### 이유

REST API는 요청 URL, HTTP method, payload, status code, response body가 명확해 재현과 디버깅이 쉽다. Claude Code 버전이나 MCP 세션 상태에 의존하지 않으며, 실패 시 어느 필드가 거부되었는지 추적하기 쉽다.

### 트레이드오프

MCP가 제공할 수 있는 고수준 편의 기능은 포기한다. 대신 API payload 정리, 허용 필드 필터링, 인증 헤더 관리 같은 반복 작업을 직접 관리해야 한다.

## ADR-002: AI Agent 노드 vs HTTP Request 직접 호출

### 배경

OpenAI 호출은 n8n LangChain `AI Agent` 노드로 처리하거나, `HTTP Request` 노드로 OpenAI REST API를 직접 호출할 수 있다. 현재 워크플로우에는 두 방식이 모두 사용된다.

### 결정

복잡한 프롬프팅, 다단계 판단, tool use 또는 retry가 중요한 작업은 `AI Agent` 노드를 사용한다. 짧고 엄격한 JSON 생성처럼 단순한 요청은 `HTTP Request`로 OpenAI API를 직접 호출한다.

### 이유

뉴스 브리핑의 국가/주제/점수 분류와 기사 요약, 경제지표 코멘트는 맥락 판단이 필요하므로 `AI Agent`가 적합하다. Telegram to Obsidian의 제목/태그 생성은 `gpt-4o-mini`에 `response_format: json_schema`를 직접 전달하면 충분하며, REST 호출이 더 가볍고 출력 스키마를 명확히 통제할 수 있다.

### 트레이드오프

`AI Agent`는 노드 구성이 많아지고 실행 오버헤드가 있다. `HTTP Request`는 schema, retry, parsing, error handling을 직접 구현해야 한다.

## ADR-003: Merge 노드 우선 원칙

### 배경

n8n에서는 IF/Switch 분기 후 실행 경로에 없는 노드를 `$('노드명')`로 참조하면 런타임 에러가 발생할 수 있다. 특히 첨부파일 유무, 기사 출처, 지표 카테고리처럼 분기가 많은 워크플로우에서 원본 데이터 소실 문제가 반복된다.

### 결정

분기 후 원본 데이터 또는 병렬 처리 결과를 다시 사용해야 할 때는 `$('노드명')` 참조보다 `Merge` 노드로 재연결하는 방식을 우선한다.

### 이유

Merge 노드는 데이터가 어떤 경로로 합쳐지는지 그래프에 드러낸다. Telegram to Obsidian은 AI 메타데이터와 원본 메시지를 `Merge`로 합치고, 뉴스 브리핑은 출처별 HTML 추출 결과를 `Merge yonhap`, `Merge cnbc`, `Merge yahoo`로 원본 메타데이터와 재결합한다. 경제지표 자동화도 AI 코멘트와 파싱된 지표를 `Merge`, `Merge1`, `Merge2`, `Merge Chart+Comment`로 연결한다.

### 트레이드오프

노드 수가 증가하고 캔버스가 복잡해진다. 단순한 선형 흐름에서는 직접 참조보다 장황할 수 있지만, 운영 안정성과 디버깅 가능성을 우선한다.

## ADR-004: Credential 직접 연결 금지

### 배경

Claude Code는 n8n Credential의 실제 secret 값을 알 수 없고 알아서도 안 된다. Credential ID는 인스턴스, 계정, 재생성 여부에 따라 달라질 수 있다.

### 결정

워크플로우를 생성하거나 수정할 때 노드 타입과 인증 방식은 명시하되, 새 Credential 직접 연결은 사용자 또는 n8n UI 작업에 위임한다.

### 이유

Credential은 보안 경계 안에 남겨야 한다. 운영자가 n8n UI에서 Telegram, OpenAI, Microsoft OneDrive, Google Sheets credential을 직접 선택하면 권한 범위를 확인할 수 있고, 잘못된 계정 연결을 즉시 교정할 수 있다.

### 트레이드오프

워크플로우 JSON만으로 완전 자동 배포가 끝나지 않을 수 있다. 신규 환경에서는 UI에서 credential을 재연결하는 수동 단계가 필요하다.

## ADR-005: OneDrive -> Obsidian 동기화

### 배경

Obsidian vault가 OneDrive에 위치한다. 텔레그램 메시지와 첨부파일을 Obsidian에서 바로 검색/링크하려면 vault 내부 Markdown 파일과 attachment 경로에 저장되어야 한다.

### 결정

n8n에서 Microsoft Graph API를 사용해 OneDrive의 `옵시디언/Startegy_Investment/Telegram/` 하위 경로에 Markdown 파일과 첨부파일을 직접 업로드한다.

### 이유

Obsidian 플러그인이나 로컬 파일 시스템 접근 없이도 Railway의 n8n 인스턴스에서 vault 동기화가 가능하다. Markdown 본문은 Obsidian 링크 문법을 포함하므로 OneDrive 동기화 후 Obsidian에서 자연스럽게 열람된다.

### 트레이드오프

Microsoft OAuth2 토큰 상태와 Graph API 경로 인코딩에 의존한다. 한글 경로 또는 특수문자가 포함된 파일명은 URL 인코딩을 주의해야 하며, 403/404 발생 시 credential과 경로를 함께 점검해야 한다.

## ADR-006: Google Sheets를 운영 아카이브와 시계열 저장소로 사용

### 배경

뉴스 브리핑은 중복 발행 방지가 필요하고, 경제지표 자동화는 환율/유가/국고채 데이터를 누적해 차트로 재사용해야 한다. 별도 데이터베이스를 도입하면 인프라 관리 부담이 증가한다.

### 결정

뉴스 URL 아카이브와 경제지표 시계열 저장소는 Google Sheets를 사용한다. 뉴스 브리핑은 `뉴스 아카이브` 문서를 읽고 쓰며, 경제지표 자동화는 `경제지표 차트 자동화` 문서의 `환율`, `유가`, `국고채` 탭에 append한다.

### 이유

Google Sheets는 n8n 노드 지원이 안정적이고, 운영자가 UI에서 데이터 상태를 직접 확인하고 수정할 수 있다. 차트 생성 전 최근 60일 데이터를 읽는 흐름도 단순하다.

### 트레이드오프

대량 데이터, 복잡한 쿼리, 동시성 제어에는 한계가 있다. 데이터 규모가 커지면 BigQuery, PostgreSQL, SQLite 기반 저장소를 검토해야 한다.

## ADR-007: QuickChart.io로 차트 렌더링

### 배경

경제지표 자동화는 텔레그램 채널에 환율, WTI, 국고채 차트를 이미지로 발행해야 한다. n8n 내부에서 직접 이미지를 렌더링하면 런타임 의존성이 커진다.

### 결정

차트 이미지는 `Build QuickChart JSON`에서 Chart.js 호환 JSON을 만들고, `Send to QuickChart`에서 QuickChart.io `/chart/create` API로 생성한다.

### 이유

QuickChart.io는 HTTP 요청만으로 차트 URL을 반환하므로 Railway n8n 환경에 브라우저나 이미지 렌더링 라이브러리를 추가할 필요가 없다. 반환된 URL은 Telegram `sendPhoto` 입력으로 바로 사용할 수 있다.

### 트레이드오프

외부 SaaS 가용성과 API 응답 형식에 의존한다. 민감한 데이터가 차트 payload에 포함되면 외부 전송 범위를 별도로 검토해야 한다.
