#!/usr/bin/env python3
"""DOI または arXiv ID から BibTeX を取得する（記憶から BibTeX を書かないため）。

使い方:
  python3 fetch_bibtex.py --doi 10.1109/CVPR52688.2022.01392 --key roth2022towards
  python3 fetch_bibtex.py --arxiv 2106.08265 --key roth2022towards --append docs/references.bib

- DOI: https://doi.org/ に BibTeX を要求する（出版社の登録情報）
- arXiv: https://arxiv.org/bibtex/<id> から取得する
- --key で citekey をノートのファイル名に合わせて置き換える
- --append を付けると、同じ citekey がなければファイル末尾に追記する

Python 標準ライブラリのみ使用。HTTPS_PROXY などの環境変数のプロキシ設定に従う。
"""
import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "research-memory/0.2 (BibTeX lookup; mailto not set)"
ARXIV_ID = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")


def http_get(url, accept):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_doi(doi):
    doi = doi.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/:;()._-")
    return http_get(url, "application/x-bibtex; charset=utf-8")


def fetch_arxiv(arxiv_id):
    arxiv_id = arxiv_id.strip()
    arxiv_id = re.sub(r"^(https?://arxiv\.org/(abs|pdf)/|arxiv:)", "", arxiv_id, flags=re.I)
    arxiv_id = re.sub(r"\.pdf$", "", arxiv_id)
    if not ARXIV_ID.match(arxiv_id):
        raise ValueError(f"arXiv ID の形式ではありません: {arxiv_id}")
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)  # 版番号を付けず、最新版を指す
    try:
        text = http_get("https://arxiv.org/bibtex/" + arxiv_id, "text/plain")
        if text.lstrip().startswith("@"):
            return text
    except urllib.error.HTTPError:
        pass
    # 予備: arXiv が登録している DOI（DataCite）から取得する
    return fetch_doi("10.48550/arXiv." + arxiv_id)


def normalize(bib, key):
    bib = bib.strip()
    m = re.match(r"\s*@(\w+)\s*\{\s*([^,\s]*)\s*,", bib)
    if not m:
        raise ValueError("BibTeX として解釈できない応答でした:\n" + bib[:300])
    if key:
        bib = bib[: m.start(2)] + key + bib[m.end(2):]
    return bib, (key or m.group(2))


def has_key(path, key):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return False
    return re.search(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", text) is not None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--doi")
    src.add_argument("--arxiv")
    ap.add_argument("--key", help="citekey（ノートのファイル名と同じにする）")
    ap.add_argument("--append", metavar="BIBFILE", help="この .bib ファイルに追記する")
    args = ap.parse_args()

    try:
        raw = fetch_doi(args.doi) if args.doi else fetch_arxiv(args.arxiv)
        bib, key = normalize(raw, args.key)
    except urllib.error.HTTPError as e:
        print(f"取得に失敗しました（HTTP {e.code}）。識別子を確認してください。", file=sys.stderr)
        return 2
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"接続できませんでした: {e}。ネットワークまたはプロキシ設定を確認してください。", file=sys.stderr)
        return 3
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 4

    if args.append:
        if has_key(args.append, key):
            print(f"{args.append} には既に {key} があります。追記しませんでした。", file=sys.stderr)
            print(bib)
            return 0
        with open(args.append, "a", encoding="utf-8") as f:
            f.write("\n" + bib + "\n")
        print(f"{args.append} に {key} を追記しました。", file=sys.stderr)
    print(bib)
    return 0


if __name__ == "__main__":
    sys.exit(main())
