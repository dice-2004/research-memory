"""research-memory プラグインの動作確認（開発用）。

使い方: python3 tests/smoke_test.py
テンプレートから一時的な研究リポジトリを作り、各 hook と文献スクリプトを実際に動かして結果を確かめる。
標準ライブラリだけで動く。ネットワークは使わない（fetch_bibtex.py の通信は試さない）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "research-memory")
SCRIPTS = os.path.join(PLUGIN, "scripts")
LIT = os.path.join(PLUGIN, "skills", "literature", "scripts")
TEMPLATES = os.path.join(PLUGIN, "skills", "research-init", "templates")

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok or not detail else f"\n     {detail}"))


def hook(script, payload, cwd=None):
    p = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, script)],
        input=json.dumps(payload), capture_output=True, text=True, cwd=cwd, timeout=30,
    )
    return p.returncode, p.stdout, p.stderr


def git(repo, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                   check=True, capture_output=True)


def make_repo(base):
    repo = os.path.join(base, "repo")
    shutil.copytree(TEMPLATES, repo)
    os.rename(os.path.join(repo, "research-memory.json"), os.path.join(repo, ".research-memory.json"))
    os.makedirs(os.path.join(repo, "src"))
    with open(os.path.join(repo, "src", "a.py"), "w") as f:
        f.write("a\n")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def main():
    # 0. 版の整合
    with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json")) as f:
        pver = json.load(f)["version"]
    with open(os.path.join(TEMPLATES, "research-memory.json")) as f:
        tver = json.load(f).get("template_version")
    check("plugin.json の version と template_version が同じ", pver == tver, f"{pver} != {tver}")

    base = tempfile.mkdtemp(prefix="rm-smoke-")
    try:
        repo = make_repo(base)

        # 1. SessionStart
        rc, out, err = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("SessionStart: MEMORY.md を渡す", rc == 0 and "MEMORY.md (current state" in out, err)
        check("SessionStart: 版が同じなら更新の通知を出さない", "template version" not in out)
        cfg_path = os.path.join(repo, ".research-memory.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg.pop("template_version", None)
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("SessionStart: 版が記録されていなければ通知する", "template version not recorded" in out)

        # 2. PostToolUse（エージェントの編集の記録）と git status の印
        with open(os.path.join(repo, "src", "a.py"), "a") as f:
            f.write("agent\n")
        hook("record_edit.py", {"cwd": repo, "tool_name": "Edit",
                                "tool_input": {"file_path": os.path.join(repo, "src", "a.py")}})
        hook("record_edit.py", {"cwd": repo, "tool_name": "Write", "tool_input": {"file_path": "/etc/hosts"}})
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("PostToolUse: 編集したファイルに [agent …] の印が付く", " M src/a.py  [agent " in out, out[-600:])
        time.sleep(1.1)
        with open(os.path.join(repo, "src", "a.py"), "a") as f:
            f.write("user\n")
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("PostToolUse: その後に変わったら changed since になる", "changed since]" in out)
        git(repo, "commit", "-qam", "c")
        hook("session_start.py", {"cwd": repo, "source": "startup"})
        with open(os.path.join(repo, ".git", "research-memory", "state.json")) as f:
            st = json.load(f)
        check("PostToolUse: 作業ツリーがきれいになったら記録を消す", st.get("agent_edits") == {}, str(st.get("agent_edits")))

        # 3. Stop（記録漏れ）
        time.sleep(1.1)
        with open(os.path.join(repo, "src", "a.py"), "a") as f:
            f.write("change\n")
        _, out, _ = hook("stop_check.py", {"cwd": repo})
        check("Stop: 研究に関わる変更があり、ログが古ければ止める", '"decision": "block"' in out, out)
        _, out, _ = hook("stop_check.py", {"cwd": repo})
        check("Stop: 同じ変更では2回止めない", out.strip() == "", out)
        _, out, _ = hook("stop_check.py", {"cwd": repo, "stop_hook_active": True})
        check("Stop: stop_hook_active なら通す", out.strip() == "")

        # 4. PreToolUse（MEMORY.md の承認制）
        _, out, _ = hook("guard_memory.py", {"cwd": repo, "tool_name": "Edit",
                                             "tool_input": {"file_path": os.path.join(repo, "MEMORY.md")}})
        check("PreToolUse: MEMORY.md の編集は承認を求める", '"permissionDecision": "ask"' in out, out)
        _, out, _ = hook("guard_memory.py", {"cwd": repo, "tool_name": "Edit",
                                             "tool_input": {"file_path": os.path.join(repo, "src", "a.py")}})
        check("PreToolUse: ほかのファイルは素通り", out.strip() == "", out)
        _, out, _ = hook("guard_memory.py", {"cwd": repo, "tool_name": "Bash",
                                             "tool_input": {"command": "echo x >> MEMORY.md"}})
        check("PreToolUse: Bash での MEMORY.md への書き込みも承認を求める", '"ask"' in out, out)

        # 5. PreCompact（会話の控え）
        tr = os.path.join(base, "transcript.jsonl")
        with open(tr, "w") as f:
            f.write('{"x":1}\n')
        rc, _, err = hook("pre_compact.py", {"cwd": repo, "transcript_path": tr, "trigger": "auto"})
        tdir = os.path.join(repo, ".git", "research-memory", "transcripts")
        saved = os.listdir(tdir) if os.path.isdir(tdir) else []
        check("PreCompact: 会話の控えを .git/research-memory/transcripts/ に保存", rc == 0 and len(saved) == 1, err)
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "compact"})
        check("SessionStart（圧縮後）: 控えの場所を伝える", "The context was compacted" in out)

        # 6. 文献スクリプト
        p = subprocess.run([sys.executable, os.path.join(LIT, "check_papers.py"), repo],
                           capture_output=True, text=True)
        check("check_papers.py: テンプレートのままでエラーなし", p.returncode == 0, p.stdout + p.stderr)
        p = subprocess.run([sys.executable, os.path.join(LIT, "build_index.py"), repo, "--check"],
                           capture_output=True, text=True)
        check("build_index.py --check: 実行できる", p.returncode in (0, 1), p.stdout + p.stderr)

        # 6b. 同時に動く hook・日本語のパス・名前の変更・archive タグ・日本語のリンク
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "c3")
        names = [f"src/p{i}.py" for i in range(20)]
        for n in names:
            with open(os.path.join(repo, n), "w") as f:
                f.write("x\n")
        procs = [subprocess.Popen([sys.executable, os.path.join(SCRIPTS, "record_edit.py")],
                                  stdin=subprocess.PIPE, text=True) for _ in names]
        for pr, n in zip(procs, names):
            pr.communicate(json.dumps({"cwd": repo, "tool_name": "Write",
                                       "tool_input": {"file_path": os.path.join(repo, n)}}))
        with open(os.path.join(repo, ".git", "research-memory", "state.json")) as f:
            kept = json.load(f).get("agent_edits", {})
        check("PostToolUse: 20件を同時に記録しても消えない", all(n in kept for n in names), f"{len(kept)}/20")
        for n in names:
            os.remove(os.path.join(repo, n))

        jp = os.path.join(repo, "src", "日本語 名.py")
        with open(jp, "w") as f:
            f.write("x\n")
        hook("record_edit.py", {"cwd": repo, "tool_name": "Write", "tool_input": {"file_path": jp}})
        git(repo, "mv", "src/a.py", "src/b.py")
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("SessionStart: 日本語・空白を含むファイル名にも印が付く", "?? src/日本語 名.py  [agent " in out, out[-700:])
        check("SessionStart: 名前の変更は変更後のパスで表示する", "R  src/b.py" in out, out[-700:])
        git(repo, "mv", "src/b.py", "src/a.py")
        os.remove(jp)

        git(repo, "tag", "archive/exp/001_x")
        with open(os.path.join(repo, "MEMORY.md"), "a") as f:
            f.write("\n| 案 | 理由 | 自分 | `archive/exp/001_x-v2` |\n")
        _, out, _ = hook("session_start.py", {"cwd": repo, "source": "startup"})
        check("SessionStart: 名前の一部だけ一致する archive タグは未記録として知らせる",
              "Unrecorded archive tags" in out and "archive/exp/001_x" in out)
        git(repo, "checkout", "-q", "MEMORY.md")
        git(repo, "tag", "-d", "archive/exp/001_x")

        note = os.path.join(repo, "docs", "literature", "overview.md")
        with open(os.path.join(repo, "docs", "papers", "日本語.md"), "w") as f:
            f.write("x\n")
        with open(note, "a") as f:
            f.write("\n[参考](../papers/%E6%97%A5%E6%9C%AC%E8%AA%9E.md)\n")
        p = subprocess.run([sys.executable, os.path.join(LIT, "check_papers.py"), repo],
                           capture_output=True, text=True)
        check("check_papers.py: URL エンコードされた日本語のリンクを切れていると判定しない",
              "リンク先 ../papers/%E6" not in p.stdout, p.stdout[-500:])
        git(repo, "checkout", "-q", "docs/literature/overview.md")
        os.remove(os.path.join(repo, "docs", "papers", "日本語.md"))

        # 7. 研究リポジトリでない場所では何もしない
        other = os.path.join(base, "other")
        os.makedirs(other)
        outs = [hook(s, {"cwd": other, "source": "startup", "tool_name": "Edit",
                         "tool_input": {"file_path": os.path.join(other, "MEMORY.md")}})[1].strip()
                for s in ("session_start.py", "stop_check.py", "guard_memory.py", "record_edit.py")]
        check("研究リポジトリでない場所では、どの hook も何も出さない", outs == ["", "", "", ""], str(outs))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
