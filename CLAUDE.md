# research-memory プラグインの開発

> このリポジトリで作業する AI とユーザーのための開発メモ。**最初にこのファイル、次に `docs/dev/history.md`（経緯・決定・未解決）を読む。**
> 使い方（利用者向け）は `README.md`（導入・更新）と `README-use.md`（日々の使い方）。

## これは何か

研究リポジトリで Claude Code を使うときに、研究の記憶（今の状態・判断の経緯・ミーティングの決定）をセッションをまたいで失わず、研究として許される AI の使い方（論文は書かない・事実と推測を分ける・公平な比較・リーク防止・最新情報の確認）を守らせるための Claude Code プラグインと、そのマーケットプレイス。

- 利用者: ユーザー本人（学部4年、修士へ進学予定。研究は ViT-Core 系の異常検知）。研究室の GitLab で研究コードを管理している。
- 利用先: 研究サーバー Europa の `~/research-memory-marketplace`（このリポジトリの clone）→ 研究リポジトリ `~/research/vitcore-loco`（GitLab）で `--scope local` で有効化。
- 研究リポジトリの中身（研究内容・データ・結果）は、このリポジトリには置かない。

## 構成

```
.claude-plugin/marketplace.json            マーケットプレイス（名前 research-tools）
plugins/research-memory/
  .claude-plugin/plugin.json               プラグイン（version はここ）
  hooks/hooks.json                         SessionStart / Stop（スクリプト＋AI判定）/ PreCompact / PreToolUse / PostToolUse
  scripts/                                 hook のスクリプト（標準ライブラリのみ、Python 3.9+）
    common.py session_start.py stop_check.py pre_compact.py guard_memory.py record_edit.py
  skills/
    research-init/   初期設定とアップグレード（templates/ が研究リポジトリに配るファイル）
    research-log/    logs/YYYY-MM-DD.md への記録と MEMORY.md の更新
    meeting-note/    ミーティング・ゼミの記録
    experiment/      実験の計画・実行・報告
    lit-check/       最新情報の単発確認
    literature/      体系的な文献調査（scripts/: fetch_bibtex / build_index / check_papers、references/）
  THIRD_PARTY_NOTICES.md                   claude-scholar（MIT）の出典
tests/smoke_test.py                        動作確認（後述）
docs/dev/history.md                        開発の経緯・決定・却下・未解決・やりたいこと
```

## 開発のルール

### 進め方
- 会話は日本語。結論から、平易に説明する。ユーザーは Web 開発は得意、研究の専門分野は勉強中。
- 変更の前に「何をどこにどう変えるか」を先に示す。依頼の意図が曖昧なら先に質問する（多くても3つ）。選ばれなかった案を出し直さない。
- 見積もりを聞かれたら、実行せずに推測で答える（推測と明記）。
- このリポジトリでは、変更をコミットして `main` に push してよい（ユーザー了承済み）。研究リポジトリ側（vitcore-loco）は逆で、コミットもプッシュも依頼されるまでしない。
- ユーザーが研究リポジトリの差分やファイルを貼ってくれたら、**研究固有でない部分だけ**をテンプレートに取り込む（逆輸入）。研究の中身は取り込まない。

### 版とタグ
- 変更を出すたびに版を上げる。`plugins/research-memory/.claude-plugin/plugin.json` の `version` と、`plugins/research-memory/skills/research-init/templates/research-memory.json` の `template_version` を**同じ値**にする（`tests/smoke_test.py` が確かめる）。
- 版のタグ（`vX.Y.Z`、注釈付き）は、アップグレード時の差分の一覧に使う。**クラウドの作業環境からはタグを push できない**（プロキシに拒否される）ので、push 後にユーザーへ次を伝える:
  `cd ~/research-memory-marketplace && git pull && git tag -a vX.Y.Z <commit> -m "X.Y.Z" && git push origin vX.Y.Z`、その後 Claude Code で `/reload-plugins`、研究リポジトリで `/research-memory:research-init`。

