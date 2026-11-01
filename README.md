# research-memory

研究の記憶（現在の状態・判断の経緯・ミーティングでの決定）を、Claude Code のセッションをまたいで失わないためのプラグイン。

## 仕組み

| 層 | 中身 | 役割 |
|---|---|---|
| ルール | `AGENTS.md`（研究リポジトリに置く） | 必ず守ることと、いつ何を使うか |
| 手順 | Skills: `research-log` / `meeting-note` / `lit-check` / `literature` / `experiment` / `research-init` | 記録・調査・文献管理・実験のやり方 |
| 強制 | hooks（下表） | 読み込み・記録漏れ防止・承認制 |

| hook | いつ | 何をするか |
|---|---|---|
| SessionStart | セッション開始・再開・圧縮後 | MEMORY.md、当日ログの目次、未記録の `archive/` タグ、未コミットの変更（あなたの変更の検出用）を自動で読み込ませる |
| Stop（スクリプト） | 応答が終わるたび | `.research-memory.json` の `watch`（既定は `src/` `configs/` `scripts/`）がこのセッション中に変わったのに今日のログが更新されていなければ、終了を止めてログを書かせる。同じ変更では1回だけ |
| Stop（AI判定） | 応答が終わるたび | 議論での決定・考察・ミーティング報告などがあったのにログに書いていなければ、ログを書かせる |
| PreCompact | コンテキスト圧縮の直前 | 会話の全文の控えを `.git/research-memory/transcripts/` に保存（圧縮後に未記録の内容をログに起こせるように）。控えは14日で自動削除 |
| PreToolUse | ファイル編集・コマンド実行の前 | MEMORY.md への書き込みを毎回あなたの承認制にする |
| PostToolUse | ファイル編集の後 | エージェントが編集したファイルを記録する（コミットせずに残った変更を、次のセッションで「エージェントの変更」と「あなたの変更」に見分けるため。記録は `.git/research-memory/` の中） |

hooks は、リポジトリのルートに `MEMORY.md` と `logs/` があるときだけ動きます（研究と関係ないリポジトリでは何もしません。ただし Stop の AI 判定だけはプラグインが有効な場所すべてで動くので、下の手順どおり**研究リポジトリ単位で有効化**してください）。

## 必要なもの

- 研究サーバー上の Claude Code（VS Code の Remote-SSH 拡張・Orca・ターミナルのどれから使っても同じ）
- Python 3.9 以上（標準ライブラリのみ使用）、git

## インストール（研究サーバー上で）

VS Code 拡張機能は Claude Code 本体を内蔵していますが、`claude` コマンドを PATH に追加しません。そのため、サーバーのターミナルで `claude` が見つからないのは正常です。プラグインの登録には CLI を使うので、先にサーバーへ CLI を入れます（拡張機能と CLI は同じ `~/.claude/` の設定を読むので、CLI で入れたプラグインは拡張機能でも有効になります）。

```bash
# 0. サーバーに Claude Code CLI を入れる（1回だけ。~/.local/bin/claude に入る）
curl -fsSL https://claude.ai/install.sh | bash
claude --version   # 見つからなければ新しいターミナルを開く

# 1. このリポジトリを研究サーバーに clone する
git clone git@github.com:dice-2004/research-memory.git ~/research-memory-marketplace
# 2. マーケットプレイスとして登録（1回だけ）
claude plugin marketplace add ~/research-memory-marketplace

# 3. 研究リポジトリの中で、そのリポジトリだけに有効化
cd ~/path/to/your-research-repo
claude plugin install research-memory@research-tools --scope local
```

`--scope local` は「自分だけ・このリポジトリだけ」で有効にする設定で、研究室の他の人には影響しません。別の研究リポジトリや別のサーバーでも、2〜3 を実行すれば同じ仕組みが入ります。

### 更新と逆輸入

ローカルディレクトリのマーケットプレイスは、その場所のファイルをそのまま読みます。したがって更新は clone した場所で `git pull` して、Claude Code で `/reload-plugins`（または新しいセッション）を実行するだけです。再登録は要りません。

サーバー上でプラグインを直したときは、その場でコミットして push してください。どこを直したかは `git diff` で確認できます。

インストール後、VS Code の Claude Code パネルで次を確かめてください。

- `/plugins` を開き、research-memory が有効になっている
- Claude に「`hostname` と `python3 --version` を実行して」と頼み、**サーバーのホスト名**と Python 3.9 以上が返る（hooks は Claude Code が動いているマシン＝サーバー上で実行されるため）

## 初期設定（研究リポジトリごとに1回）

Claude Code で次を実行します。

```
/research-memory:research-init
```

AGENTS.md・CLAUDE.md・CONTRIBUTING.md・MEMORY.md・docs/（実験一覧 experiments.md、結果の索引 results.md、実行手順 how_to_run.md、過去の判断 decisions.md を含む）・logs/_template.md・.research-memory.json・.gitattributes（ログのマージ設定）が作られます。その後、AGENTS.md・CONTRIBUTING.md・docs/how_to_run.md の `<...>` と docs/research_context.md を埋めてください（AI と相談しながら埋めてかまいません。確定させるのはあなたです）。

