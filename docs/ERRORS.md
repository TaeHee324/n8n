# Error Knowledge Base

## 1. `$('노드명')` 런타임 에러

### 증상

Code 노드나 expression에서 `$('Prepare Message')`, `$('시장 데이터 조회 + 메시지 포맷')`처럼 특정 노드를 참조할 때 실행이 실패한다. 에러 메시지는 실행 경로에 해당 노드 데이터가 없거나 paired item을 찾을 수 없다는 형태로 나타난다.

### 원인

IF/Switch/Loop 분기 이후 현재 item의 실행 경로에 없는 노드를 직접 참조했기 때문이다. n8n expression은 캔버스에 노드가 존재하는지만 보지 않고, 현재 실행 item이 그 노드를 지나왔는지도 영향을 받는다.

### 해결

분기 전에 필요한 원본 데이터를 별도 입력으로 보존하고, 분기 후 `Merge` 노드로 다시 합친다. Telegram to Obsidian의 `Merge`, 뉴스 브리핑의 `Merge yonhap`/`Merge cnbc`/`Merge yahoo`, 경제지표 자동화의 `Merge Article Data`처럼 원본 메타데이터와 후속 처리 결과를 명시적으로 재결합한다.

### 예방

분기 이후 단계에서 원본 필드가 필요하면 expression 직접 참조보다 Merge 설계를 먼저 검토한다. 직접 참조가 필요할 때는 해당 노드가 모든 실행 경로에서 실행되는지 확인한다.

## 2. Credential 연결 안 됨 에러

### 증상

Telegram, OpenAI, Google Sheets, Microsoft OneDrive 노드 실행 시 `Credential not found`, 인증 정보 없음, 권한 없음 메시지가 발생한다.

### 원인

워크플로우 JSON에 있는 Credential ID가 현재 n8n 인스턴스에 없거나, 다른 계정의 Credential ID를 참조하고 있다. 새 워크플로우를 import하거나 Credential을 재생성한 경우 자주 발생한다.

### 해결

n8n UI에서 실패한 노드를 열고 Credential 드롭다운에서 올바른 계정을 다시 선택한다. Telegram Bot, OpenAI API, Microsoft OneDrive OAuth2, Google Sheets OAuth2 노드는 각각 실제 운영 계정으로 재연결해야 한다.

### 예방

Claude Code나 JSON 편집 단계에서는 Credential secret을 직접 다루지 않는다. 노드 타입과 `nodeCredentialType`만 맞춘 뒤, 운영자가 UI에서 최종 연결한다.

## 3. OneDrive PUT 403 에러

### 증상

`Upload Attachment` 또는 `uproad to drive` 실행 시 Microsoft Graph API가 `403 Forbidden`을 반환한다. Markdown 또는 첨부파일 업로드가 실패한다.

### 원인

Microsoft OAuth2 토큰이 만료되었거나, Graph API 경로에 포함된 한글/공백/특수문자가 올바르게 URL 인코딩되지 않았다. OneDrive 대상 폴더 권한이 변경된 경우도 가능하다.

### 해결

먼저 n8n UI에서 Microsoft OneDrive Credential을 재인증한다. 그래도 실패하면 Graph API URL의 vault 경로와 파일명을 `encodeURIComponent` 기준으로 인코딩한다. 특히 `옵시디언`, 공백, `/`, `?`, `#`, `%`가 포함된 동적 파일명은 sanitize 후 업로드한다.

### 예방

파일명 생성 단계에서 Windows/OneDrive 금지 문자를 제거하고, Graph API URL에는 인코딩된 path segment를 사용한다. 한글 경로를 raw 문자열과 percent-encoded 문자열로 섞어 쓰지 않는다.

## 4. OpenAI JSON Schema 파싱 실패

### 증상

`response_format: json_schema` 사용 시 빈 응답, schema validation 실패, JSON 파싱 에러가 발생한다. AI Agent 출력이 JSON 코드블록이나 느슨한 텍스트로 돌아와 `JSON.parse`가 실패하기도 한다.

### 원인

JSON Schema에 `additionalProperties: false`가 빠졌거나 `required`와 `properties` 구조가 일치하지 않는다. AI Agent 방식에서는 모델이 system prompt의 JSON 요구를 따르지 않고 설명 문장을 섞을 수 있다.

### 해결

OpenAI REST 직접 호출에서는 `strict: true`, `additionalProperties: false`, 모든 필수 필드의 `required` 포함 여부를 확인한다. AI Agent 출력은 `Parse Summary`처럼 JSON parse를 먼저 시도하고, 실패 시 정규식 fallback 또는 빈 필드 방어 로직을 둔다.

### 예방

단순 JSON 생성은 HTTP Request 직접 호출과 엄격한 schema를 사용한다. 복잡한 AI Agent 출력은 후속 Code 노드에서 파싱/검증한 뒤 텔레그램 메시지나 Sheets append에 넘긴다.

## 5. RSS 트리거 중복 실행

### 증상

같은 뉴스나 경제지표 기사가 여러 번 처리되어 텔레그램에 중복 발행되거나 Google Sheets에 중복 행이 추가된다.

### 원인

