# research-memory 使い方ガイド

インストール手順は `README.md` にあります。このファイルは、入れたあとの「どこに何があるか」と「どう使うか」だけをまとめたものです。

## 1. どこに何があるか

### プラグイン側（サーバーの `~/` 以下。リポジトリには入らない）

| もの | 中身 |
|---|---|
| `~/research-memory-marketplace/`（登録に使ったフォルダ） | Skills（`research-log` / `meeting-note` / `lit-check` / `literature` / `experiment` / `research-init`）と hooks のスクリプト（`scripts/*.py`） |

- Claude Code が、登録したプラグインからこれらを読み込みます。研究リポジトリの中には Skills も scripts も置かれません。
- 登録に使ったフォルダは削除・移動しないでください。
- Skills や hooks を直したときは、`/reload-plugins` か新しいセッションで反映されます。

### 研究リポジトリ側（`/research-memory:research-init` を1回実行したあと）

```
your-research-repo/
├── AGENTS.md              # 必ず守るルールと「いつ何を使うか」の表（短く保つ）
├── CLAUDE.md              # AGENTS.md を読み込むだけ
├── CONTRIBUTING.md        # ブランチの名前の付け方とタグの付け方（ブランチは削除しない。worktree の使い捨てのブランチは例外）
├── MEMORY.md              # 現在の研究状態の要約。書き換えは毎回あなたの承認制
├── docs/
│   ├── research_context.md   # 研究の背景・課題・用語（ドメイン知識）
│   ├── how_to_run.md         # 実験の実行手順（正本）
│   ├── experiments.md        # 実験・ブランチの一覧（実験ID＝ブランチ番号）
│   ├── results.md            # 結果の索引（数値を引用するときはここから原本をたどる）
│   ├── decisions.md          # MEMORY.md から外した過去の設計判断
│   ├── related_work.md       # 関連研究の入口（比較表・論文一覧・読む予定・未確認）
│   ├── datasets.md           # データセットの情報
│   ├── papers/               # 1論文1ノート（<citekey>.md）と目次 README.md（自動生成。GitLab でフォルダを開くと表示）
│   ├── literature/           # 検索の記録・分野の概観・手法の分類・研究ギャップ
│   └── references.bib        # BibTeX（DOI・arXiv から取得したもの）
├── logs/
│   ├── _template.md          # ログの書式見本
│   └── YYYY-MM-DD.md         # 1日1ファイル。冒頭に目次、イベントごとにブロックを追記
├── .research-memory.json  # 監視するパス・タイムゾーン・テンプレートの版などの設定
└── .gitattributes         # logs/*.md の merge=union（ブランチ間でログが衝突しにくくする）
```

これらはすべて GitLab で管理するファイルです。

### リポジトリ内だが GitLab に上がらないもの

- `.claude/settings.local.json`: `--scope local` でインストールしたときに作られる
- `.git/research-memory/`: hooks の状態（`state.json`。エージェントが編集したファイルの記録を含む）と、圧縮直前の会話の控え（`transcripts/`、14日で自動削除）

## 2. 1日の流れ（会話のしかた）

### 開始時（自動）

セッションを始める・再開する・圧縮されるたびに、次の内容が自動で Claude に渡されます。何もお願いする必要はありません。

- `MEMORY.md`（現在の状態）
- 今日（なければ直近）のログの目次
- `MEMORY.md` に載っていない `archive/*` タグ
- 未コミットの変更と直近のコミット

### 作業中（ふつうに話しかける）

| やりたいこと | 言い方の例 | 使われるもの |
|---|---|---|
| 続きから再開 | 「前回の続きをやりたい」 | 自動で読み込まれた MEMORY.md とログ |
| 実験を計画・実行 | 「この条件で比較実験を設計して」 | `experiment` Skill（実験ID、再現性・公平性・リークの確認） |
| 数値や事実をさっと確認 | 「PatchCore の MVTec での AUROC を確認して」 | `lit-check` Skill（一次情報を確認し、論文を創作しない） |
| 関連研究を体系的に調べる | 「エッジ向け ViT 異常検知のベースライン候補を調べたい」 | `literature` Skill（範囲を決める → 検索を記録 → 1本ノートを作って書式確認 → 続きを数本ずつ） |
| 論文を読んでノートにする | 「この論文（arXiv ID）を読んでノートにして」 | `literature` Skill（`docs/papers/` にノート、BibTeX を取得） |
| 研究ギャップを整理する | 「今読んだ論文から研究ギャップを整理して」 | `literature` Skill（`docs/literature/gaps.md`。追うかどうかはあなたが判断） |
| ミーティング内容を記録 | `/research-memory:meeting-note` に続けてメモを貼る | `meeting-note` Skill（決定・指示・助言・保留に分類して記録） |
| 判断の経緯を残す | 「A案をやめてB案にする。理由は…」 | `research-log` Skill（ログに記録し、MEMORY.md の更新を提案） |
| 自分でコードを直した | そのまま話しかける | 変更を検出して、Claude が意図を尋ね、回答をログに記録 |

### 記録漏れの防止（自動）

- コードや結果が変わったのに今日のログが更新されていないと、Claude は終了前にログを書くよう促されます（同じ変更につき1回だけ）。
- 議論で決めたことや考察、ミーティング報告があったのにログに書かれていない場合も、AI 判定で促されます。
- `MEMORY.md` を書き換えようとすると、毎回あなたの承認を求めます。Claude が勝手に書き換えることはありません。

