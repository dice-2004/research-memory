"""PreCompact hook: コンテキスト圧縮の直前に、会話の全文を保存する。

圧縮自体はブロックしない（ブロックするとコンテキストがあふれて作業が止まるため）。
代わりに会話全文を .git/research-memory/transcripts/ に保存し、
圧縮直後の SessionStart hook がその場所をエージェントに伝え、未記録の内容をログに残させる。
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    cleanup_transcripts,
    find_root,
    load_config,
    load_state,
    now,
    read_input,
    save_state,
    state_lock,
    state_dir,
)


def main():
    data = read_input()
    root = find_root(data)
    if not root:
        return 0
    src = data.get("transcript_path")
    if not src or not os.path.isfile(src):
        return 0
    cfg = load_config(root)
    dest_dir = os.path.join(state_dir(root), "transcripts")
    os.makedirs(dest_dir, exist_ok=True)

    cleanup_transcripts(root, cfg)
    stamp = now(cfg).strftime("%Y%m%d-%H%M%S")
    sid = (data.get("session_id") or "session")[:8]
    dest = os.path.join(dest_dir, f"{stamp}_{sid}.jsonl")
    try:
        shutil.copy2(src, dest)
    except Exception:
        return 0
    with state_lock(root):
        state = load_state(root)
        state["last_transcript_backup"] = dest
        save_state(root, state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
