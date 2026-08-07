# Python replication results (RQ1)

Sources: `analysis/python_rq1_stats.ipynb`, `analysis/python_revision_extraction.ipynb`, `analysis/extract_answer_list.py`, `analysis/levenshtein_distances_python.csv`, `README.md`.
Java comparators throughout come from `technical-report/paper.pdf` only, per step 4 of the plan.

---

## 1. Selection criteria, confirmed identical to the Java study

`extract_answer_list.py --tag python` selects an answer when all three hold:

1. **Accepted:** the answer's `Id` equals its parent question's `AcceptedAnswerId`.
2. **Tagged:** the parent question carries the `python` tag, resolved through `PostTags` joined to `Tags.Id` (tag id 16). Answers carry no tags of their own, so the tag is taken from the parent question, exactly as the paper describes for Java.
3. **Revised:** `EXISTS (SELECT 1 FROM PostVersion pv WHERE pv.PostId = a.Id AND pv.PredPostHistoryId IS NOT NULL)`, i.e. edited at least once.

Criterion 3 is the same predicate the paper states for Java. The `EXISTS` form is used instead of `COUNT(*) > 1` purely for speed over `PostVersion`; the two are equivalent. **`--require-code-block` was in fact used**, contrary to the script's default. Verified against the database, see section 6: the unrestricted query returns 346,535 answers, whereas `acceptedWithVersionAnswer_python.txt` holds 305,768. The extraction stage duly found code blocks in 305,762 of the 305,763 answers it processed, which is the signature of a pre-filtered list. Both figures are reported above.

Code block extraction (`python_revision_extraction.ipynb`) follows the paper's rules exactly: `PostBlockTypeId = 2`, blocks tracked separately by `(PostId, LocalId)` rather than merged, one file per revision, `_recent` from `MostRecentVersion = 1`, `_original` from the root of the edit chain via `RootPostBlockVersionId`. Output tree: `Matcha_Study/python_files/{PostId}/`.

**Same SOTorrent release as the Java study**, the local `sotorrent` MySQL copy of 2020-12-31.

---

## 2. RQ1 headline numbers

| Quantity | Python | Java (paper) |
|---|---|---|
| Questions carrying the tag | 1,597,896 | not reported |
| Accepted answers | **840,132** | 874,438 |
| Code snippets in accepted answers (latest version) | **1,190,274** | 917,389 |
| Avg code snippets per accepted answer | **1.42** (std **1.32**) | 1.05 (std 1.22) |
| Accepted answers with more than one revision | **346,535** (see section 6) | 140,840 |
| ... as a percentage of accepted answers | **41.25%** | 16.11% |
| ... of which contain at least one code block | **305,768**, i.e. 88.24% | not reported |
| Code-bearing revised answers as a percentage of accepted | **36.40%** | not reported |
| Avg revisions per revised answer | **2.78** | 2.82 |
| Median revisions per revised answer | **2.0** | 2.0 |
| Std of revisions per revised answer | **1.43** | not reported |
| Max revisions | **111** | 53 |
| Most-revised post | **60662471** | 62805030 |
| Date span of the most-revised post | 2020-03-12 22:09:40 to 2020-03-17 04:22:21 (**4 days 6 hours**) | 8 July 2020 to 24 January 2021 (6 months 17 days) |
| Code snippets across all revisions (indexed set) | **1,640,080** | 283,838 |
| Files written by the extraction stage | 2,915,855 across 305,762 posts | not reported |

Extraction runtime: 7.8 minutes for 305,763 posts.

### Points worth making in the write-up

- **Python answers are edited about two and a half times as often as Java answers**, 41.25% against 16.11%, under an identical operational definition of "revised". This is the single largest divergence from the Java study and needs a careful sentence in the Discussion. Note the direction: it strengthens rather than weakens the paper's premise, since a larger share of accepted answers carries a potential improvement.
- **Python accepted answers carry more code**: 1.42 snippets per answer against Java's 1.05. Combined with the higher revision rate, the indexed corpus is far larger, 1,640,080 snippet revisions against Java's 283,838, a factor of 5.8.
- **The revision count per revised answer is almost identical**, 2.78 against 2.82, median 2.0 in both. So Python answers are edited *more often*, but when edited they are edited a *similar number of times*. This is a clean replication of the paper's per-answer editing behaviour.
- The most-revised Python answer (111 revisions in just over four days) is a very different phenomenon from the Java maximum (53 revisions over six and a half months). Worth one sentence, and worth eyeballing post 60662471 before making any claim about it.

---

## 3. Levenshtein distance, original versus latest code block

Computed by `code_diff.py` over every `{PostId}_{LocalId}_original.py` / `_recent.py` pair. Statistics as printed by the notebook, plus additional quantiles I computed directly from `levenshtein_distances_python.csv`.

| Statistic | Python | Java (paper) |
|---|---|---|
| Pairs analysed | **637,923** | not reported |
| Min | 0 | 0 |
| Max | **28,500** | 21,158 |
| Mean | **49.66** | 88.87 |
| Median | **0** | not reported |
| Std | **268.53** | 359.44 |

Additional quantiles (computed for this report, not in the notebook):

| | value |
|---|---|
| 25th percentile | 0 |
| 50th percentile | 0 |
| 75th percentile | 7 |
| 90th percentile | 103 |
| 95th percentile | 244 |
| 99th percentile | 866 |

**Zero-distance pairs: 438,152 of 637,923, i.e. 68.68%.** Only 199,771 pairs (31.32%) show any change at all. Restricted to the pairs that did change, mean distance is **158.57** and median is **43**.

