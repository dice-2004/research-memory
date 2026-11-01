"""Stop hook（方法A: 機械的チェック）

研究に影響するファイル（src/ configs/ scripts/ outputs/ など）が変更されたのに、
今日のログがその後に更新されていなければ、終了をブロックしてログを書かせる。

- stop_hook_active が true（直前にブロック済み）のときは通す（無限ループ防止）
- 同じ変更に対しては1回しかブロックしない（記録不要と判断された場合に繰り返さないため）
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    find_root,
    load_config,
    load_state,
    read_input,
    run_git,
    mtime,
    newest_change,
    save_state,
    today_log_rel,
)


def main():
    data = read_input()
    if data.get("stop_hook_active"):
        return 0
    root = find_root(data)
    if not root:
        return 0
    cfg = load_config(root)
    watch = [w for w in cfg.get("watch", []) if os.path.exists(os.path.join(root, w))]
    if not watch:
        return 0

    changed_at, changed_path = newest_change(root, watch)
    log_rel = today_log_rel(cfg)
    log_at = mtime(os.path.join(root, log_rel))
    state = load_state(root)

    if changed_at <= log_at or changed_at <= state.get("last_notified_change", 0.0):
        return 0

    state["last_notified_change"] = changed_at
    save_state(root, state)
    # Claude に渡す理由文（AI だけが読むので英語。記録そのものは日本語で書かせる）
    reason = (
        f"A change that may affect the research (e.g., {changed_path}) is newer than the last update of today's log {log_rel}. "
        "If this change is a research event (running an experiment or its results, a change to evaluation or preprocessing, "
        "a code change that affects results, etc.), append a block to today's log following the research-log Skill "
        "(in Japanese) and propose a MEMORY.md update if needed. "
        "If it does not affect the research (typo fix, refactoring, etc.), say in one line (in Japanese) that no record "
        "is needed and finish; the same change will not block again."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
