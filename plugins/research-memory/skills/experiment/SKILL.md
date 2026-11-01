---
name: experiment
description: 実験の計画・実行・評価・結果報告を行うときの手順。実験IDの付け方、再現性・比較の公平性・データリークのチェックリスト、評価結果の報告方法を含む。新しい実験を始めるとき、結果を比較・解釈するときに使う。
---

# Running experiments

**Language: write records and reports to the user in Japanese.**

## 1. Before the experiment (plan)

Write the following in 1–3 lines and agree on it with the user before starting.

- The hypothesis (what is being tested) and **what result would refute it**
- The baselines
- The metrics and the success criterion
- The research question it serves (the experiment design table in docs/research_context.md)

Get the user's confirmation before long or expensive runs (roughly over 1 hour, or long GPU occupation). Run a smoke test first on small data with few epochs.

If `docs/how_to_run.md` exists, it is the authoritative run procedure: follow its pre-run checks, run steps, and post-run recording exactly, and do not improvise a different way of running.

## 2. Experiment IDs and branches

- Give every experiment a unique ID `exp-NNN`, where NNN is the branch number from `CONTRIBUTING.md` (e.g., branch `exp/004_topk` → `exp-004`). New branches take the current maximum + 1. Several runs that belong together (e.g., a reproduction) share one ID and one branch.
- Output goes to `outputs/exp-NNN_<name>/` (or the results directory named in AGENTS.md). **Never overwrite an existing experiment directory**; to redo a run while keeping the old one, use a new ID.
- Always use the ID in logs, MEMORY.md, and reports.
- When the experiment (branch) starts, add one row to `docs/experiments.md`.

## 3. Reproducibility checklist

Save the following in each experiment's output directory.

- [ ] The config used (the file in configs/; do not override it with hard-coded values or command-line arguments)
- [ ] Random seeds (Python / NumPy / PyTorch, etc.)
- [ ] The git commit hash (and a note if there were uncommitted changes)
- [ ] Run date/time and versions of the main libraries
- [ ] Metric values in machine-readable form (e.g., JSON)

## 4. Fair-comparison checklist

Being reproducible and being a valid comparison are different things.

- [ ] Are data split, preprocessing, augmentation, training budget, and evaluation conditions the same for the baselines and the proposed method?
- [ ] Are any conditions that cannot be matched stated explicitly in the report?
- [ ] Were the data split, metrics, or evaluation conditions changed **after seeing results**? (If a change is needed, state the reason first and get the user's approval.)
- [ ] When results were bad, were metrics or settings silently changed to make it look "improved"? (Never do this.)

## 5. Data-leakage checklist

- [ ] Does the same individual, product, video, etc. appear across train / val / test?
- [ ] What were preprocessing steps (normalization, feature extraction) fit on — train only, or all data?
- [ ] Was the test set used for hyperparameter tuning or method selection? (The test set is for final evaluation only.)
- [ ] Is augmentation applied after the data split?

See docs/datasets.md for dataset-specific caveats.

## 6. Reporting results

- Do not claim superiority from a single run. Report the mean and spread (e.g., standard deviation) over multiple seeds (roughly 3–5), together with the number of runs.
- Check whether differences between methods fall within the spread. Whether a statistical test is needed depends on the situation (do not apply a particular test mechanically); note in the discussion what you considered.
- **Separate observed results from interpretation.**
- **Record failed experiments and bad results too.** Do not cherry-pick favorable results.

## 7. Recording

- Add one row to `docs/results.md`: path of the final table (the original file), main numbers, comparison targets with their sources, verification status, and a link to the log. Copy numbers from the original file; never retype them from memory.
- Update the row in `docs/experiments.md` (状態, 結論).
- With the research-log Skill, append an experiment block to today's log (experiment ID, purpose, settings, results, discussion, next steps).
- Propose an update to 「現在の実験状態」 in MEMORY.md (requires approval).

## 8. Quoting numbers later

When a number is needed for MEMORY.md, a report, slides, or the thesis, look it up in `docs/results.md` first, then confirm the value in the original file, and say which row and file it came from.