This is an important observation and has no counterpart in the paper, which reports only the mean over all pairs. It means the great majority of Python code blocks are byte-identical between the original and the latest revision: the answer was edited, but that particular block was not. It also explains why Python's mean distance (49.66) is *lower* than Java's (88.87) despite Python having a higher revision rate, the mean is diluted by a large mass of zeros.

### Derived per-answer figures (computed for this report)

- Answers with at least one original/recent code block pair: **303,271**
- Average code blocks per revised answer: **2.10**
- Answers with **at least one code block that actually changed**: **163,360**, i.e. **53.87%** of the code-bearing revised answers and **19.44%** of all 840,132 accepted answers.

Three percentages are therefore available, and the report must keep them apart:

| Measure | Python |
|---|---|
| Accepted answers edited at least once (**comparable to Java's 16.11%**) | **41.25%** |
| ... and containing at least one code block | 36.40% |
| ... and containing a code block that actually changed | 19.44% |

Use 41.25% as the RQ1 headline, since that is the quantity the paper reports for Java. Report 19.44% as the stricter code-change-only variant, and do **not** present it as the direct comparator to 16.11%.

---

## 4. Figures available

| Figure | File | Paper counterpart |
|---|---|---|
| Revisions distribution histogram | `analysis/post_revisions_histogram.pdf` | Fig 8 |
| Levenshtein boxplot, with outliers | `python_levenshtein_boxplot.pdf` and `.png` (repo root) | Fig 9 |
| Levenshtein boxplot, outliers hidden | `python_levenshtein_boxplot_no_outliers.pdf` and `.png` (repo root) | none |
| Code size histograms per popularity group | `analysis/code_size_histogram_{lesser,medium,high}.pdf` | Fig 7 (Java) |

Caveats on the files:

- `analysis/post_revisions_histogram.pdf` is the **Python** histogram: the notebook's `HIST_OUTPUT` is the unprefixed name. The JavaScript one is `javascript_post_revisions_histogram.pdf`. Rename to `python_post_revisions_histogram.pdf` when copying into `technical-report/figures/` to avoid confusion with the Java figure.
- There are two generations of boxplot files: `analysis/levenshtein_boxplot_python.pdf` (older) and `python_levenshtein_boxplot.pdf` at the repo root (written by the current notebook run, dated 24 July). **Use the repo-root pair.**
- The histogram uses a log-scaled y axis, unlike Fig 8 in the paper, which uses a linear axis with an annotation box. Decide in step 7 whether to regenerate for consistency across the three languages. Recommendation: regenerate all three on the same axes, since the Python maximum of 111 revisions would otherwise be invisible.

---

## 5. Verification of the answer-list provenance (resolved)

Run against the local `sotorrent` instance on 7 August 2026:

```sql
SELECT COUNT(*) FROM (
    SELECT a.Id
    FROM Posts q
    JOIN PostTags pt ON pt.PostId = q.Id AND pt.TagId = 16
    JOIN Posts a ON a.Id = q.AcceptedAnswerId
    WHERE q.PostTypeId = 1
      AND EXISTS (SELECT 1 FROM PostVersion pv
                  WHERE pv.PostId = a.Id AND pv.PredPostHistoryId IS NOT NULL)
) x;
-- 346535
```

The unrestricted count is **346,535**, against the 305,768 ids in `acceptedWithVersionAnswer_python.txt`. The file was therefore built with `--require-code-block`, and 88.24% of revised Python accepted answers contain a code block, closely matching the 87.45% measured for JavaScript.

The same query run for JavaScript (`TagId = 3`) returned **447,379**, exactly the size of `acceptedWithVersionAnswer_javascript.txt`, confirming that the JavaScript list is unrestricted and that its 39.10% needs no adjustment. The discrepancy is Python-specific.

Consequences:

1. The RQ1 headline for Python is **41.25%**, not 36.40%. The latter is the code-bearing subset.
2. Every downstream figure (revision counts, Levenshtein distances, the extracted snippet tree, and the Matcha index) is computed over the 305,768 code-bearing answers. That is correct and desirable, since the study is about code edits, but the Methodology must say so explicitly, otherwise the 41.25% headline and the 1,640,080 indexed snippets appear to come from the same set when they do not.
3. `python_rq1_stats.ipynb`, `javascript_rq1_stats.ipynb` and `python_rq1_stats.py` have been changed to select the filtered set from the database with the canonical predicate rather than reading the id file, and to cross-check the file and report any disagreement. Re-running the Python notebook will now report 346,535 and warn that the file disagrees. The JavaScript list needs no such correction, it was already built unrestricted.

---

## 6. Open items for later steps

1. The notebook cell that imports `code_diff` raised a `NameError: name 'Path' is not defined` on the recorded run (the `from pathlib import Path` lives in an earlier cell that had not been re-executed). The subsequent cells nonetheless produced output, so the recorded statistics are valid, but the notebook is not cleanly runnable top to bottom. Not blocking for the report; worth fixing before the replication package is published.
2. **Done in step 5:** RQ2 results for Python are in `notes-rq2-clones.md`, aggregated by `analysis/aggregate_so_gh_clones.py`.
3. The paper's Table 4 and Table 5 have no counterpart here: the replication searched a fixed, balanced sample of 100 projects per language (33 low, 33 medium, 34 high) rather than deriving quartiles from a Python project population. Recorded in `notes-rq2-clones.md` section 5 as a scale caveat for the Methodology and Threats to Validity.
