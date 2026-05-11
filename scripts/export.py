#!/usr/bin/env python3
"""n8n 서버에서 워크플로우를 가져와 로컬 JSON으로 저장합니다.

사용법:
  python3 scripts/export.py <workflow_id> [output_path]

예시:
  python3 scripts/export.py WW51yZ7oEmyp01kW projects/chart-automation/workflows/chart-automation.json
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


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

    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        name = data.get("name", workflow_id).replace(" ", "-").lower()
        out_path = Path(f"{name}.json")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 저장 완료: {out_path}")
    print(f"   이름: {data.get('name')}, 노드 수: {len(data.get('nodes', []))}")


if __name__ == "__main__":
    main()
