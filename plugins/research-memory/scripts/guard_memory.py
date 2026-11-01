"""PreToolUse hook: MEMORY.md への書き込みを毎回ユーザーの承認制にする。

Edit / Write などのファイル編集ツールで MEMORY.md を書き換えようとした場合と、
Bash で MEMORY.md を書き換えそうなコマンドを実行しようとした場合に "ask" を返す。
推測が「確定した事実」として記憶に固定されるのを、人間のレビューで防ぐため。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import find_root, read_input  # noqa: E402

FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# MEMORY.md に触れる Bash のうち、書き込みの可能性があるもの
BASH_WRITE = re.compile(
    r"(>|\btee\b|\bsed\s+-i|\bperl\s+-[a-z]*i|\bmv\b|\bcp\b|\brm\b|\btruncate\b|"
    r"\bpython3?\b|\bgit\s+(checkout|restore|reset|stash|apply|am|merge|rebase)\b)"
)

REASON = (
    "MEMORY.md（研究の記憶）の変更はユーザーの承認が必要です。"
    "差分を確認し、推測が確定事項として書かれていないかを確認してください。"
)


def ask():
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": REASON,
                }
            },
            ensure_ascii=False,
        )
    )


def main():
    data = read_input()
    root = find_root(data)
    if not root:
        return 0
    tool = data.get("tool_name", "")
    tin = data.get("tool_input") or {}
    memory = os.path.realpath(os.path.join(root, "MEMORY.md"))

    if tool in FILE_TOOLS:
        path = tin.get("file_path") or tin.get("notebook_path") or ""
        if path and os.path.realpath(path.replace("\\", "/")) == memory:
            ask()
    elif tool in ("Bash", "PowerShell"):
        cmd = tin.get("command") or ""
        if "MEMORY.md" in cmd and BASH_WRITE.search(cmd):
            ask()
    return 0


if __name__ == "__main__":
    sys.exit(main())
