#!/usr/bin/env python3
"""PreToolUse hook: 위험한 Bash 명령어 차단"""
import json
import re
import sys


BLOCKED_PATTERNS = [
    (r"rm\s+-[rf]{1,2}\s+[/\\.]", "rm -rf 사용 금지"),
    (r"rm\s+-[rf]{1,2}\s+\*", "rm -rf * 사용 금지"),
    (r"git\s+push\s+(--force|-f)\b", "git push --force 금지"),
    (r"git\s+reset\s+--hard", "git reset --hard 금지"),
    (r"git\s+clean\s+-f", "git clean -f 금지"),
    (r"git\s+checkout\s+--\s+\.", "git checkout -- . 금지"),
    (r"DROP\s+TABLE", "DROP TABLE 금지"),
    (r"del\s+/[fFsS]", "del /f /s 금지"),
    (r"format\s+[cCdD]:", "format 드라이브 금지"),
    (r"Remove-Item\s+.*-Recurse.*-Force", "Remove-Item -Recurse -Force 금지"),
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
