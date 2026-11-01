# How to search the literature

Adapted and condensed from claude-scholar (Galaxy-Dawn, MIT License), research-ideation/references/literature-search-strategies.md. Write what you record in Japanese.

## 1. Expand keywords

1. Extract 2–3 core concepts from the research interest (e.g., "edge", "ViT", "anomaly detection").
2. List synonyms, paraphrases, and abbreviations for each concept.

   | Concept | Synonyms / variants |
   |---|---|
   | anomaly detection | anomaly detection, defect detection, novelty detection, out-of-distribution |
   | edge | edge, on-device, embedded, lightweight, efficient, quantization |

3. Combine with Boolean operators: `(synonyms of A OR ...) AND (synonyms of B OR ...)`
4. Also search by field-specific names (dataset names, metric names, representative methods), e.g., MVTec AD, AUROC, PatchCore.

## 2. Choose sources

| Source | Good for |
|---|---|
| arXiv | New preprints; narrow by category such as `cat:cs.CV` |
| Semantic Scholar | Following citation relations (citing / cited-by) |
| OpenAlex | Confirming bibliographic data; broad searches |
| Official venue pages (CVF Open Access, OpenReview, etc.) | Confirming the accepted version and official bibliographic data |
| Leaderboards such as Papers with Code | Finding baseline candidates (always confirm numbers in the original paper) |
| Google Scholar | Manual discovery only; never the authority for bibliographic data |

## 3. Process

- **Iterate**: refine the query using titles and keywords of the important papers from the first search, then search again.
- **Follow citations**: for core papers, check both references (backward) and citing papers (forward).
- **Follow authors**: check other papers by central authors and labs.
- Record every search in `docs/literature/searches.md`. Without a record, nobody can later tell whether something was searched.

## 4. Screening stages

1. **First pass on title and abstract**: relevance to the purpose, task, dataset. Leave a one-word reason for anything dropped (memo column of searches.md).
2. **Second pass on the full text**: evaluation conditions, baselines, information needed to reproduce (whether code is public).
3. Write notes for the remaining papers, starting with the core ones used for comparison or citation.

## 5. Secure an identifier

- Secure a DOI or arXiv ID before writing a note. If neither exists, use the official venue page URL.
- If only an abstract page or event page is found, look again for the official paper page. If still not found, set `source_type: abstract-only` and do not use it as evidence.
- If both a preprint and an accepted version exist, prefer the accepted version's bibliographic data and list both identifiers.
