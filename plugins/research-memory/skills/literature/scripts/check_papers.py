#!/usr/bin/env python3
"""docs/papers/ の論文ノートと、BibTeX・リンクの整合を確認する。

使い方: python3 check_papers.py <リポジトリのルート>

確認すること:
  エラー（直す）
    - frontmatter の必須項目がない・値が埋まっていない・値が決められた選択肢にない
    - 出典（doi・arxiv・url のどれか）がない
    - citekey とファイル名が一致しない、DOI や arXiv ID が他のノートと重複している
    - 必須の見出しがない
    - アブスト・Webページしか読んでいないノートに、強さ supported / strong の主張がある
    - docs/ 内の Markdown の相対リンクの行き先がない
  警告（内容を見て判断する）
    - references.bib に citekey がない、または % UNVERIFIED のエントリがある
    - 目次 docs/papers/README.md が最新ではない（build_index.py で再生成する）
    - 「読んだ記録」に取得元の URL がない
    - docs/literature/ の「根拠」にリンクがない、またはアブスト・Webページのみのノートを根拠にしている

claude-scholar（Galaxy-Dawn, MIT License）の verify_paper_notes.py の考え方を参考に、
このリポジトリの書式に合わせて書き直したもの。Python 標準ライブラリのみ使用。
"""
import os
import re
from urllib.parse import unquote
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_index  # noqa: E402