RSS 트리거의 `pollTimes`가 너무 짧거나 RSS 제공자가 GUID/link를 변경한다. 수동 실행과 스케줄 실행이 같은 시간대에 겹치거나, archive read 실패로 기존 URL 목록이 비어 있는 경우도 있다.

### 해결

폴링 간격을 늘리고, 중복 체크 Code 노드를 추가한다. 뉴스 브리핑처럼 Google Sheets의 기존 URL을 읽어 `archived_urls`와 실행 내 `seenUrls`를 함께 비교한다. 경제지표는 날짜+카테고리+기사 제목 조합을 보조 키로 사용하는 방식을 검토한다.

### 예방

RSS 수집 후 바로 발행하지 말고 normalize, archive read, dedup 단계를 통과시킨다. Google Sheets read 노드가 실패했을 때 중복 방지가 비활성화되지 않도록 에러 출력과 fallback 정책을 점검한다.

## 6. n8n API PUT 400 에러: 허용되지 않는 필드

### 증상

n8n REST API로 워크플로우를 수정할 때 `400 Bad Request`가 발생한다. 응답에는 허용되지 않는 필드 또는 schema validation 오류가 포함될 수 있다.

### 원인

워크플로우 JSON의 `settings`에 API가 허용하지 않는 키가 포함되어 있다. 특히 업데이트 payload에 export 전용 메타데이터나 인스턴스 내부 필드가 섞이면 실패한다.

### 해결

PUT payload의 `settings`에는 운영에 필요한 허용 필드만 남긴다. 현재 기준으로 `executionOrder`, `timezone`, `callerPolicy`를 우선 허용하고, 환경에서 검증된 경우에만 `availableInMCP`, `binaryMode`, `timeSavedMode` 같은 필드를 포함한다. 불필요한 `meta`, `versionId`, read-only 필드는 업데이트 payload에서 제거한다.

### 예방

로컬 workflow export 파일을 그대로 PUT하지 않는다. API 업데이트 전 payload 정리 단계를 두고, 실패한 응답 body를 보관해 어느 필드가 거부되었는지 확인한다.

## 7. Webhook 응답 없음

### 증상

텔레그램 메시지를 보내도 `Telegram Trigger`가 실행되지 않거나, 봇 Webhook 기반 워크플로우가 반응하지 않는다.

### 원인

워크플로우가 비활성화되어 있거나, Railway 배포 URL 변경으로 Telegram Webhook URL이 이전 주소를 가리킨다. Telegram credential이 다른 봇 토큰으로 연결된 경우도 있다.

### 해결

n8n UI에서 워크플로우 active 상태를 확인한다. Telegram Trigger 노드를 다시 저장/활성화해 Webhook을 재등록하거나 Telegram Bot API의 `setWebhook`으로 현재 Railway URL을 등록한다. Credential이 올바른 봇인지 확인한다.

### 예방

Railway 도메인 변경, 워크플로우 import, credential 재연결 후에는 테스트 메시지로 트리거 동작을 확인한다. 운영 URL은 문서와 환경 변수에 일관되게 유지한다.

## 8. Telegram MarkdownV2 파싱 에러

### 증상

`Send Telegram` 또는 `텔레그램 전송`에서 메시지 전송이 실패하고, Telegram API가 Markdown entity 파싱 오류를 반환한다.

### 원인

MarkdownV2 모드에서 `_ * [ ] ( ) ~ ` > # + - = | { } . ! \` 문자가 이스케이프되지 않았다. 뉴스 제목, URL, 수치, AI 요약문에 특수문자가 섞일 때 발생한다.

### 해결

`Assemble Message`처럼 전송 직전에 escape 함수를 적용한다. 링크 URL은 `.` 같은 문자도 이스케이프하고, 굵게 처리할 제목과 본문을 따로 escape한 뒤 Markdown 문법을 조립한다.

### 예방

AI 출력과 RSS 제목을 신뢰하지 말고 모든 사용자/외부 입력 문자열을 escape한다. 메시지 길이가 긴 브리핑은 테스트 채팅으로 먼저 전송해 파싱 오류 위치를 확인한다.

## 9. QuickChart 응답 URL 없음

### 증상

`Send to QuickChart` 이후 `Send Chart Photos`가 보낼 `url` 필드를 찾지 못하거나 Telegram photo 전송이 실패한다.

### 원인

QuickChart payload의 `chart` 구조가 Chart.js 형식과 맞지 않거나, 데이터 배열에 숫자가 아닌 문자열/빈 값이 섞였다. QuickChart API 응답 형식이 예상과 다르거나 HTTP 요청이 실패했을 수도 있다.

### 해결

`Build QuickChart JSON`에서 `parseFloat` 결과가 유효하지 않은 값은 `null`로 처리한다. `Send to QuickChart` 응답에 `url`이 있는지 확인하고, 없으면 response body를 로그로 남긴다. 차트 JSON은 단일 지표부터 최소 구성으로 줄여 검증한다.

### 예방

Google Sheets에서 읽은 값은 차트 생성 전에 날짜 정렬, 숫자 변환, 최근 기간 필터를 통과시킨다. QuickChart 호출 직후 URL 존재 여부를 검증하는 IF/Code 노드를 추가하면 텔레그램 전송 실패를 분리할 수 있다.
