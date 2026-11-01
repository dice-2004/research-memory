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
    git_status,
    newest_change,
    read_input,
    run_git,
    save_state,
    state_lock,
    today_log_rel,
)

MAX_TOTAL = 9000  # hook 出力の上限(10,000字)より少し小さく


def toc_of(path, limit=40):
    """ログファイルの目次（## 見出し）を返す。"""
    try:
        with open(path, encoding="utf-8") as f:
            heads = [l.rstrip() for l in f if l.startswith("## ") and l.strip() != "## 目次"]
        return heads[-limit:]
    except Exception:
        return []


def plugin_version():
    """プラグインの版（plugin.json の version）。読めなければ空文字。"""
    path = os.path.join(os.path.dirname(__file__), "..", ".claude-plugin", "plugin.json")
    try:
        import json

        with open(path, encoding="utf-8") as f:
            return str(json.load(f).get("version", ""))
    except Exception:
        return ""


def version_tuple(v):
    """'0.3.2' -> (0, 3, 2)。読めない版は (0,) 扱い。"""
    parts = re.findall(r"\d+", v or "")
    return tuple(int(p) for p in parts) if parts else (0,)


def annotate_status(root, entries):
    """git status の各項目を表示用の行にし、エージェントが編集したファイルには印を付ける。

    entries は common.git_status() の結果 [(XY, パス), ...]。
    record_edit.py（PostToolUse）が残した記録と、今の更新時刻を比べる。
    未コミットでなくなったファイルの記録は消す。
    """
    with state_lock(root):
        st = load_state(root)
        edits = st.get("agent_edits", {})
        seen = set()
        out = []
        for xy, rel in entries:
            line = f"{xy} {rel}"
            if rel.endswith("/"):  # 未追跡のディレクトリ
                inside = [k for k in edits if k.startswith(rel)]
                seen.update(inside)
                if inside:
                    line += f"  [contains {len(inside)} file(s) edited by the agent]"
            elif rel in edits:
                seen.add(rel)
                e = edits[rel]
                full = os.path.join(root, rel)
                cur = os.path.getmtime(full) if os.path.exists(full) else None
                if cur is not None and abs(cur - e.get("mtime", 0)) < 1.0:
                    line += f"  [agent {e.get('at', '')}]"
                else:
                    line += f"  [agent {e.get('at', '')}, changed since]"
            out.append(line)
        pruned = {k: v for k, v in edits.items() if k in seen}
        if pruned != edits:
            st["agent_edits"] = pruned
            save_state(root, st)
    return out


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
            changed = newest_change(root, watch)[0]
            with state_lock(root):
                st = load_state(root)
                st["last_notified_change"] = max(st.get("last_notified_change", 0.0), changed)
                save_state(root, st)

    out.append("# research-memory: research project memory (loaded automatically)")
    today_rel = today_log_rel(cfg)
    out.append(
        f"Today's log file (今日のログファイル): {today_rel} (time zone {cfg['timezone']}). "
        "Follow the research-log Skill when recording. Write all records in Japanese."
    )

    # 0. テンプレートの版: プラグインより古ければ更新を知らせる
    plugin_ver = plugin_version()
    repo_ver = str(cfg.get("template_version") or "")
    if plugin_ver and version_tuple(repo_ver) < version_tuple(plugin_ver):
        shown = repo_ver or "not recorded"
        out.append(
            f"\nNote: this repository's research-memory files follow template version {shown}, "
            f"but the plugin is {plugin_ver}. Tell the user once, in Japanese, that they can run "
            "/research-memory:research-init to review the template changes (nothing is changed without approval)."
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
    # 部分一致で誤って「記録済み」としないよう、タグ名の直後が名前の続きでないことを確かめる
    missing = [t for t in tags if not re.search(re.escape(t) + r"(?![\w./-])", memory)]
    if missing:
        out.append("\n## Unrecorded archive tags")
        out.append(
            "These tags are not listed under 「検討したが却下した選択肢」 in MEMORY.md. "
            "Mention this briefly to the user in your first reply and offer to record the tag name and why it was rejected: "
            + ", ".join(missing)
        )

    # 4. 作業ツリーの変更（ユーザーによるコード変更の検出用）
    status = git_status(root)
    if status:
        lines = annotate_status(root, status)
        out.append("\n## Uncommitted changes (git status)")
        out.extend(lines[:30])
        if len(lines) > 30:
            out.append(f"... and {len(lines) - 30} more")
        out.append(
            "[agent ...] = edited by the agent's file tools at that time and unchanged since. "
            "[agent ..., changed since] = the agent edited it, then something else changed it. "
            "Lines without a mark were not edited by the agent's file tools: they may be the user's changes, "
            "or the agent's shell commands (check 「変更したファイル・コード」 in recent logs). "
            "For changes that are not the agent's, do not guess the intent: ask the user, and record the answer in the log."
        )
    elif status is not None:
        annotate_status(root, [])  # 作業ツリーがきれいなら、編集の記録を消す
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
