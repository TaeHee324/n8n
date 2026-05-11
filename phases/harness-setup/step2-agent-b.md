# Step 2 — Agent B: `scripts/` 영역

## 역할 및 규칙
- **담당 영역: `scripts/` 폴더만 (신규 파일만 생성)**
- `.claude/`, `docs/`, `templates/`, `projects/` 등 다른 폴더 건드리지 않음
- 모든 스크립트는 Python 3 / Windows 호환으로 작성
- `pathlib.Path` 사용, 슬래시 하드코딩 금지

## 작업 디렉토리
`C:\Users\PC\Desktop\n8n`

## 프로젝트 컨텍스트
- n8n 워크플로우 자동화 프로젝트
- n8n 인스턴스: `https://primary-production-90c7.up.railway.app`
- API 키: 프로젝트 루트 `.env`의 `N8N_API_KEY`
- PUT payload 허용 필드: `name`, `nodes`, `connections`, `settings`(executionOrder/timezone/callerPolicy만), `staticData`
- 플랫폼: Windows 11 / Python 3

---

## 생성할 파일 (8개)

---

### 1. `scripts/hooks/pre_bash_check.py`

PreToolUse hook — 위험한 Bash 명령어 자동 차단.
Claude Code가 Bash 도구 호출 직전에 실행. stdin으로 JSON 수신, exit 1이면 차단.

```python
#!/usr/bin/env python3
"""PreToolUse hook: 위험한 Bash 명령어 차단"""
import json, sys, re

BLOCKED_PATTERNS = [
    (r'rm\s+-[rf]{1,2}\s+[/\\.]',          "rm -rf 사용 금지"),
    (r'rm\s+-[rf]{1,2}\s+\*',              "rm -rf * 사용 금지"),
    (r'git\s+push\s+(--force|-f)\b',        "git push --force 금지"),
    (r'git\s+reset\s+--hard',               "git reset --hard 금지"),
    (r'git\s+clean\s+-f',                   "git clean -f 금지"),
    (r'git\s+checkout\s+--\s+\.',           "git checkout -- . 금지"),
    (r'DROP\s+TABLE',                        "DROP TABLE 금지"),
    (r'del\s+/[fFsS]',                      "del /f /s 금지"),
    (r'format\s+[cCdD]:',                   "format 드라이브 금지"),
    (r'Remove-Item\s+.*-Recurse.*-Force',   "Remove-Item -Recurse -Force 금지"),
]

def main():
    try:
        data = json.load(sys.stdin)
        cmd = data.get("tool_input", {}).get("command", "")
    except Exception:
        sys.exit(0)

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            print(f"⛔ 위험한 명령어 차단: {reason}")
            print(f"   명령어: {cmd[:150]}")
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### 2. `scripts/hooks/post_write_validate.py`

PostToolUse hook — Write/Edit 후 workflow JSON 자동 검증.

```python
#!/usr/bin/env python3
"""PostToolUse hook: workflow JSON 수정 후 문법 검사"""
import json, sys
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
        file_path = data.get("tool_input", {}).get("file_path", "")
    except Exception:
        sys.exit(0)

    path = Path(file_path)

    # workflow JSON 파일만 검사
    if not (path.suffix == ".json" and "workflows" in path.parts):
        sys.exit(0)

    if not path.exists():
        sys.exit(0)

    try:
        content = path.read_text(encoding="utf-8")
        json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 문법 오류: {path.name}")
        print(f"   {e}")
        sys.exit(1)

    # compact 형식 경고
    if content.count("\n") < 10:
        print(f"⚠️  {path.name} 이 compact 형식입니다. pretty-print 권장")
        print("   실행: python3 scripts/format_json.py")

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### 3. `scripts/hooks/on_stop_check.py`

Stop hook — 세션 종료 시 미커밋 변경 알림 + .env staging 경고.

