# Step 5 — Orchestrator After (병렬 완료 후 실행)

## 역할
step1 ~ step4 가 모두 완료된 후 오케스트레이터가 실행하는 통합·검수 단계.

## 사전 조건
- [ ] step1 (Agent A): `.claude/settings.json` + 6개 커맨드 파일 생성 확인
- [ ] step2 (Agent B): `scripts/` 하위 8개 파일 생성 확인
- [ ] step3 (Agent C): `templates/` 하위 3개 파일 생성 확인
- [ ] step4 (Agent D): `docs/` 하위 3개 파일 생성 확인

---

## 실행 단계

### 1. 전체 결과물 검수

아래 명령으로 생성된 파일 목록 확인:
```bash
find . -not -path "./.git/*" -not -path "./phases/*" -not -path "./__pycache__/*" -type f | sort
```

**기대하는 신규 파일 목록 (14개):**
```
.claude/settings.json
.claude/commands/harness.md
.claude/commands/new-project.md
.claude/commands/deploy.md
.claude/commands/export.md
.claude/commands/validate.md
.claude/commands/review.md
scripts/execute.py
scripts/deploy.py
scripts/export.py
scripts/validate.py
scripts/format_json.py
scripts/hooks/pre_bash_check.py
scripts/hooks/post_write_validate.py
scripts/hooks/on_stop_check.py
templates/project/SOP.md
templates/project/README.md
templates/workflow/base.json
docs/ARCHITECTURE.md
docs/ADR.md
docs/ERRORS.md
```

**검수 항목:**
- `.claude/settings.json` JSON 문법 오류 없음
- `templates/workflow/base.json` JSON 문법 오류 없음
- `scripts/validate.py` 실행 테스트: `python3 scripts/validate.py`
- `scripts/format_json.py` 실행 테스트: `python3 scripts/format_json.py`

---

### 2. `CLAUDE.md` 보강

기존 `CLAUDE.md` 끝에 아래 섹션 추가:

```markdown
---

## 슬래시 커맨드 목록

| 커맨드 | 역할 |
|--------|------|
| `/harness` | 새 워크플로우 전체 제작 플로우 (SOP → 설계 → 생성 → 검증 → 배포) |
| `/new-project` | 새 프로젝트 스캐폴드 자동 생성 (폴더 + SOP + README + base workflow) |
| `/deploy` | 로컬 JSON → n8n 서버 배포 (`scripts/deploy.py` 연동) |
| `/export` | n8n 서버 → 로컬 JSON 저장 (`scripts/export.py` 연동) |
| `/validate` | 워크플로우 JSON 검증 (`scripts/validate.py` 연동) |
| `/review` | 변경사항 리뷰 후 커밋 메시지 제안 |

---

## 자동화 스크립트

| 스크립트 | 사용법 | 설명 |
|---------|--------|------|
| `scripts/deploy.py` | `python3 scripts/deploy.py {id} {json_path}` | 로컬 JSON → n8n 배포 |
| `scripts/export.py` | `python3 scripts/export.py {id} [output_path]` | n8n → 로컬 JSON 저장 |
| `scripts/validate.py` | `python3 scripts/validate.py` | 전체 워크플로우 JSON 검증 |
| `scripts/format_json.py` | `python3 scripts/format_json.py` | 전체 JSON pretty-print 변환 |
| `scripts/execute.py` | `python3 scripts/execute.py {task-name}` | harness 단계별 실행 |

---

## 참고 문서

| 문서 | 내용 |
|------|------|
| `docs/ARCHITECTURE.md` | 전체 자동화 시스템 구조 |
| `docs/ADR.md` | 주요 설계 결정 기록 |
| `docs/ERRORS.md` | 에러 패턴 및 해결법 |
| `templates/project/SOP.md` | 새 프로젝트 SOP 템플릿 |
| `templates/workflow/base.json` | 기본 워크플로우 뼈대 |
```

---

### 3. 루트 `README.md` 업데이트

기존 README.md의 프로젝트 구조 섹션에 신규 폴더 설명 추가:

```markdown
## 폴더 구조

| 폴더/파일 | 설명 |
|---------|------|
| `projects/` | 각 워크플로우 프로젝트 (SOP, README, workflow JSON) |
| `scripts/` | 배포·내보내기·검증 자동화 스크립트 |
| `templates/` | 새 프로젝트 생성 시 사용하는 템플릿 |
| `docs/` | 시스템 아키텍처·설계 결정·에러 패턴 문서 |
| `.claude/` | Claude Code 설정 및 슬래시 커맨드 |
| `phases/` | harness 실행 계획 파일 (git 추적) |
| `CLAUDE.md` | Claude Code 작업 지침 |
```

---

### 4. Memory 파일 보강

`C:/Users/PC/.claude/projects/C--Users-PC-Desktop-n8n/memory/` 에서:

**`MEMORY.md`** 에 아래 항목 추가:
```
- [Harness 구조](project_harness.md) — scripts/, templates/, docs/, .claude/commands/ 구축 완료
- [워크플로우 ID](reference_workflow_ids.md) — 3개 워크플로우 ID 및 경로 매핑
```

**`project_harness.md`** 신규 생성:
```markdown
---
name: Harness 구조 완성
description: n8n 프로젝트에 harness 프레임워크 구축 완료 상태
type: project
---

harness 구축 완료 (phases/harness-setup/ 기반).

**Why:** Claude Code 작업 효율화 — 반복 작업 스크립트화, 슬래시 커맨드로 워크플로우 표준화

**How to apply:** 
- 새 세션 시작 시 /harness, /validate 등 커맨드 사용 가능
- 배포 시 python3 scripts/deploy.py 사용 (수동 import 불필요)
- 에러 발생 시 docs/ERRORS.md 먼저 확인
```

**`reference_workflow_ids.md`** 신규 생성:
```markdown
---
name: 워크플로우 ID 매핑
description: n8n 워크플로우 ID와 로컬 파일 경로 매핑 테이블
type: reference
---

| 워크플로우 | ID | 로컬 경로 |
|---------|-----|---------|
| Telegram to Obsidian | a5RvxdkYFp9VLw5A | projects/telegram-to-obsidian/workflows/telegram-to-obsidian.json |
| 경제지표 차트 자동화 | WW51yZ7oEmyp01kW | projects/chart-automation/workflows/chart-automation.json |
| 뉴스 브리핑 자동화 | (n8n UI에서 확인 필요) | projects/news-briefing-automation/workflows/news-briefing-automation.json |
```

---

### 5. 최종 커밋

커밋 전 사전 점검 (CLAUDE.md 체크리스트 준수):
1. `python3 scripts/validate.py` 실행 → 통과 확인
2. `python3 scripts/format_json.py` 실행 → JSON pretty-print 확인
3. `.env` 스테이징 포함 여부 확인

커밋:
```bash
git add .claude/settings.json .claude/commands/ scripts/ templates/ docs/ phases/ CLAUDE.md README.md .gitignore
git commit -m "feat: add harness framework (hooks, scripts, templates, docs, commands)"
```

---

## 완료 기준
- [ ] 전체 21개 신규 파일 존재 확인
- [ ] `python3 scripts/validate.py` 정상 실행
- [ ] `CLAUDE.md` 슬래시 커맨드·스크립트·참고 문서 섹션 추가됨
- [ ] `README.md` 폴더 구조 업데이트됨
- [ ] Memory 파일 3개 (MEMORY.md 업데이트 + 신규 2개) 완료
- [ ] 최종 커밋 완료