## 新しい版に更新する（プラグインと研究リポジトリの両方）

プラグインの更新は2段階です。**1でプラグイン本体（Skills・hooks）が新しくなり、2で研究リポジトリのファイル（AGENTS.md・docs/ など）にテンプレートの変更を取り込みます。** 2をしないと、新しいルールや表の行は研究リポジトリに入りません。リポジトリの版がプラグインより古いと、セッション開始時に Claude が知らせます。

### 1. プラグイン本体（サーバーごとに1回）

```bash
cd ~/research-memory-marketplace && git pull
claude plugin list | grep research-memory   # 版を確かめる
```

Claude Code で `/reload-plugins` を実行します（開いているセッションすべて。新しいセッションでもよい）。

### 2. 研究リポジトリ（リポジトリごとに1回）

1. 作業ツリーをきれいにする（記録や設定の未コミットの変更をコミットしておく）。`CONTRIBUTING.md` の決まりがあれば、更新用のブランチを作る（例: `chore/NNN_update-research-memory`）。
2. Claude Code で `/research-memory:research-init` を実行する。既存のリポジトリでは**アップグレード**として動き、次の順に進む。
   - 前回の版（`.research-memory.json` の `template_version`）から、テンプレートの何が変わったかを一覧にする
   - 足りないファイルだけを追加する（既存のファイルは上書きしない）
   - ファイルごとに「テンプレートにあって、このリポジトリにない汎用の部分」を示すので、取り込むものを選ぶ。研究固有の内容は残る。あなたの決めたことと食い違う変更は、両方を見せて尋ねる
   - Claude Code の auto memory にだけある運用ルールがないかを確かめる
   - `template_version` を更新し、ログに記録する
3. `git diff` で確かめて、よければ「コミットして」と頼む（AI は依頼されるまでコミットしない）。MR を作るなら、その後に push する。

別のサーバーや別の研究リポジトリでも、同じ手順で更新できます。

### 版を上げる側（プラグインを直す人）がすること

- `plugins/research-memory/.claude-plugin/plugin.json` の `version` と、`templates/research-memory.json` の `template_version` を同じ版に上げる
- コミットに版のタグを付けて push する: `git tag -a v<版> -m "<変更の要約>" && git push origin main --tags`（アップグレード時の差分の一覧は、このタグを使って作られる）

## ログの形式

- ファイルは `logs/YYYY-MM-DD.md`（1日1ファイル、日付は日本時間）。研究上のイベントがあったときだけ、末尾にブロックを追記する
- ファイル冒頭に目次、各ブロックは `## HH:MM 要約` の見出しで、種類・決めた人・経緯と判断根拠・やり取り・次にやること を書く
- 定義は `plugins/research-memory/skills/research-log/SKILL.md`、記入例は初期設定で作られる `logs/_template.md`

## 使い方

ふだんは何もしなくても、記録が必要な場面で hooks が促します。手動で呼ぶ場合:

- ミーティング・ゼミの内容を記録: `/research-memory:meeting-note <メモを貼り付け>`
- その他の Skill もエージェントが場面に応じて使います（AGENTS.md の「いつ何を使うか」）

## 運用ルール（決めたこと）

- logs/・MEMORY.md・docs/ は研究コードと同じリポジトリで GitLab 管理。記録の更新は `notes:` で始まる別コミットにする。AI は依頼されるまでコミットしない（区切りでコミット内容を提案するだけ）
- 案ごとにブランチを切り、MEMORY.md もブランチごとに分かれてよい。マージ時の MEMORY.md の書き換えは自分で指示する
- 不採用のブランチは削除せず `archive/<名前>` タグを付けて保存。ログは必要に応じて手動で main にコピーする（MEMORY.md の却下表に載っていないタグは、セッション開始時に知らされる）
- `.research-memory.json` で監視ディレクトリ・タイムゾーンを変更できる

## 注意

- PreCompact で保存する会話の控えは `.git/` の中にあり、GitLab には上がりません。書き損じ防止の一時的な保険なので、`transcript_retention_days`（既定14日）を過ぎると自動で削除されます。研究の記録として残るのは logs/ の要約ログです
- hook の動作確認は Claude Code で `/hooks` を開くと一覧できます
- 文献管理（`literature` Skill）の書式とルールは claude-scholar（MIT License）を参考にしています。出典とライセンスは `plugins/research-memory/THIRD_PARTY_NOTICES.md` にあります
- 使い方の詳細は `README-use.md` を参照してください
- 言語: AI だけが読む部分（Skill の本文と参考資料、SessionStart・Stop の hook が Claude に渡す文、Stop の AI 判定プロンプト）は、トークン節約のため英語で書いています。人が読むもの（テンプレート、記録、Skill の説明文、MEMORY.md 編集時の承認メッセージ、スクリプトの出力）は日本語です。記録は日本語で書くよう、AGENTS.md と各 Skill に明記しています
