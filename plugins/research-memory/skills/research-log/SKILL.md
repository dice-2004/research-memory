---
name: research-log
description: 研究上のイベント（意思決定・実験の実施や結果・考察・データや評価方法の変更・研究に影響するコード変更・ユーザーのコード変更の意図確認・関連研究の重要な知見）が起きたとき、logs/YYYY-MM-DD.md にブロックを追記し、必要なら MEMORY.md を更新する手順。Stop hook から記録を求められたときも使う。
---

# Recording the research log

**Language: write every record (logs/, MEMORY.md, docs/) in Japanese.** Keep the Japanese headings and field labels shown below exactly as written; other files and the user rely on them.

This procedure keeps the research memory from being lost. **logs/ is the chronological record of *why* things were done; MEMORY.md is a snapshot of *where things stand now*.** Do not mix the two roles.

## 1. Decide whether to record

Record when any of the following happens. If only part of the conversation qualifies, record only that part.

- A research decision (research question, hypothesis, metric, baseline, data split, adopting or rejecting a method)
- Running an experiment, its results, or discussion of the results
- A change to the dataset, preprocessing, or evaluation method
- A code change that affects results or experimental conditions
- Confirming the intent of a code change the user made (question, answer, follow-up)
- A research-relevant finding from the literature
- Research information that the next session needs

Do not record general programming questions, fixes that do not affect the research, or small talk. **When in doubt, record.**

## 2. Log file

- One file per day: `logs/YYYY-MM-DD.md`. Use the "今日のログファイル" given at session start (it uses the configured time zone even if the server clock is UTC).
- If the file does not exist, create it following the top of `logs/_template.md` (title and the `## 目次` heading).
- **Never rewrite existing blocks.** Append new blocks at the end of the file.
- After appending a block, **add one line to the 目次 at the top**: `- [HH:MM 短い要約](#hhmm-短い要約)`
- Block heading: `## HH:MM 短い要約` (time in the same time zone as the file name).
- **Following up on earlier blocks.** Because blocks are never rewritten, when an earlier 「次にやること・申し送り」 is done or withdrawn, an earlier （未決定） item is decided, or an earlier block turns out to be wrong, say so in the new block and name the earlier one by date and time (e.g., 「2026-10-20 17:02 の申し送りは取り下げ」「2026-10-29 10:15 の案は採らない」「2026-10-20 17:02 の記録では 01・03 だけと書いたが、02 も同じだった」).
- A proposal waiting for the user's answer is recorded with 種類 「意思決定（未決定）」 and 決めた人 「（未決定。ユーザーの返事待ち）」; the answer gets its own block that names the proposal.

## 3. Block contents (write only the fields that apply)

```markdown
## HH:MM 短い要約

**種類**: 意思決定 / 実験 / 考察 / ミーティング / コード変更 / 意図確認 / 文献
**決めた人**: ユーザー / 指導教員 / ゼミでの指摘 / エージェントの提案をユーザーが採用 / （未決定）

**目的・きっかけ**
**変更したファイル・コード**
- `<パス>`: <何をどう変えたか>
- 挙動への影響: <計算・結果が変わるか>
**経緯・判断根拠**
- 観測した事実:
- 確認したこと: <実行・照合して確かめたこと。確かめていないことは「未確認」>
- 採用した判断とその理由:
- 却下した選択肢とその理由:
**ユーザーとのやり取り**
- 相談 / 質問:
- 回答・決定:
**参照した外部情報**（出典・確認日）
**実験**（実験ID・設定・結果・考察）
**次にやること・申し送り**
```

Rules:
- **Separate observed facts from inference and interpretation.** Write "〜と考えられる" when it is an inference; never state it as fact.
- Do not dump your whole thought process. Write the research decision and its grounds.
- Never write secrets (passwords, API keys), personal information, or raw data contents (lab members can see the repository).
- Always write numbers together with the experiment ID.
- Record only what has happened. Something the user plans (a merge, a push, a meeting) is written as 予定, not as done; when MEMORY.md or docs/ are written ahead of time on the user's instruction, say so and correct them once the real state is known.
- Do not record planned events as done (e.g., "merged" before the merge happened), even if asked to write ahead; write them as planned (「予定」) and update once they happen.
- When an earlier 申し送り is resolved or withdrawn, say so in the new block with the time of the earlier block (e.g., 「10:15 の申し送りは取り下げ」), so the next session does not pick it up again.
- When the user states a standing preference or rule (e.g., "don't run anything when I ask for an estimate"), also propose adding it to AGENTS.md; a rule that exists only in a log is easily lost.

## 4. Updating MEMORY.md

When the *current state* of the research changes (experiment status, hypotheses, settled design decisions, rejected options, open problems, next steps), update the matching section of MEMORY.md (sections such as 「現在の実験状態」「現在の仮説」「確定した設計判断」「検討したが却下した選択肢」「未解決の問題」「次にやること」).

- **MEMORY.md holds only current facts.** When something changes, rewrite it; do not narrate history there, link to the log date instead.
- In 「確定した設計判断」 and 「検討したが却下した選択肢」, write **who decided** (決めた人).
- Never record your own guesses as settled. Put anything undecided under 「未解決の問題」 or 「現在の仮説」.
- A hook requires the user's approval for every MEMORY.md edit. Keep changes minimal so the user can review the diff on the approval screen.
- Keep MEMORY.md short. When a phase of experiments ends, or MEMORY.md exceeds about 5000 characters, propose moving overturned or finished decisions from 「確定した設計判断」「検討したが却下した選択肢」 to `docs/decisions.md` (with the date and a link to the log). Move them only after approval.

## 5. Commit (only when the user asks)

**Do not commit unless the user asks** (it clutters the history). At a natural stopping point, you may suggest the commit below in one line. When the user asks, commit only the record files, never mixed with research code changes:

```bash
git add logs/ MEMORY.md docs/
git commit -m "notes: <短い要約>"
```

- Do not push (the user does).
- Never use `git add -A` or `git add .`, so the user's uncommitted code changes are not swept in.
