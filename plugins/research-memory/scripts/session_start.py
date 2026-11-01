"""SessionStart hook: 研究の記憶をセッション冒頭で自動的に読み込ませる。

標準出力のテキストがそのまま Claude のコンテキストに入る（AI だけが読むので英語で書く）。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    cleanup_transcripts,
    find_root,
    load_config,
    load_state,
    newest_change,
    read_input,
    run_git,
    save_state,
    today_log_rel,
)

MAX_TOTAL = 9000  # hook 出力の上限(10,000字)より少し小さく


def toc_of(path, limit=40):
    """ログファイルの目次（## 見出し）を返す。"""
    try:
        with open(path, encoding="utf-8") as f:
            heads = [l.rstrip() for l in f if l.startswith("## ") and "目次" not in l]
        return heads[-limit:]
    except Exception:
        return []


def latest_log(root, exclude):
    logs = os.path.join(root, "logs")
    files = sorted(
        f
        for f in os.listdir(logs)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", f) and f != exclude
    )
    return files[-1] if files else None


def main():
    data = read_input()
    root = find_root(data)
    if not root:
        return 0
    cfg = load_config(root)
    cleanup_transcripts(root, cfg)
    out = []

    # Stop hook の基準点: セッション開始前の変更は対象外にする
    # （開始前の変更は記録済みか、ユーザーの変更として下の git status で意図を確認する）
    if data.get("source") != "compact":
        watch = [w for w in cfg.get("watch", []) if os.path.exists(os.path.join(root, w))]
        if watch:
            st = load_state(root)
            st["last_notified_change"] = max(
                st.get("last_notified_change", 0.0), newest_change(root, watch)[0]
            )
            save_state(root, st)

    out.append("# research-memory: research project memory (loaded automatically)")
    today_rel = today_log_rel(cfg)
    out.append(
        f"Today's log file (今日のログファイル): {today_rel} (time zone {cfg['timezone']}). "
        "Follow the research-log Skill when recording. Write all records in Japanese."
    )

    # 1. MEMORY.md
    with open(os.path.join(root, "MEMORY.md"), encoding="utf-8") as f:
        memory = f.read()
    limit = int(cfg.get("memory_max_chars", 6000))
    out.append("\n## MEMORY.md (current state of the research)")
    if len(memory) > limit:
        out.append(memory[:limit])
        out.append(f"\n(MEMORY.md has {len(memory)} characters and was truncated here. Read the rest with the Read tool.)")
    else:
        out.append(memory)

    # 2. 当日（なければ直近）のログの目次
    today_abs = os.path.join(root, today_rel)
    if os.path.isfile(today_abs):
        heads = toc_of(today_abs)
        out.append(f"\n## Table of contents of {today_rel} (blocks already recorded today)")
        out.extend(heads or ["(no blocks)"])
    else:
        last = latest_log(root, os.path.basename(today_rel))
        if last:
            out.append(f"\n## Table of contents of the latest log logs/{last}")
            out.extend(toc_of(os.path.join(root, "logs", last)) or ["(no blocks)"])

    # 3. archive/ タグのうち MEMORY.md に載っていないもの
    tags = (run_git(["tag", "-l", "archive/*"], root) or "").split()
    missing = [t for t in tags if t not in memory]
    if missing:
        out.append("\n## Unrecorded archive tags")
        out.append(
            "These tags are not listed under 「検討したが却下した選択肢」 in MEMORY.md. "
            "Mention this briefly to the user in your first reply and offer to record the tag name and why it was rejected: "
            + ", ".join(missing)
        )

    # 4. 作業ツリーの変更（ユーザーによるコード変更の検出用）
    status = run_git(["status", "--short"], root)
    if status and status.strip():
        lines = status.strip().splitlines()
        out.append("\n## Uncommitted changes (git status)")
        out.extend(lines[:30])
        if len(lines) > 30:
            out.append(f"... and {len(lines) - 30} more")
        out.append(
            "Any of these changes that you (the agent) did not make were made by the user. "
            "Do not guess their intent: ask the user, and record the answer in the log."
        )
    log = run_git(["log", "-5", "--format=%h %ad %s", "--date=short"], root)
    if log and log.strip():
        out.append("\n## Recent commits")
        out.append(log.strip())

    # 5. コンテキスト圧縮の直後
    if data.get("source") == "compact":
        st = load_state(root)
        saved = st.get("last_transcript_backup")
        out.append("\n## The context was compacted")
        msg = "Details of the conversation before compaction are lost. "
        if saved:
            msg += f"The full pre-compaction transcript is saved at {saved}. "
        msg += (
            "If research events (decisions, experiments, discussion, meeting reports, etc.) happened before compaction "
            "and are not yet in the log, read the saved transcript as needed and record them with the research-log Skill."
        )
        out.append(msg)

    text = "\n".join(out)
    if len(text) > MAX_TOTAL:
        text = text[:MAX_TOTAL] + "\n(Output truncated because it was too long. Read the needed files with the Read tool.)"
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
