# n8n 프로젝트 아카이브

n8n 워크플로우 자동화 프로젝트 모음입니다.

---

## 프로젝트 목록

| 폴더 | 설명 | 상태 |
|------|------|------|
| `projects/news-briefing-automation/` | 경제·증시 뉴스 수집·분석·텔레그램 브리핑 | 완료 |
| `projects/telegram-to-obsidian/` | 텔레그램 메시지 → OneDrive → Obsidian .md 자동 저장 | 완료 |

---

## 프로젝트 종료 체크리스트

새 프로젝트를 완료하고 GitHub에 반영할 때 아래 순서를 따른다.

### 1. n8n에서 최신 워크플로우 JSON 가져오기

```python
import json, urllib.request

N8N_URL = "https://primary-production-90c7.up.railway.app"
N8N_API_KEY = "YOUR_N8N_API_KEY"
WORKFLOW_ID = "워크플로우_ID"

url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
headers = {"X-N8N-API-KEY": N8N_API_KEY, "Accept": "application/json"}
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    wf = json.loads(resp.read().decode("utf-8"))

with open("projects/{project-name}/workflows/{name}.json", "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=2)
```

### 2. README.md 작성

`projects/{project-name}/README.md` 를 생성한다. 포함 내용:
- 워크플로우가 하는 일 (1~2줄 요약)
- 전체 흐름 다이어그램 (`Trigger → 처리 → 저장 → 알림`)
- 지원 기능/타입
- 사전 준비 (필요한 서비스, API 키)
- 설치 방법 (Import → Credential → Variables → 경로 수정)
- 에러 처리 정책
- 이 프로젝트에서 배운 것들 (선택)

### 3. 시크릿 확인 후 커밋

파이썬 파일에 하드코딩된 시크릿(API 키, 봇 토큰 등)은 반드시 플레이스홀더로 교체:
```
YOUR_N8N_API_KEY
YOUR_BOT_TOKEN
YOUR_SUPABASE_SECRET_KEY
```

```bash
# main 브랜치 기준으로 작업
git checkout main-local   # 또는 git checkout -b main-local origin/main

# 파일 추가
git add projects/{project-name}/

git commit -m "Add {project-name} workflow project"
git push origin main-local:main
```

> **주의**: GitHub가 시크릿을 감지하면 push가 차단됨.
> 차단 시 → `git reset --soft HEAD~1` → 시크릿 교체 → 재커밋

### 4. CLAUDE.md 프로젝트 목록 업데이트

루트 `CLAUDE.md`의 프로젝트 목록 테이블에 새 프로젝트를 추가한다.

---

## 저장소 정보

- GitHub: `https://github.com/TaeHee324/n8n`
- 기본 브랜치: `main`
- n8n 인스턴스: `https://primary-production-90c7.up.railway.app`