```python
#!/usr/bin/env python3
"""Stop hook: 미커밋 변경사항 알림 및 .env staging 경고"""
import subprocess, sys

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def main():
    has_issue = False

    # .env staging 체크 (치명적)
    staged = run("git diff --cached --name-only")
    if ".env" in staged.splitlines():
        print("❌ 경고: .env 파일이 staging에 포함되어 있습니다! 커밋 전 반드시 제거하세요.")
        has_issue = True

    # 미커밋 변경사항 알림 (정보성)
    status = run("git status --short")
    if status:
        print("⚠️  미커밋 변경사항 있음:")
        for line in status.splitlines()[:10]:
            print(f"   {line}")

    sys.exit(1 if has_issue else 0)

if __name__ == "__main__":
    main()
```

---

### 4. `scripts/deploy.py`

로컬 workflow JSON → n8n REST API PUT 배포.

```python
#!/usr/bin/env python3
"""로컬 workflow JSON을 n8n 서버에 배포합니다.

사용법:
  python3 scripts/deploy.py <workflow_id> <json_path>

예시:
  python3 scripts/deploy.py WW51yZ7oEmyp01kW projects/chart-automation/workflows/chart-automation.json
"""
import json, sys, os
from pathlib import Path
import urllib.request, urllib.error

BASE_URL = "https://primary-production-90c7.up.railway.app"
ALLOWED_SETTINGS_KEYS = {"executionOrder", "timezone", "callerPolicy"}


def load_env():
    env = {}
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    workflow_id, json_path = sys.argv[1], sys.argv[2]

    env = load_env()
    api_key = env.get("N8N_API_KEY") or os.environ.get("N8N_API_KEY", "")
    if not api_key:
        print("❌ N8N_API_KEY를 .env에서 찾을 수 없습니다")
        sys.exit(1)

    path = Path(json_path)
    if not path.exists():
        print(f"❌ 파일 없음: {json_path}")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # PUT에 허용된 필드만 포함
    settings = {k: v for k, v in data.get("settings", {}).items()
                if k in ALLOWED_SETTINGS_KEYS}
    payload = {
        "name": data["name"],
        "nodes": data["nodes"],
        "connections": data["connections"],
        "settings": settings,
        "staticData": data.get("staticData"),
    }

    req_body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/workflows/{workflow_id}",
        data=req_body,
        method="PUT",
        headers={
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json",
        },
    )

    print(f"🚀 배포 중: {data['name']} → {workflow_id}")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"✅ 배포 완료: {result.get('name')} (ID: {result.get('id')})")
            print(f"   URL: {BASE_URL}/workflow/{workflow_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {e.code}: {body[:400]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

### 5. `scripts/export.py`

n8n 서버 → 로컬 workflow JSON 저장.

```python
#!/usr/bin/env python3
"""n8n 서버에서 워크플로우를 가져와 로컬 JSON으로 저장합니다.

사용법:
  python3 scripts/export.py <workflow_id> [output_path]

예시:
  python3 scripts/export.py WW51yZ7oEmyp01kW projects/chart-automation/workflows/chart-automation.json
"""
import json, sys, os
from pathlib import Path
import urllib.request, urllib.error

BASE_URL = "https://primary-production-90c7.up.railway.app"


def load_env():
    env = {}
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    env = load_env()
    api_key = env.get("N8N_API_KEY") or os.environ.get("N8N_API_KEY", "")
    if not api_key:
        print("❌ N8N_API_KEY를 .env에서 찾을 수 없습니다")
        sys.exit(1)

    workflow_id = sys.argv[1]
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": api_key},
    )

    print(f"📥 가져오는 중: {workflow_id}")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)

    # 저장 경로 결정
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        name = data.get("name", workflow_id).replace(" ", "-").lower()
        out_path = Path(f"{name}.json")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 저장 완료: {out_path}")
    print(f"   이름: {data.get('name')}, 노드 수: {len(data.get('nodes', []))}")


if __name__ == "__main__":
    main()
```

---

### 6. `scripts/validate.py`

workflow JSON 검증 — 필수 필드, 연결 끊김, 보안 패턴 탐지.

```python
#!/usr/bin/env python3
"""projects/ 하위 모든 workflow JSON을 검증합니다."""
import json, sys, re
from pathlib import Path

REQUIRED_FIELDS = ["name", "nodes", "connections"]

SECURITY_PATTERNS = [
    (r'bot\d{5,}:[A-Za-z0-9_-]{30,}',  "Telegram Bot Token 하드코딩 의심"),
    (r'sk-[A-Za-z0-9]{20,}',           "OpenAI API 키 하드코딩 의심"),
    (r'"password"\s*:\s*"[^"]+"',       "패스워드 하드코딩 의심"),
]

