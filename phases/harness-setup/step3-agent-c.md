# Step 3 — Agent C: `templates/` 영역

## 역할 및 규칙
- **담당 영역: `templates/` 폴더만 (신규 파일만 생성)**
- `.claude/`, `scripts/`, `docs/`, `projects/` 등 다른 폴더 건드리지 않음
- 템플릿은 `{PLACEHOLDER}` 형식으로 치환 가능하게 작성

## 작업 디렉토리
`C:\Users\PC\Desktop\n8n`

## 프로젝트 컨텍스트
- n8n 워크플로우 자동화 프로젝트 (3개 워크플로우 운영 중)
- 기존 프로젝트 참고용:
  - `projects/chart-automation/SOP.md` — 경제지표 차트 자동화
  - `projects/news-briefing-automation/SOP.md` — 뉴스 브리핑 자동화
  - `projects/telegram-to-obsidian/SOP.md` — 텔레그램 → 옵시디언
- 새 프로젝트 생성 시 `/new-project` 커맨드가 이 템플릿을 복사해서 사용

---

## 생성할 파일 (3개)

---

### 1. `templates/project/SOP.md`

새 n8n 프로젝트 SOP 작성 가이드. 기존 SOP들의 구조를 따름.

```markdown
# SOP — {PROJECT_NAME}

> 이 파일은 템플릿입니다. `{중괄호}` 항목을 실제 내용으로 채우세요.

## 워크플로우 개요
{워크플로우가 하는 일을 1~2문장으로 요약}

## 트리거
- **종류**: {Schedule / Webhook / RSS Feed / Manual}
- **조건**: {언제/어떤 조건으로 실행되는지}
- **cron 표현식** (Schedule인 경우): `{cron expression}`

## 데이터 소스
| 소스 | 형식 | URL / 경로 | 설명 |
|------|------|-----------|------|
| {소스명} | {RSS / HTTP / DB / Telegram} | {URL or 경로} | {설명} |

## 처리 로직
1. **{단계 이름}**: {설명}
2. **{단계 이름}**: {설명}
3. ...

## 변수 생존 검증 표
| 변수명 | 생성 노드 | 사용 노드 | 분기 후 소실 여부 | 해결 방식 |
|--------|---------|---------|--------------|---------|
| {변수} | {노드} | {노드} | ✅ 유지 / ❌ 소실 | {Merge 또는 $('노드')} |

## 에러 처리 정책
| 노드 | 에러 발생 시 동작 |
|------|----------------|
| {노드명} | continueErrorOutput / continueRegularOutput / stopWorkflow |

## 최종 출력
- **형식**: {JSON / 텍스트 / 파일 / Telegram 메시지}
- **목적지**: {Telegram 채널 / OneDrive 경로 / Google Sheets / 등}

## 필요한 Credential
| Credential 종류 | 노드 타입 | 사용 노드 |
|---------------|---------|---------|
| {예: Telegram API} | {telegramApi} | {Send Message} |
| {예: OpenAI API} | {openAiApi} | {AI Agent} |

## 주의사항
- {특별히 주의해야 할 사항 1}
- {특별히 주의해야 할 사항 2}
```

---

### 2. `templates/project/README.md`

새 n8n 프로젝트 README 뼈대. 기존 README 구조를 따름.

```markdown
# {PROJECT_NAME}

{워크플로우 한 줄 설명}

## 워크플로우 구조

```
{트리거} → {처리 단계1} → {처리 단계2} → {출력}
```

| 단계 | 노드 | 설명 |
|------|------|------|
| 트리거 | {노드 타입} | {설명} |
| {단계} | {노드 타입} | {설명} |

## 데이터 소스
- **{소스명}**: {설명 및 URL}

## 사전 준비

### 필요한 Credential
- [ ] **{Credential 종류}** — {발급 방법 또는 설정 위치}
- [ ] **{Credential 종류}** — {발급 방법 또는 설정 위치}

### 외부 설정
- [ ] {필요한 외부 서비스 설정}

## 설치 방법

1. n8n에서 `workflows/{name}.json` import
2. 아래 Credential 생성 및 노드에 연결:
   - **{Credential}** → [{노드명1}, {노드명2}]
3. 워크플로우 활성화

## 에러 처리 정책
{에러 발생 시 동작 방식 설명}

## 사용 서비스
| 서비스 | 용도 |
|--------|------|
| {서비스명} | {용도} |
```

---

### 3. `templates/workflow/base.json`

새 워크플로우의 기본 뼈대. Manual Trigger + Schedule Trigger + 에러 출력 패턴 포함.

```json
{
  "name": "{WORKFLOW_NAME}",
  "nodes": [
    {
      "parameters": {},
      "id": "node-manual-trigger",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [-200, 0]
    },
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 9 * * 1-5"
            }
          ]
        }
      },
      "id": "node-schedule-trigger",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [-200, 160]
    },
    {
      "parameters": {
        "jsCode": "// 메인 로직을 여기에 작성하세요\nconst item = $input.first().json;\n\nreturn [{ json: { ...item, processed: true } }];\n"
      },
      "id": "node-main-logic",
      "name": "Main Logic",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [0, 80]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [[{ "node": "Main Logic", "type": "main", "index": 0 }]]
    },
    "Schedule Trigger": {
      "main": [[{ "node": "Main Logic", "type": "main", "index": 0 }]]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "timezone": "Asia/Seoul",
    "callerPolicy": "workflowsFromSameOwner"
  },
  "active": false,
  "tags": []
}
```

---

## 완료 기준
- [ ] `templates/project/SOP.md` 생성됨
- [ ] `templates/project/README.md` 생성됨
- [ ] `templates/workflow/base.json` 생성됨 (JSON 문법 오류 없음)
- [ ] 모든 `{PLACEHOLDER}` 가 실제 값이 아닌 치환용 형식으로 유지됨
- [ ] 다른 폴더 건드리지 않음
