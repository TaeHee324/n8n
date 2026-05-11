#!/usr/bin/env python3
"""projects/ 하위 모든 workflow JSON을 검증합니다."""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


REQUIRED_FIELDS = ["name", "nodes", "connections"]

SECURITY_PATTERNS = [
    (r"bot\d{5,}:[A-Za-z0-9_-]{30,}", "Telegram Bot Token 하드코딩 의심"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI API 키 하드코딩 의심"),
    (r'"password"\s*:\s*"[^"]+"', "패스워드 하드코딩 의심"),
]

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

    for field in REQUIRED_FIELDS:
        if not data.get(field):
            errors.append(f"필수 필드 누락: {field}")

    if content.count("\n") < 10:
        warnings.append("compact 형식 — pretty-print 권장 (python3 scripts/format_json.py)")

    nodes = {n["name"]: n.get("type", "") for n in data.get("nodes", [])}
    referenced = set()
    for src, dests in data.get("connections", {}).items():
        referenced.add(src)
        for branch in dests.get("main", []):
            for conn in branch or []:
                referenced.add(conn.get("node", ""))

    trigger_nodes = {name for name, typ in nodes.items() if typ in TRIGGER_TYPES}
    annotation_nodes = {name for name in nodes if name.startswith("Sticky Note")}
    unconnected = set(nodes.keys()) - referenced - trigger_nodes - annotation_nodes
    if unconnected:
        warnings.append(f"연결 끊긴 노드 의심: {', '.join(sorted(unconnected))}")

    for pattern, msg in SECURITY_PATTERNS:
        if re.search(pattern, content):
            # URL 컨텍스트 내 토큰은 경고로 처리
            in_url = bool(re.search(r'"url"\s*:\s*"[^"]*' + pattern, content))
            if in_url:
                warnings.append(f"보안 주의 (URL 내 토큰): {msg}")
            else:
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
        for error in errors:
            print(f"     ❌ {error}")
            total_errors += 1
        for warning in warnings:
            print(f"     ⚠️  {warning}")

    print()
    if total_errors:
        print(f"총 {total_errors}개 에러 발견")
        sys.exit(1)

    print("모든 워크플로우 검증 통과 ✅")


if __name__ == "__main__":
    main()
