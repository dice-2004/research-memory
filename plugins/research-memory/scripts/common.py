"""research-memory プラグインの hook スクリプトで共有する処理。

Python 標準ライブラリのみを使う（研究サーバーに追加インストール不要）。
"""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

try:  # Unix のみ。Windows ではロックなしで動く
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

DEFAULT_CONFIG = {
    # Stop hook が「研究に影響する変更」とみなすパス（ファイルも可）。
    # 実験の出力先（outputs/ など）は実行中に変わり続けるので入れない
    "watch": ["src", "configs", "scripts"],
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


# zoneinfo のデータ（tzdata）がない環境でも日付がずれないための固定オフセット
FIXED_OFFSETS = {"Asia/Tokyo": 9, "UTC": 0, "Etc/UTC": 0}


def now(cfg):
    name = cfg.get("timezone", "Asia/Tokyo")
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(name))
    except Exception:
        if name in FIXED_OFFSETS:
            return datetime.now(timezone(timedelta(hours=FIXED_OFFSETS[name])))
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


@contextlib.contextmanager
def state_lock(root):
    """state.json の読み書きを排他にする（hook が同時に動いても書き込みが消えないように）。

    使い方: with state_lock(root): st = load_state(root); ...; save_state(root, st)
    """
    d = state_dir(root)
    if fcntl is None:
        yield
        return
    with open(os.path.join(d, "state.lock"), "a") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def load_state(root):
    path = os.path.join(state_dir(root), "state.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(root, state):
    """一時ファイルに書いてから置き換える（読み手が書きかけのファイルを見ないように）。"""
    d = state_dir(root)
    fd, tmp = tempfile.mkstemp(dir=d, prefix="state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, os.path.join(d, "state.json"))
    except Exception:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def git_status(root, pathspecs=None):
    """未コミットの変更を [(XY, パス), ...] で返す。失敗したら None。

    日本語や空白を含むパスもそのまま扱えるよう、-z と core.quotePath=false を使う。
    名前の変更（R/C）は変更後のパスを返す。
    """
    args = ["-c", "core.quotePath=false", "status", "--porcelain", "-z"]
    if pathspecs:
        args += ["--", *pathspecs]
    out = run_git(args, root)
    if out is None:
        return None
    entries = out.split("\0")
    result, i = [], 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        xy, path = e[:2], e[3:]
        if "R" in xy or "C" in xy:
            i += 1  # 次の要素は変更前のパス
        result.append((xy, path))
    return result


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def newest_change(root, watch):
    """監視対象の最新の変更時刻と、その対象パスを返す。"""
    best, best_path = 0.0, None

    # 1. 未コミットの変更（追跡対象ファイル + 未追跡ファイル）
    for _, rel in git_status(root, watch) or []:
        t = mtime(os.path.join(root, rel.rstrip("/")))
        if t > best:
            best, best_path = t, rel

    # 2. 監視対象に触れた最新のコミット（エージェントがコミット済みの場合）
    ct = run_git(["log", "-1", "--format=%ct", "--", *watch], root)
    if ct and ct.strip():
        t = float(ct.strip())
        if t > best:
            best, best_path = t, "（コミット済みの変更）"

    # 3. gitignore されたファイルの変更も拾うため、監視対象の直下のエントリの更新時刻を見る
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