### 終了時

- ログや MEMORY.md の更新は、`notes:` で始まる別コミットにします（研究コードの変更とは分けます）。AI は依頼されるまでコミットしないので、区切りで「記録をコミットして」と頼んでください。
- 実験の結果が出たら `docs/results.md` に1行、ブランチを作ったら `docs/experiments.md` に1行が足されます。数値を探すときは、まず `docs/results.md` を見ます。
- MEMORY.md が長くなったら（目安5000文字）、古い判断を `docs/decisions.md` に移す提案が出ます。
- push は自分で行います。Claude は push しません。

## 3. ブランチで案を試すとき

- 案ごとにブランチを切り、MEMORY.md もブランチごとに変わってかまいません。
- 不採用のブランチは削除せず、`archive/<名前>` タグを付けて残します。MEMORY.md の「却下した選択肢」に書いていないタグは、次のセッション開始時に Claude が知らせます。
- 採用案をマージするときの MEMORY.md の書き換えは、あなたが直接指示します。
- 不採用ブランチのログが必要なときは、手動で main にコピーします。

## 文献管理（literature Skill）

- **1論文1ノート**: `docs/papers/<citekey>.md` に、主張・評価条件・報告値（表番号つき）・限界・自分の研究との関係を書きます。誰が（Claude／あなた）どこまで読んだかも残します。
- **根拠の強さ**: 主張ごとに speculative / observed / supported / strong を付けます。アブストしか読んでいない論文（`source_type: abstract-only`）は、読む候補を見つけるためだけに使い、総括の根拠にはしません。
- **検索の記録**: `docs/literature/searches.md` に検索ごとの記録（日付・検索式・件数）を残すので、「どこまで調べたか」を後から説明できます。研究ギャップは「誰もやっていない」ではなく「この範囲では見つからなかった」と書きます。
- **BibTeX**: 記憶からは書かず、DOI か arXiv から取得します。研究サーバーから `doi.org` と `arxiv.org` に接続できる必要があります。
- **目次**: `docs/papers/README.md` は、各ノートの書誌情報から自動生成される一覧です（新しい順・タグ別・根拠に使えないもの）。GitLab で `docs/papers/` を開くとそのまま表示されます。ノートを作るたびに Claude が再生成するので、手で編集する必要はありません。
- **出典**: ノートには DOI・arXiv・URL のどれか、実際に読んだ PDF の URL（arXiv は版番号つき）、数値や主張の論文内の場所（表・節）を必ず書きます。総括や比較表の記述は、根拠のノートへのリンクと場所を付けます。
- **確認**: 調査の区切りで `check_papers.py` を実行し、書式の崩れ、出典の抜け、BibTeX の抜け、切れたリンク、古い目次、弱い根拠への依存を検出します。
- **Zotero**: 任意です。Zotero の MCP サーバーを接続していれば、書誌情報と全文の取得元に使います。ライブラリの変更は事前に確認します。
- **Obsidian**: 今は使いません。ノートは通常の Markdown リンクと YAML の frontmatter で書いているので、将来、リポジトリのフォルダを vault として開けばそのまま読めます。
- **論文の文章は書きません**。関連研究の節の下書きなどは作りません。

プラグインを更新したら、研究リポジトリで `/research-memory:research-init` をもう一度実行してください（アップグレード）。足りないファイルが追加され、既存のファイルについてはテンプレートの変更点がファイルごとに示されるので、取り込むものを選びます。研究固有の内容は上書きされません。手順の全体は `README.md` の「新しい版に更新する」にあります。

## 4. 設定（`.research-memory.json`）

| キー | 既定値 | 意味 |
|---|---|---|
| `watch` | `["src","configs","scripts"]` | 変更があればログ記録を促すパス（ファイルも可）。実験の出力先は、実行中に変わり続けるので入れない |
| `timezone` | `Asia/Tokyo` | ログの日付を決めるタイムゾーン（サーバーが UTC でも日本時間で日付を切る） |
| `memory_max_chars` | `6000` | セッション開始時に読み込ませる MEMORY.md の最大文字数 |
| `transcript_retention_days` | `14` | 圧縮直前の会話の控えを残す日数 |
| `template_version` | （初期設定・アップグレード時に記録） | このリポジトリのファイルがどの版のテンプレートに合わせてあるか。プラグインより古いと、セッション開始時に知らされる |

## 5. うまく動かないとき

- `/plugins` で research-memory が有効になっているか確認する
- `/hooks` で hooks が登録されているか確認する
- hooks は、リポジトリのルートに `MEMORY.md` と `logs/` の両方があるときだけ動きます。`research-init` を実行済みか確認してください
- AI 判定（Stop の prompt hook）のトークン消費や待ち時間が気になる場合は、Claude に「research-memory のリポジトリで、Stop の prompt hook を外して版を上げて」と頼みます（サーバーの clone を手で直すと、次の `git pull` とぶつかります）。スクリプトによる記録漏れ検出は残ります。消費量は `/usage` で確認できます
- prompt hook は、実際の Claude Code セッションでの動作確認ができていません。1週間ほど使って、精度と負荷を確かめてください
