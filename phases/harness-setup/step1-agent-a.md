# Step 1 — Agent A: `.claude/` 영역

## 역할 및 규칙
- **담당 영역: `.claude/` 폴더만 (신규 파일만 생성)**
- `settings.local.json` 은 절대 수정하지 않음
- `scripts/`, `docs/`, `templates/`, `projects/` 등 다른 폴더 건드리지 않음

## 작업 디렉토리
`C:\Users\PC\Desktop\n8n`

## 프로젝트 컨텍스트
- n8n 워크플로우 자동화 프로젝트 (3개 워크플로우 운영 중)
- n8n 인스턴스: `https://primary-production-90c7.up.railway.app`
- API 키: 프로젝트 루트 `.env`의 `N8N_API_KEY`
- Hook 스크립트: `scripts/hooks/` (Agent B가 별도 생성 — 경로만 참조)
- 플랫폼: Windows 11 / Python 3 사용 가능

---

## 생성할 파일 (7개)

---

### 1. `.claude/settings.json`

Claude Code가 세션 중 자동으로 실행하는 hook 설정. git에 커밋되어 공유됨.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/hooks/pre_bash_check.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/hooks/post_write_validate.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/hooks/on_stop_check.py"
          }
        ]
      }
    ]
  }
}
```

---

### 2. `.claude/commands/harness.md`

n8n 워크플로우 전체 제작 플로우를 안내하는 슬래시 커맨드 (`/harness`).

```markdown
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
```

---

### 3. `.claude/commands/new-project.md`

새 n8n 프로젝트 스캐폴드 자동 생성 커맨드 (`/new-project`).

```markdown
# /new-project — 새 프로젝트 스캐폴드 생성

사용자가 `/new-project` 를 입력하면 아래를 실행한다.

## 실행 단계

1. 사용자에게 프로젝트 이름 질문 (예: `stock-alert-automation`)
2. 아래 폴더/파일 구조 생성:

```
projects/{name}/
├── SOP.md       ← templates/project/SOP.md 복사 후 {PROJECT_NAME} 치환
├── README.md    ← templates/project/README.md 복사 후 {PROJECT_NAME} 치환
└── workflows/
    └── {name}.json  ← templates/workflow/base.json 복사
```

3. CLAUDE.md 프로젝트 목록 테이블에 새 항목 추가 (사용자 확인 후)
4. README.md 루트 프로젝트 목록 테이블에 새 항목 추가 (사용자 확인 후)
5. 생성된 SOP.md 파일 열어서 내용 작성 시작
```

---

### 4. `.claude/commands/deploy.md`

로컬 workflow JSON을 n8n 서버에 배포하는 커맨드 (`/deploy`).

```markdown
# /deploy — n8n 서버에 워크플로우 배포

사용자가 `/deploy` 를 입력하면 아래를 실행한다.

## 실행 단계

1. `projects/*/workflows/*.json` 목록 표시
2. 사용자에게 배포할 워크플로우 선택 요청
3. n8n 워크플로우 ID 확인 (workflow JSON의 `id` 필드 또는 사용자에게 확인)
4. 배포 전 확인 메시지 출력:
   - 대상 파일
   - 워크플로우 ID
   - n8n 인스턴스 URL
5. 사용자 승인 후 실행:
   ```
   python3 scripts/deploy.py {workflow_id} {json_path}
   ```
6. 결과 확인 및 n8n 워크플로우 URL 제공:
   `https://primary-production-90c7.up.railway.app/workflow/{workflow_id}`
```

---

### 5. `.claude/commands/export.md`

n8n 서버에서 최신 워크플로우를 로컬로 가져오는 커맨드 (`/export`).

```markdown
# /export — n8n 서버에서 워크플로우 가져오기

사용자가 `/export` 를 입력하면 아래를 실행한다.

## 실행 단계

1. `index.json`의 `projectContext.workflows` 목록 표시
2. 사용자에게 export할 워크플로우 선택 요청
3. 실행:
   ```
   python3 scripts/export.py {workflow_id} {local_json_path}
   ```
4. 로컬 파일과 기존 파일의 diff 요약 출력
5. 변경사항이 있으면 커밋 여부 질문
```

---

### 6. `.claude/commands/validate.md`

워크플로우 JSON 검증 커맨드 (`/validate`).

```markdown
# /validate — 워크플로우 JSON 검증

사용자가 `/validate` 를 입력하면 아래를 실행한다.

## 실행 단계

1. 실행:
   ```
   python3 scripts/validate.py
   ```
2. 결과 파싱:
   - ✅ 이면 "모든 워크플로우 검증 통과" 출력
   - ⚠️ 이면 경고 내용 설명 및 수정 여부 질문
   - ❌ 이면 에러 내용 분석 후 수정 방법 제안
3. 에러가 있으면 `docs/ERRORS.md` 에서 해당 패턴 검색하여 참고 해결법 제시
```

---

### 7. `.claude/commands/review.md`

변경사항 리뷰 커맨드 (`/review`).

```markdown
# /review — 변경사항 리뷰

사용자가 `/review` 를 입력하면 아래를 실행한다.

## 실행 단계

1. `git diff --stat` 실행하여 변경 파일 목록 확인
2. `git diff` 실행하여 상세 변경 내용 확인
3. 변경된 workflow JSON 파일에 대해:
   - 추가/수정/삭제된 노드 요약
   - 연결 변경 사항 요약
   - `python3 scripts/validate.py` 실행하여 문제 없는지 확인
4. 문제점 있으면 지적
5. 커밋 준비 됐으면 CLAUDE.md 커밋 규칙에 따라 메시지 제안
```

---

## 완료 기준
- [ ] `.claude/settings.json` 생성됨
- [ ] `.claude/commands/` 폴더에 7개 `.md` 파일 생성됨
- [ ] JSON 문법 오류 없음 (`settings.json`)
- [ ] `.claude/settings.local.json` 수정 안 함
- [ ] 다른 폴더 건드리지 않음
