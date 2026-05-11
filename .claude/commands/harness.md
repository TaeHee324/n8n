# /harness — n8n 워크플로우 제작 플로우

사용자가 `/harness` 를 입력하면 아래 단계를 순서대로 진행한다.

## 실행 단계

### Phase 1: 컨텍스트 파악
1. 사용자에게 워크플로우 이름과 목적을 질문
2. `projects/{name}/SOP.md` 존재 여부 확인
   - 있으면 읽고 요약
   - 없으면 `templates/project/SOP.md` 복사 후 사용자에게 작성 안내

### Phase 2: 변수 생존 검증 표 작성
CLAUDE.md의 "변수 생존 검증 원칙"에 따라 표를 작성하고 사용자 확인.

| 변수명 | 생성 노드 | 사용 노드 | 분기 후 소실 여부 | 해결 방식 |
|--------|---------|---------|--------------|---------|

### Phase 3: 노드 설계
- `n8n-workflow-patterns` 스킬 참고하여 최적 노드 구성 설계
- 연결 다이어그램 텍스트로 표현 후 사용자 확인

### Phase 4: 워크플로우 JSON 생성
- `templates/workflow/base.json` 기반으로 작성
- `projects/{name}/workflows/{name}.json` 에 저장
- `python3 scripts/validate.py` 실행하여 검증

### Phase 5: 배포 (선택)
- 사용자가 원하면: `python3 scripts/deploy.py {workflow_id} {json_path}`
- Credential 설정 가이드 제공

### Phase 6: 커밋
CLAUDE.md의 Git 커밋 규칙에 따라 커밋 메시지 제안 후 사용자 확인.
