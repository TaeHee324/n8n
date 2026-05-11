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
