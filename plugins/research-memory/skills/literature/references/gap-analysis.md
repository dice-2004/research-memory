# Finding research gaps

Adapted and condensed from claude-scholar (Galaxy-Dawn, MIT License), research-ideation/references/gap-analysis-guide.md and research-contract.md. Write what you record in Japanese, keeping the Japanese field labels below exactly as written.

## Types of gaps

| Type (label to write) | Example |
|---|---|
| 文献 (literature) | No coherent body of work on a problem setting |
| 手法 (method) | A weakness or assumption shared by existing methods (e.g., assumes a large backbone and never evaluates compute cost on edge devices) |
| 応用 (application) | Methods exist but have not been tried in a specific environment or data (real factory images, low-resource devices) |
| 評価 (evaluation) | Insufficient evaluation conditions, metrics, or benchmarks (e.g., only accuracy, no latency or power) |
| 時間 (temporal) | A new technique (new architecture, quantization method) has not been applied yet |

## What to look at

1. Which problem settings and datasets are covered, and how much
2. Strengths and weaknesses of each method (summarized in the `taxonomy.md` table)
3. Completeness of experimental setups (baselines, ablations, reporting of compute cost)
4. Usability of datasets and benchmarks
5. The gap between theory and practical deployment

A matrix (method × dataset × metric × compute cost) helps: empty cells are gap candidates.

## Format of each item in gaps.md

```markdown
### G-01: <ギャップの名前>
- 種類: <文献 | 手法 | 応用 | 評価 | 時間>
- 内容: <何が足りないか>
- 根拠: <ノートへのリンクと場所。例: [Tanaka 2024](../papers/tanaka2024vit.md) 表3>
- 強さ: speculative | observed | supported | strong
- 調べた範囲: <searches.md の何番の検索で確認したか>
- 言えること: <根拠に見合った表現。例: 「今回調べた範囲では、〜の評価は見当たらなかった」>
- 言いすぎ: <避けるべき強い表現。例: 「〜は誰も研究していない」>
- 次の確認: <追加で調べること、または試す実験>
- 判断: 追う | もっと読む | 保留 | 捨てる（判断したのはユーザー）
```

## Cautions

- **Never assert "nobody has done this".** The most you can say is "not found within the searched scope", and the scope must always be written.
- That a gap exists and that it is worth filling are different questions. Decide the value (why it matters, whether it is feasible) with the user, and record the decision in the log with the research-log Skill.
- The stronger the gap, the harder you should look for counter-evidence (papers that actually do something similar). If found, add it and lower the strength.
- Record discussions with the advisor or lab members with the meeting-note Skill.

## Research question card (when moving from a gap to a research question)

When a gap becomes a research question, propose adding this card to `docs/research_context.md` (the user decides).

```markdown
### 研究課題カード: <名前>
- 問い:
- 種類: 探索的 | 検証的 | 応用
- 仮説:
- なぜ重要か:
- 今ある根拠: <ノートへのリンク>
- 足りない根拠:
- 何が見つかれば支持されるか:
- 何が見つかれば否定されるか:
- 最小の次の一歩:
```
