#!/usr/bin/env python3
"""모든 workflow JSON 파일을 pretty-print (indent=2) 형식으로 변환합니다."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main():
    paths = sorted(Path("projects").glob("*/workflows/*.json"))
    if not paths:
        print("변환할 파일 없음")
        return

    for path in paths:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ {path}")

    print(f"\n총 {len(paths)}개 파일 변환 완료")


if __name__ == "__main__":
    main()
