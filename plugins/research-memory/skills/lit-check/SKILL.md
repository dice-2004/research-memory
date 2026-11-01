---
name: lit-check
description: 関連研究の紹介・SOTAやベースラインの数値・新規性の主張・ライブラリのAPIや推奨設定など、記憶では古い可能性がある情報を扱うときに、Web検索や公式ドキュメントで確認し docs/related_work.md に記録する手順。
---

# Checking current information and recording sources

**Language: write records and answers to the user in Japanese.**

Model knowledge has a cutoff; SOTA results, related work, and library specifications are likely to be outdated. In the following situations, **do not answer from memory — verify first**.

- Stating SOTA numbers or comparisons with baselines
- Introducing related work, or discussing novelty or positioning
- Using a library or framework API or its recommended settings (verify for the version in use)
- Whenever you are about to write "recent", "近年", or "最新の" yourself

## Steps

1. **Verify with primary sources**: prefer arXiv, conference/journal papers, official documentation, and official repositories. Do not rely only on summary articles or blogs.

2. **Never invent what you cannot confirm**: if any of title, authors, year, venue, or URL/DOI cannot be confirmed, do not present the paper as existing. If verification fails, say explicitly 「記憶に基づく情報で未確認」 and do not assert it.

3. **Separate facts from interpretation**: keep the numbers and claims written in a paper (facts) apart from evaluations drawn from them ("SOTA", "better"). Always keep numbers together with their **evaluation conditions** (dataset, split, metric, backbone, training setup). Never rank numbers obtained under different conditions.

4. **Record**: do not let important findings stay in the conversation only.
   - For papers used in the research (baselines, method references, citation candidates), create a note at `docs/papers/<citekey>.md` following the literature Skill, then regenerate the index (`docs/papers/README.md`). Papers you cannot read now go to 「読む予定」 in `docs/related_work.md`.
   - When updating the SOTA / comparison table, always include evaluation conditions and the date checked.
   - Anything that could not be confirmed goes to the 「未確認・要調査」 section of `docs/related_work.md`.
   - Non-paper findings (library specifications, etc.) do not get a note; record them in the log if relevant.

   If the task becomes systematic (repeated searches, comparing several papers, looking for research gaps), switch to the literature Skill.

5. **Log it**: for checks that produced research-relevant findings, add a short record to today's log with the research-log Skill (which papers were checked and what was learned).

6. **Cite sources in answers to the user**: include the title, URL, and date checked.
