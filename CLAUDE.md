# CLAUDE.md — n8n 워크플로우 프로젝트

이 폴더는 n8n 워크플로우 프로젝트들을 관리하는 공간입니다.
새 프로젝트 시작 시 `projects/{project-name}/` 폴더를 생성하고, 해당 폴더의 **SOP.md를 먼저 읽고** 작업하세요.

---

## 프로젝트 목록

| 폴더 | 설명 |
|------|------|
| `projects/news-briefing-automation/` | 경제·증시 뉴스 수집·분석·텔레그램 브리핑 |
| `projects/telegram-to-obsidian/` | 텔레그램 메시지 → OneDrive → 옵시디언 .md 자동 저장 |

---

## 사용 가능한 도구

### n8n MCP
- n8n 인스턴스: `https://primary-production-90c7.up.railway.app`
- 워크플로우 생성·조회·수정·실행 가능

### n8n Skills (7개)
`~/.claude/skills/` 에 설치됨. 워크플로우 제작 시 단계별로 활용하세요.

| 스킬명 | 용도 |
|--------|------|
| `n8n-workflow-patterns` | 워크플로우 패턴 설계 |
| `n8n-node-configuration` | 노드 설정값 구성 |
| `n8n-mcp-tools-expert` | MCP 도구 활용 |
| `n8n-code-javascript` | JavaScript 코드 노드 |
| `n8n-code-python` | Python 코드 노드 |
| `n8n-expression-syntax` | n8n 표현식 문법 |
| `n8n-validation-expert` | 워크플로우 검증 |

---

## 워크플로우 제작 프로세스 (10단계)

1. **SOP.md 읽기** — 워크플로우 로직, 데이터 스키마, 에러 처리 규칙 파악
2. **변수 생존 검증 및 데이터 흐름 설계** — 아래 원칙 참고
3. **노드 구성 설계** — n8n Skills(`n8n-workflow-patterns`, `n8n-node-configuration`)를 참고해 최적 노드 구성 설계
4. **워크플로우 생성** — n8n MCP + n8n Skills를 통해 워크플로우 생성 (Credential은 노드 타입만 지정, 연결은 사용자에게 맡김)
4. **테스트 실행** — 각 노드 개별 실행 후 전체 플로우 검증
5. **테스트 실행** — 각 노드 개별 실행 후 전체 플로우 검증
6. **에러 자동 수정** — 실패 노드 원인 분석 후 수정
7. **노드 설정값 검수** — 모든 노드의 필수 설정값 누락 여부 확인 (`n8n-validation-expert` 활용)
8. **Credential 설정 가이드 제공** — 사용자가 직접 연결할 수 있도록 필요한 Credential 목록과 설정 방법 안내
9. **워크플로우 링크 제공** — 완료 후 `https://primary-production-90c7.up.railway.app` 워크플로우 URL 제공
10. **JSON 파일 저장** — `./projects/{project-name}/workflows/` 에 저장

---

## 변수 생존 검증 원칙

노드 구성 전, 아래 표를 작성하여 각 변수가 사용 시점에 `$json`에 살아있는지 확인한다.

| 변수명 | 생성 노드 | 사용 노드 | 분기 후 소실 여부 | 해결 방식 |
|--------|---------|---------|--------------|---------|
| 예: `msg_type` | Prepare Message | Build MD | ❌ 소실 | Merge 노드로 재연결 |
| 예: `gpt_title` | Parse GPT Response | Upload MD | ✅ 유지 | `$json.gpt_title` |

**데이터 소실 해결 우선순위 (반드시 이 순서를 따를 것)**

1. **Merge 노드 우선** — 분기 전 노드를 Merge로 다시 연결해 `$json`에 데이터 유지
2. **`$('노드명')` 참조는 최후 수단** — 해당 노드가 실행 경로에 없으면 런타임 에러 발생 위험

**Merge 적용 기준:**
- IF/Switch 분기 이후 원본 데이터가 필요한 경우
- 두 브랜치 결과를 하나로 합쳐야 하는 경우

---

## Credential 처리 원칙

- **워크플로우 생성 시 Credential을 직접 연결하지 않는다**
- 노드 타입(`telegramApi`, `openAiApi` 등)만 지정하고, 실제 Credential 생성·연결은 사용자에게 맡긴다
- 워크플로우 완성 후 사용자에게 아래 형식으로 Credential 설정 가이드를 제공한다:

```
필요한 Credential 목록:
- Telegram API → [노드명1, 노드명2]
- OpenAI API   → [노드명3]
- OneDrive OAuth2 → [노드명4, 노드명5]
```

---

## 필수 체크리스트

- [ ] 변수 생존 검증 표 작성 완료
- [ ] 데이터 소실 구간에 Merge 노드 우선 적용
- [ ] Credential은 노드 타입만 지정, 연결은 사용자에게 맡김
- [ ] 에러 핸들링이 필요한 노드 파악 후 해당 노드의 에러 핸들링 옵션 설정
- [ ] 각 노드에 명확한 영어 이름 부여
- [ ] SOP.md에 명시된 로직을 정확히 따름
- [ ] 모든 노드 설정값 누락 없는지 확인
- [ ] n8n Skills를 단계별로 실행
- [ ] **AI 노드 설정 시 `operation` 값은 반드시 실제 존재하는 값만 사용** (n8n MCP로 사전 확인)
