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
