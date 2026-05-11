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
