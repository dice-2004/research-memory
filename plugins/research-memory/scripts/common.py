"""research-memory プラグインの hook スクリプトで共有する処理。

Python 標準ライブラリのみを使う（研究サーバーに追加インストール不要）。
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

DEFAULT_CONFIG = {
    # Stop hook が「研究に影響する変更」とみなすディレクトリ
    "watch": ["src", "configs", "scripts", "outputs"],
    # ログの日付を決めるタイムゾーン（サーバーがUTCでも日本時間で切る）
    "timezone": "Asia/Tokyo",
    # SessionStart で読み込ませる MEMORY.md の最大文字数
    "memory_max_chars": 6000,
    # 圧縮直前に保存した会話の控えを残す日数（書き損じ防止の一時的な保険）
    "transcript_retention_days": 14,
}


def read_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def run_git(args, cwd):
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except Exception:
        return None


def find_root(data):
    """研究プロジェクトのルートを返す。研究プロジェクトでなければ None。

    MEMORY.md と logs/ の両方があるディレクトリだけを研究プロジェクトとみなす。
    これにより、プラグインが有効でも無関係なリポジトリでは何もしない。
    """
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    top = run_git(["rev-parse", "--show-toplevel"], cwd)
    root = top.strip() if top else cwd
    if os.path.isfile(os.path.join(root, "MEMORY.md")) and os.path.isdir(
        os.path.join(root, "logs")
    ):
        return root
    return None


def load_config(root):
    cfg = dict(DEFAULT_CONFIG)
    path = os.path.join(root, ".research-memory.json")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def now(cfg):
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(cfg.get("timezone", "Asia/Tokyo")))
    except Exception:
        return datetime.now()


def today_log_rel(cfg):
    return f"logs/{now(cfg).strftime('%Y-%m-%d')}.md"


def state_dir(root):
    """worktree ごとの状態置き場（.git 内なのでコミットされない）。"""
    gd = run_git(["rev-parse", "--git-dir"], root)
    if gd:
        gd = gd.strip()
        if not os.path.isabs(gd):
            gd = os.path.join(root, gd)
        d = os.path.join(gd, "research-memory")
    else:
        d = os.path.join(root, ".research-memory-state")
    os.makedirs(d, exist_ok=True)
    return d


def load_state(root):
    path = os.path.join(state_dir(root), "state.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(root, state):
    path = os.path.join(state_dir(root), "state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def newest_change(root, watch):
    """監視対象の最新の変更時刻と、その対象パスを返す。"""
    best, best_path = 0.0, None

    # 1. 未コミットの変更（追跡対象ファイル + 未追跡ファイル）
    status = run_git(["status", "--porcelain", "--", *watch], root) or ""
    for line in status.splitlines():
        rel = line[3:].split(" -> ")[-1].strip().strip('"')
        t = mtime(os.path.join(root, rel))
        if t > best:
            best, best_path = t, rel

    # 2. 監視対象に触れた最新のコミット（エージェントがコミット済みの場合）
    ct = run_git(["log", "-1", "--format=%ct", "--", *watch], root)
    if ct and ct.strip():
        t = float(ct.strip())
        if t > best:
            best, best_path = t, "（コミット済みの変更）"

    # 3. outputs/ など gitignore されたディレクトリは直下のエントリの更新時刻を見る
    for w in watch:
        d = os.path.join(root, w)
        if not os.path.isdir(d):
            continue
        try:
            for name in os.listdir(d):
                t = mtime(os.path.join(d, name))
                if t > best:
                    best, best_path = t, f"{w}/{name}"
        except OSError:
            pass
    return best, best_path


def cleanup_transcripts(root, cfg):
    """保存期間を過ぎた会話の控えを削除する。"""
    d = os.path.join(state_dir(root), "transcripts")
    if not os.path.isdir(d):
        return
    cutoff = time.time() - float(cfg.get("transcript_retention_days", 14)) * 86400
    for name in os.listdir(d):
        p = os.path.join(d, name)
        try:
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass
