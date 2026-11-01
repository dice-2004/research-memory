---
name: research-init
description: 研究プロジェクトのリポジトリに、研究の記憶の仕組み（AGENTS.md・MEMORY.md・docs/・logs/ など）を初期設定する。新しい研究リポジトリで最初に一度だけ使う。
disable-model-invocation: true
---

# Initializing a research project

**Language: talk to the user in Japanese.** Copy the template files as they are (they are written in Japanese on purpose; do not translate them).

Copy `${CLAUDE_SKILL_DIR}/templates/` to the root of the current git repository to enable the research-memory system.

## Steps

1. Find the repository root with `git rev-parse --show-toplevel`. If this is not a git repository, stop and tell the user.

2. Copy according to this table. **If a file with the same name already exists, do not overwrite it**; tell the user the file name and ask whether to merge or keep it.

   | In templates/ | Destination |
   |---|---|
   | `AGENTS.md` | `AGENTS.md` |
   | `CLAUDE.md` | `CLAUDE.md` (only loads AGENTS.md via `@AGENTS.md`) |
   | `MEMORY.md` | `MEMORY.md` |
   | `CONTRIBUTING.md` | `CONTRIBUTING.md` (branch naming and tags) |
   | Everything under `docs/` (`research_context.md`, `datasets.md`, `related_work.md`, `references.bib`, `how_to_run.md`, `experiments.md`, `results.md`, `decisions.md`, `papers/_template.md`, `papers/README.md` (index), `literature/*.md`) | `docs/` (same layout) |
   | `logs/_template.md` | `logs/_template.md` |
   | `research-memory.json` | `.research-memory.json` |

   **On a second or later run** (e.g., after the plugin was updated), add only the files that do not exist yet. Then:
   - If the existing `AGENTS.md` differs from the template (e.g., it lacks rows of 「いつ何を使うか」, lines of the structure section, or rules in 「必ず守ること」), show the user the missing parts and offer to merge them, keeping the user's own edits (the `<...>` fields they filled in and any project-specific lines).
   - If the existing `docs/related_work.md` has old-format entries (sections starting with `### <論文タイトル>`), propose moving each entry into a note at `docs/papers/<citekey>.md` (only after approval).

3. Add this line to `.gitattributes` (create the file if missing, append otherwise). It keeps log lines appended on both branches when branches are merged.

   ```
   logs/*.md merge=union
   ```

4. Check that `watch` in `.research-memory.json` (directories whose changes count as research-relevant) matches the repository's actual layout. If not, propose changing it to directories that exist.

5. If `.gitignore` excludes `outputs/`, ask the user whether to commit only the experiment metadata in `outputs/` (configs and metric JSON files). Large files such as checkpoints can stay excluded.

6. Do not commit on your own. Show the user the command below and commit only if they ask.

   ```bash
   git add AGENTS.md CLAUDE.md CONTRIBUTING.md MEMORY.md docs/ logs/_template.md .research-memory.json .gitattributes
   git commit -m "notes: 研究の記憶の仕組みを初期設定"
   ```

7. Finally, tell the user what to fill in next (the `<...>` fields in AGENTS.md, CONTRIBUTING.md and docs/how_to_run.md, the research questions in docs/research_context.md, and docs/datasets.md). Never fill them in with your own guesses.