REQUIRED_FIELDS = ("type", "citekey", "title", "year", "status", "source_type", "checked")
STATUS = {"to-read", "skimmed", "read"}
SOURCE_TYPES = {"full-paper", "preprint", "abstract-only", "webpage"}
WEAK_SOURCES = {"abstract-only", "webpage"}
REQUIRED_HEADINGS = ("## 要約", "## 主張", "## 評価条件", "## 報告されている結果", "## 自分の研究との関係", "## 読んだ記録")
# [文字](先) と [文字](<空白を含む 先>) の両方を拾う
LINK_RE = re.compile(r"\]\((?:<([^>]+)>|([^)\s]+))(?:\s+\"[^\"]*\")?\)")
STRENGTH_RE = re.compile(r"強さ\s*[:：]\s*(speculative|observed|supported|strong)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm, text[end + 4:]


def strip_code(text):
    """コードブロックとインラインコードの中のリンクは確認しない。"""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def md_files(docs):
    for base, _, files in os.walk(docs):
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f)


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    docs = os.path.join(root, "docs")
    papers_dir = os.path.join(docs, "papers")
    errors, warnings = [], []
    rel = lambda p: os.path.relpath(p, root)

    if not os.path.isdir(papers_dir):
        print("docs/papers/ がありません。/research-memory:research-init を再実行してください。")
        return 1

    notes = {}
    seen_ids = {}
    for name in sorted(os.listdir(papers_dir)):
        if not name.endswith(".md") or name.startswith("_") or name == build_index.INDEX_NAME:
            continue
        path = os.path.join(papers_dir, name)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        fm, body = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{rel(path)}: frontmatter（--- で囲んだ書誌情報）がありません")
            continue
        stem = name[:-3]
        for k in REQUIRED_FIELDS:
            v = fm.get(k, "")
            if not v or v.startswith("<"):
                errors.append(f"{rel(path)}: {k} が埋まっていません")
        if fm.get("citekey") and not fm["citekey"].startswith("<") and fm["citekey"] != stem:
            errors.append(f"{rel(path)}: citekey ({fm['citekey']}) とファイル名 ({stem}) が一致しません")
        if fm.get("status") and not fm["status"].startswith("<") and fm["status"] not in STATUS:
            errors.append(f"{rel(path)}: status は {sorted(STATUS)} のどれかにしてください（現在: {fm['status']}）")
        st = fm.get("source_type", "")
        if st and not st.startswith("<") and st not in SOURCE_TYPES:
            errors.append(f"{rel(path)}: source_type は {sorted(SOURCE_TYPES)} のどれかにしてください（現在: {st}）")
        if fm.get("checked") and not fm["checked"].startswith("<") and not DATE_RE.match(fm["checked"]):
            errors.append(f"{rel(path)}: checked は YYYY-MM-DD 形式にしてください")
        for idk in ("doi", "arxiv"):
            v = fm.get(idk, "").lower()
            if v and not v.startswith("<"):
                if (idk, v) in seen_ids:
                    errors.append(f"{rel(path)}: {idk} {v} が {seen_ids[(idk, v)]} と重複しています（1論文1ノートにまとめる）")
                else:
                    seen_ids[(idk, v)] = rel(path)
        if not any(fm.get(k) and not fm[k].startswith("<") for k in ("doi", "arxiv", "url")):
            errors.append(f"{rel(path)}: 出典（doi・arxiv・url のどれか）がありません")
        m = re.search(r"^## 読んだ記録\s*$(.*?)(?=^## |\Z)", body, flags=re.M | re.S)
        if m and not re.search(r"https?://", m.group(1)):
            warnings.append(f"{rel(path)}: 「読んだ記録」に取得元（実際に読んだ PDF やページ）の URL がありません")
        for h in REQUIRED_HEADINGS:
            if not re.search("^" + re.escape(h) + r"\s*$", body, flags=re.M):
                errors.append(f"{rel(path)}: 見出し「{h}」がありません")
        if st in WEAK_SOURCES:
            strong = [s for s in STRENGTH_RE.findall(body) if s in ("supported", "strong")]
            if strong:
                errors.append(
                    f"{rel(path)}: source_type が {st} なのに強さ {', '.join(sorted(set(strong)))} の主張があります"
                    "（全文を読むまで observed 以下にする）"
                )
        notes[stem] = {"path": path, "source_type": st}

    # BibTeX
    bib = os.path.join(docs, "references.bib")
    if os.path.isfile(bib):
        with open(bib, encoding="utf-8") as f:
            bibtext = f.read()
        keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bibtext))
        for stem in notes:
            if stem not in keys:
                warnings.append(f"docs/references.bib に {stem} がありません（fetch_bibtex.py で取得する）")
        n_unverified = len(re.findall(r"^\s*%\s*UNVERIFIED\b", bibtext, flags=re.M))
        if n_unverified:
            warnings.append(f"docs/references.bib に未確認（% UNVERIFIED）のエントリが {n_unverified} 件あります")
    elif notes:
        warnings.append("docs/references.bib がありません")

    # リンク
    for path in md_files(docs):
        with open(path, encoding="utf-8") as f:
            text = strip_code(f.read())
        base = os.path.dirname(path)
        in_literature = os.path.dirname(path) == os.path.join(docs, "literature")
        for m in LINK_RE.finditer(text):
            target = m.group(1) or m.group(2)
            if re.match(r"^(https?:|mailto:|#|<)", target):
                continue
            if os.path.basename(target.split("#")[0]) == "citekey.md":
                continue  # テンプレートの記入例
            target_path = os.path.normpath(os.path.join(base, unquote(target.split("#")[0])))
            if not os.path.exists(target_path):
                errors.append(f"{rel(path)}: リンク先 {target} がありません")
                continue
            if in_literature and os.path.dirname(target_path) == papers_dir:
                stem = os.path.basename(target_path)[:-3]
                if notes.get(stem, {}).get("source_type") in WEAK_SOURCES:
                    warnings.append(
                        f"{rel(path)}: {stem} はアブスト・Webページしか読んでいないノートです。"
                        "総括の根拠にしていないか確認してください"
                    )

    # 総括の「根拠」にリンクがあるか
    lit_dir = os.path.join(docs, "literature")
    if os.path.isdir(lit_dir):
        for name in sorted(os.listdir(lit_dir)):
            if not name.endswith(".md"):
                continue
            path = os.path.join(lit_dir, name)
            with open(path, encoding="utf-8") as f:
                lines = strip_code(f.read()).splitlines()
            for i, line in enumerate(lines, 1):
                if line.lstrip().startswith(">"):
                    continue
                m = re.search(r"根拠\s*[:：]\s*(.*)", line)
                if m and m.group(1).strip() and not m.group(1).strip().startswith("<") and "](" not in m.group(1):
                    warnings.append(f"{rel(path)}:{i}: 「根拠」に出典のリンクがありません")

    # 目次
    expected = build_index.render(build_index.load_notes(papers_dir))
    index_path = os.path.join(papers_dir, build_index.INDEX_NAME)
    current = open(index_path, encoding="utf-8").read() if os.path.isfile(index_path) else None
    if current != expected:
        warnings.append("docs/papers/README.md（目次）が最新ではありません（build_index.py を実行する）")

    print(f"論文ノート: {len(notes)} 件")
    for e in errors:
        print("エラー: " + e)
    for w in warnings:
        print("警告: " + w)
    if not errors and not warnings:
        print("問題は見つかりませんでした。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
