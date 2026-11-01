"""PostToolUse hook: エージェントがファイル編集ツールで変えたファイルを記録する。

コミットは依頼されるまでしないので、未コミットの変更がセッションをまたいで残る。
SessionStart で「エージェントの変更か、ユーザーの変更か」を見分けるために、
編集したファイルの相対パスと、編集直後の更新時刻を .git/research-memory/state.json に残す。
（Bash での変更は記録されない。）
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from common import find_root, load_config, load_state, mtime, now, read_input, save_state, state_lock  # noqa: E402

FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MAX_ENTRIES = 500


def main():
    data = read_input()
    if data.get("tool_name") not in FILE_TOOLS:
        return 0
    root = find_root(data)
    if not root:
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path")
    if not path:
        return 0
    abs_path = os.path.realpath(path if os.path.isabs(path) else os.path.join(root, path))
    real_root = os.path.realpath(root)
    if not abs_path.startswith(real_root + os.sep):
        return 0
    rel = os.path.relpath(abs_path, real_root).replace(os.sep, "/")

    with state_lock(root):
        state = load_state(root)
        edits = state.get("agent_edits", {})
        try:
            when = now(load_config(root)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            when = datetime.now().strftime("%Y-%m-%d %H:%M")
        edits[rel] = {"mtime": mtime(abs_path), "at": when}
        if len(edits) > MAX_ENTRIES:
            for k in sorted(edits, key=lambda k: edits[k].get("mtime", 0))[: len(edits) - MAX_ENTRIES]:
                del edits[k]
        state["agent_edits"] = edits
        save_state(root, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
