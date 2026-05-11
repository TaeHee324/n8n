#!/usr/bin/env python3
"""PostToolUse hook: workflow JSON 수정 후 문법 검사"""
import json
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
        file_path = data.get("tool_input", {}).get("file_path", "")
    except Exception:
        sys.exit(0)

    path = Path(file_path)

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

    if content.count("\n") < 10:
        print(f"⚠️  {path.name} 이 compact 형식입니다. pretty-print 권장")
        print("   실행: python3 scripts/format_json.py")

    sys.exit(0)


if __name__ == "__main__":
    main()
