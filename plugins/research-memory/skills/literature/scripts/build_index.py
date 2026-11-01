#!/usr/bin/env python3
"""docs/papers/ の論文ノートから目次 docs/papers/README.md を生成する。

使い方:
  python3 build_index.py <リポジトリのルート>          # 目次を書き直す
  python3 build_index.py <リポジトリのルート> --check  # 目次が最新か確認だけする（古ければ終了コード1）

各ノートの frontmatter（title・authors・year・venue・status・source_type・tags・doi・arxiv・url）と
「## 要約」の最初の行から作る。GitLab ではフォルダを開くと README.md が表示されるので、
docs/papers/ を開くだけで目次が見える。手で編集しない（次の生成で上書きされる）。
Python 標準ライブラリのみ使用。
"""
import os
import re
import sys

INDEX_NAME = "README.md"
STATUS_ORDER = {"read": 0, "skimmed": 1, "to-read": 2}


def parse_frontmatter(text):
    """簡易 YAML: `key: value`、`key: [a, b]`、および `key:` の次行からの `- a` 形式のリストに対応。"""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm, last = {}, None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                fm[key] = []
            else:
                fm[key] = val.strip('"').strip("'")
            last = key
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and last and isinstance(fm.get(last), list):
            fm[last].append(m.group(1).strip().strip('"').strip("'"))
    return fm, text[end + 4:]


def filled(v):
    """テンプレートのまま（<...>）や空の値は未記入として扱う。"""
    if isinstance(v, list):
        return [x for x in v if x and not x.startswith("<")]
    return "" if (not v or str(v).startswith("<")) else str(v)


def first_summary_line(body):
    m = re.search(r"^## 要約\s*$(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = line.strip()
        if line and not line.startswith("<") and not line.startswith(">"):
            return line if len(line) <= 80 else line[:79] + "…"
    return ""


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def link(n):
    text = n["title"].replace("[", "\\[").replace("]", "\\]")
    return f"[{text}]({n['file']})"


def load_notes(papers_dir):
    notes = []
    for name in sorted(os.listdir(papers_dir)):
        if not name.endswith(".md") or name.startswith("_") or name == INDEX_NAME:
            continue
        with open(os.path.join(papers_dir, name), encoding="utf-8") as f:
            fm, body = parse_frontmatter(f.read())
        fm = fm or {}
        authors = filled(fm.get("authors", []))
        if isinstance(authors, str):
            authors = [authors]
        year = filled(fm.get("year", ""))
        notes.append(
            {
                "file": name,
                "citekey": name[:-3],
                "title": filled(fm.get("title", "")) or name[:-3],
                "authors": authors,
                "year": year,
                "venue": filled(fm.get("venue", "")),
                "status": filled(fm.get("status", "")),
                "source_type": filled(fm.get("source_type", "")),
                "tags": filled(fm.get("tags", [])) if isinstance(fm.get("tags", []), list) else [],
                "has_source": bool(filled(fm.get("doi", "")) or filled(fm.get("arxiv", "")) or filled(fm.get("url", ""))),
                "summary": first_summary_line(body),
            }
        )
    return notes


def author_label(authors):
    if not authors:
        return ""
    first = authors[0]
    return first if len(authors) == 1 else f"{first} ほか"


def render(notes):
    def year_key(n):
        return -int(n["year"]) if re.fullmatch(r"\d{4}", n["year"] or "") else 0

    notes = sorted(notes, key=lambda n: (year_key(n), n["citekey"]))
    counts = {s: sum(1 for n in notes if n["status"] == s) for s in ("read", "skimmed", "to-read")}
    out = [
        "# 論文ノートの目次",
        "",
        "> build_index.py による自動生成。手で編集しない（ノートを追加・更新したら再生成する）。",
        "> 比較表・読む予定・未確認の論文は [../related_work.md](../related_work.md) にある。",
        "",
        f"全 {len(notes)} 件（read {counts['read']} / skimmed {counts['skimmed']} / to-read {counts['to-read']}）",
        "",
        "## 一覧（新しい順）",
        "",
    ]
    if notes:
        out += [
            "| 論文 | 著者 | 年 | 会議 | 状態 | 読んだ範囲 | タグ | 要約 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for n in notes:
            tags = " ".join(f"`{t}`" for t in n["tags"])
            out.append(
                f"| {cell(link(n))} | {cell(author_label(n['authors']))} | {cell(n['year'])} "
                f"| {cell(n['venue'])} | {cell(n['status'])} | {cell(n['source_type'])} | {tags} | {cell(n['summary'])} |"
            )
    else:
        out.append("（まだノートはありません）")

    tagged = {}
    for n in notes:
        for t in n["tags"]:
            tagged.setdefault(t, []).append(n)
    if tagged:
        out += ["", "## タグ別", ""]
        for t in sorted(tagged):
            out.append(f"### {t}")
            out.append("")
            for n in sorted(tagged[t], key=lambda n: (year_key(n), n["citekey"])):
                out.append(f"- {link(n)}（{n['year'] or '年不明'}, {n['status'] or '状態未記入'}）")
            out.append("")
        if out[-1] == "":
            out.pop()

    weak = [n for n in notes if n["source_type"] in ("abstract-only", "webpage") or not n["has_source"]]
    if weak:
        out += ["", "## 根拠に使えないノート（アブスト・Webページのみ、または出典なし）", ""]
        for n in weak:
            reasons = [n["source_type"]] if n["source_type"] in ("abstract-only", "webpage") else []
            if not n["has_source"]:
                reasons.append("出典なし")
            out.append(f"- {link(n)}（{'、'.join(reasons)}）")

    return "\n".join(out) + "\n"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    root = os.path.abspath(args[0] if args else ".")
    papers_dir = os.path.join(root, "docs", "papers")
    if not os.path.isdir(papers_dir):
        print("docs/papers/ がありません。/research-memory:research-init を再実行してください。", file=sys.stderr)
        return 1
    text = render(load_notes(papers_dir))
    path = os.path.join(papers_dir, INDEX_NAME)
    current = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
    if check:
        if current != text:
            print("docs/papers/README.md（目次）が最新ではありません。build_index.py を実行してください。")
            return 1
        print("目次は最新です。")
        return 0
    if current != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("docs/papers/README.md（目次）を更新しました。")
    else:
        print("目次は最新です（変更なし）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
