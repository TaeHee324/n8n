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

## 워크플로우 제작 프로세스 (8단계)

1. **SOP.md 읽기** — 워크플로우 로직, 데이터 스키마, 에러 처리 규칙 파악
2. **노드 구성 설계** — n8n Skills(`n8n-workflow-patterns`, `n8n-node-configuration`)를 참고해 최적 노드 구성 설계
3. **워크플로우 생성** — n8n MCP + n8n Skills를 통해 워크플로우 생성
4. **테스트 실행** — 각 노드 개별 실행 후 전체 플로우 검증
5. **에러 자동 수정** — 실패 노드 원인 분석 후 수정
6. **노드 설정값 검수** — 모든 노드의 필수 설정값 누락 여부 확인 (`n8n-validation-expert` 활용)
7. **워크플로우 링크 제공** — 완료 후 `https://primary-production-90c7.up.railway.app` 워크플로우 URL 제공
8. **JSON 파일 저장** — `./projects/{project-name}/workflows/` 에 저장

---

## 필수 체크리스트

- [ ] 에러 핸들링이 필요한 노드 파악 후 해당 노드의 에러 핸들링 옵션 설정
- [ ] 각 노드에 명확한 영어 이름 부여
- [ ] SOP.md에 명시된 로직을 정확히 따름
- [ ] 모든 노드 설정값 누락 없는지 확인
- [ ] n8n Skills를 단계별로 실행
- [ ] **AI 노드 설정 시 `operation` 값은 반드시 실제 존재하는 값만 사용** (n8n MCP로 사전 확인)
