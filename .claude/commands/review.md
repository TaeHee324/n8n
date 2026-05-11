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
