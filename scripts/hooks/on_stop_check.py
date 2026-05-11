#!/usr/bin/env python3
"""Stop hook: 미커밋 변경사항 알림 및 .env staging 경고"""
import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()


def main():
    has_issue = False

    staged = run("git diff --cached --name-only")
    if ".env" in staged.splitlines():
        print("❌ 경고: .env 파일이 staging에 포함되어 있습니다! 커밋 전 반드시 제거하세요.")
        has_issue = True

    status = run("git status --short")
    if status:
        print("⚠️  미커밋 변경사항 있음:")
        for line in status.splitlines()[:10]:
            print(f"   {line}")

    sys.exit(1 if has_issue else 0)


if __name__ == "__main__":
    main()
