#!/usr/bin/env python3
"""로컬 workflow JSON을 n8n 서버에 배포합니다.

사용법:
  python3 scripts/deploy.py <workflow_id> <json_path>

예시:
  python3 scripts/deploy.py WW51yZ7oEmyp01kW projects/chart-automation/workflows/chart-automation.json
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


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

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    settings = {
        k: v
        for k, v in data.get("settings", {}).items()
        if k in ALLOWED_SETTINGS_KEYS
    }
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
