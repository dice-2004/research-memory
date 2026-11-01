---
name: meeting-note
description: 指導教員とのミーティング、ゼミ、研究室での議論、ユーザーが一人で決めたことなど、AIとの会話の外で決まった研究上の内容を、ログと MEMORY.md に反映する。ユーザーがメモを貼り付けたときや「ゼミで〜と言われた」と伝えたときに使う。
argument-hint: "[ミーティングのメモ（貼り付けでも口頭でも可）]"
---

# Recording meetings and seminars

**Language: write every record in Japanese**, and keep the user's own wording as much as possible.

Decisions made outside the conversation with the AI steer the research but are the easiest to lose. Capture them reliably here.

## Steps

1. **Receive the content**: read the notes from the argument or the user's message (bullet points or casual speech are fine). If there are no notes, ask what meeting it was and what was decided.

2. **Classify** each item into one of the following. If unsure, ask the user instead of guessing.
   - **決定事項** (decisions; e.g., unify the metric to AUROC)
   - **指摘・宿題** (feedback and assignments; e.g., add one more baseline)
   - **助言・参考情報** (advice and references; e.g., a paper that may help)
   - **未決定・持ち越し** (undecided / carried over)

3. **Identify who decided** each decision: 指導教員, ゼミでの指摘, or ユーザー自身. If the notes do not say, ask.

4. **Record in the log**: append a block to today's log using the research-log Skill format.
   - Heading: `## HH:MM ミーティング: <誰と / 何の会>`
   - 種類 is 「ミーティング」; write 決定事項, 指摘・宿題, 助言・参考情報, and 持ち越し separately
   - Keep the user's words as close to verbatim as possible; do not mix in your interpretation
   - Mark papers mentioned as advice 「未確認」 until their existence is confirmed (use the lit-check Skill). Once confirmed, add them to 「読む予定」 in `docs/related_work.md`, noting who recommended them

5. **Propose MEMORY.md updates**: decisions go to 「確定した設計判断」 (with who decided), assignments to 「次にやること」, rejected ideas to 「検討したが却下した選択肢」. Show the proposed changes and write them only after the user approves (MEMORY.md edits require approval).

6. **Point out contradictions**: if a new decision conflicts with MEMORY.md, docs/, or the current code, do not silently align things. Show the conflict and ask the user which one is correct.

7. Do not commit unless the user asks. If asked, commit following research-log Skill §5.