### 言語
- **AI だけが読む文は英語**（Skill の本文と references、hook が Claude に渡す文、Stop の AI 判定プロンプト）。トークン節約のため。ただし記録に使う日本語の見出し・ラベルは英文の中でもそのまま書く。
- **人が読むものは日本語**（テンプレート、Skill の description、承認メッセージ、スクリプトの出力、README、このファイル）。
- 研究リポジトリの記録（logs/・MEMORY.md・docs/）は必ず日本語で書かせる。

### テンプレートを変えるとき
- 研究リポジトリへは `research-init` の**アップグレード**で取り込まれる。研究固有の内容を上書きしない形で書き、埋める所は `<...>` にする。
- vitcore-loco の実物（運用の正本に近い）と食い違わないかを考える。食い違ったらユーザーに確認する（例: ブランチ削除の扱いで README と CONTRIBUTING.md が矛盾していた → 「一切削除しない」に統一）。
- ルールは AGENTS.md を薄く保ち、手順は Skill・docs/ に置く。

### 試験
- 変更したら必ず実行する:
  ```bash
  python3 tests/smoke_test.py
  claude plugin validate . && claude plugin validate plugins/research-memory
  ```
- hook や文献スクリプトの挙動を変えたら、`tests/smoke_test.py` に項目を足す。
- 実際の Claude Code のセッションでしか確かめられないもの（下の「未検証」）は、ユーザーに確かめ方を伝える。

### 外部のコード・Skill を取り込むとき
- ライセンスを確かめ、`THIRD_PARTY_NOTICES.md` に出典を書く。中身（スクリプト・隠し文字）を読んでから取り込む。

## 変えてはいけない前提（ユーザーの決定）

- AI は論文・原稿の文章を書かない。手伝うのは調査と研究作業だけ。
- エージェントは Claude Code だけ。研究リポジトリの記憶は MEMORY.md（今の状態、編集は承認制）＋ logs/（1日1ファイル、目次付き、追記のみ）＋ docs/。
- 記憶の正本はリポジトリ（Git）。auto memory やプロジェクトメモリに運用ルールを置かない。
- ブランチは一切削除しない。不採用は `archive/<ブランチ名>` タグ。
- AI は研究リポジトリで依頼されるまでコミット・プッシュしない。
- Obsidian 連携は「今は」不要（あとで使えるよう、ノートは普通の Markdown リンクで書く。wikilink は使わない）。
- 機密情報の技術的な遮断（permissions.deny など）は「今は」入れない（AGENTS.md のルールのみ）。

## 現状（最終確認: 2026-11-01）

- 版: 0.3.6。タグ v0.3.0〜v0.3.5 はユーザーがサーバーで付けて GitHub に push 済み（clone したら `git fetch --tags` で取れる）。v0.3.6 のタグはまだ（ユーザーがサーバーで付ける）。
- Europa の `~/research-memory-marketplace` はこのリポジトリの clone。プラグインはこのフォルダから直接読み込まれる（`/reload-plugins` の表示で確認済み）。アップグレード時のタグを使った差分も、Europa で動いた（v0.3.1→v0.3.4）。
- vitcore-loco は template_version 0.3.5 までアップグレード済み（ブランチ `chore/002_update-research-memory`、MR でマージ予定）。0.3.6 の取り込みはまだ。
- 古くなりやすいので、この節は作業のたびに確かめて日付を更新する。

## 未検証（実際のセッションでしか確かめられないもの）

- Stop の AI 判定（prompt 型 hook）の精度と、トークン・待ち時間の負担。重ければ hooks.json から外してよいとユーザーに伝えてある。
- `fetch_bibtex.py` の実ネットワークでの取得（研究サーバーから doi.org / arxiv.org）。
- Claude Code の auto mode や Projects の「Work locally」スレッドで、PreToolUse の承認（MEMORY.md）が確認を出すか。
- PostToolUse（record_edit.py）の印が、実際のセッションで期待どおりに付くか。