# 트리거 노드는 연결 시작점이므로 단방향 연결 경고 제외
TRIGGER_TYPES = {
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.telegramTrigger",
    "n8n-nodes-base.rssFeedReadTrigger",
    "n8n-nodes-base.webhookTrigger",
}


def validate(path: Path):
    errors, warnings = [], []

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return [f"JSON 파싱 실패: {e}"], []

    # 필수 필드
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"필수 필드 누락: {field}")

    # compact 형식 경고
    if content.count("\n") < 10:
        warnings.append("compact 형식 — pretty-print 권장 (python3 scripts/format_json.py)")

    # 연결 끊긴 노드 탐지
    nodes = {n["name"]: n.get("type", "") for n in data.get("nodes", [])}
    referenced = set()
    for src, dests in data.get("connections", {}).items():
        referenced.add(src)
        for branch in dests.get("main", []):
            for conn in (branch or []):
                referenced.add(conn.get("node", ""))

    trigger_nodes = {name for name, typ in nodes.items() if typ in TRIGGER_TYPES}
    unconnected = set(nodes.keys()) - referenced - trigger_nodes - {"Sticky Note"}
    if unconnected:
        warnings.append(f"연결 끊긴 노드 의심: {', '.join(sorted(unconnected))}")

    # 보안 패턴
    for pattern, msg in SECURITY_PATTERNS:
        if re.search(pattern, content):
            errors.append(f"보안 경고: {msg}")

    return errors, warnings


def main():
    project_root = Path("projects")
    if not project_root.exists():
        print("projects/ 폴더가 없습니다")
        sys.exit(0)

    paths = sorted(project_root.glob("*/workflows/*.json"))
    if not paths:
        print("검증할 workflow JSON 파일이 없습니다")
        sys.exit(0)

    total_errors = 0
    for path in paths:
        errors, warnings = validate(path)
        icon = "❌" if errors else ("⚠️ " if warnings else "✅")
        print(f"{icon} {path}")
        for e in errors:
            print(f"     ❌ {e}")
            total_errors += 1
        for w in warnings:
            print(f"     ⚠️  {w}")

    print()
    if total_errors:
        print(f"총 {total_errors}개 에러 발견")
        sys.exit(1)
    else:
        print("모든 워크플로우 검증 통과 ✅")

if __name__ == "__main__":
    main()
```

---

### 7. `scripts/format_json.py`

`projects/*/workflows/*.json` 전체 pretty-print 변환.

```python
#!/usr/bin/env python3
"""모든 workflow JSON 파일을 pretty-print (indent=2) 형식으로 변환합니다."""
import json
from pathlib import Path


def main():
    paths = sorted(Path("projects").glob("*/workflows/*.json"))
    if not paths:
        print("변환할 파일 없음")
        return

    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ {path}")

    print(f"\n총 {len(paths)}개 파일 변환 완료")


if __name__ == "__main__":
    main()
```

---

### 8. `scripts/execute.py`

harness_framework의 단계별 실행 엔진. GitHub에서 원본을 가져와 n8n 프로젝트용으로 조정.

**실행 방법:**
1. `https://raw.githubusercontent.com/jha0313/harness_framework/main/scripts/execute.py` 에서 원본 코드 가져오기 (WebFetch 사용)
2. 아래 항목 조정:
   - `stop_command` 기본값을 `npm run test` → `python3 scripts/validate.py` 로 변경
   - 상단 docstring에 n8n 프로젝트 컨텍스트 추가
   - 파일 상단 주석: `# Adapted from jha0313/harness_framework for n8n workflow project`
3. `scripts/execute.py` 로 저장

---

## 완료 기준
- [ ] `scripts/hooks/` 폴더에 3개 Python 파일 생성됨
- [ ] `scripts/` 에 5개 Python 파일 생성됨 (deploy, export, validate, format_json, execute)
- [ ] 모든 스크립트 `python3 --version` 호환 확인 (문법 오류 없음)
- [ ] `.claude/`, `docs/`, `templates/`, `projects/` 건드리지 않음
