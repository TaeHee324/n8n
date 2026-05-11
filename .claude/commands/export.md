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
