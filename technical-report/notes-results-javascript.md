# JavaScript replication results (RQ1)

Sources: `analysis/javascript_rq1_stats.ipynb`, `analysis/javascript_revision_extraction.ipynb`, `analysis/extract_answer_list.py`, `analysis/levenshtein_distances_javascript.csv`.
Java comparators come from `technical-report/paper.pdf` only, per step 4 of the plan.

---

## 1. Selection criteria

Identical to the Python run, and therefore to the Java study: accepted answer, parent question tagged `javascript` (tag id 3, 2,130,783 questions), and at least one `PostVersion` row with `PredPostHistoryId IS NOT NULL`. Same SOTorrent 2020-12-31 local copy, same `(PostId, LocalId)` block tracking, same `_original` taken from `RootPostBlockVersionId` and `_recent` from `MostRecentVersion = 1`. Output tree: `Matcha_Study/javascript_files/{PostId}/`, extension `.js`.

---

## 2. RQ1 headline numbers

| Quantity | JavaScript | Python | Java (paper) |
|---|---|---|---|
| Questions carrying the tag | 2,130,783 | 1,597,896 | not reported |
| Accepted answers | **1,144,185** | 840,132 | 874,438 |
| Code snippets in accepted answers (latest version) | **1,591,776** | 1,190,274 | 917,389 |
| Avg code snippets per accepted answer | **1.39** (std **1.24**) | 1.42 (std 1.32) | 1.05 (std 1.22) |
| Accepted answers with more than one revision | **447,379** (verified, section 5) | 346,535 | 140,840 |
| ... as a percentage of accepted answers | **39.10%** | 41.25% | 16.11% |
| ... of which contain at least one code block | 391,264, i.e. 87.45% | 305,768, i.e. 88.24% | not reported |
| Code-bearing revised answers as a percentage of accepted | 34.20% | 36.40% | not reported |
| Avg revisions per revised answer | **2.68** | 2.78 | 2.82 |
| Median revisions per revised answer | **2.0** | 2.0 | 2.0 |
| Std of revisions per revised answer | **1.31** | 1.43 | not reported |
| Max revisions | **68** | 111 | 53 |
| Most-revised post | **9550412** | 60662471 | 62805030 |
| Date span of the most-revised post | 2012-03-03 22:24:30 to 2020-11-26 21:47:46 (**8 years 8 months**) | 4 days 6 hours | 6 months 17 days |
| Code snippets across all revisions (indexed set) | **1,998,016** | 1,640,080 | 283,838 |
| Posts with at least one code block | **391,264** of 447,379 (87.45%) | 305,762 of 305,768 (99.998%) | not reported |
| Files written by the extraction stage | 3,584,721 | 2,915,855 | not reported |

Extraction runtime: 10.5 minutes for 447,376 posts.

### Points worth making in the write-up

- **Both replication languages are edited far more than Java**: Python 41.25% (corrected, see section 5), JavaScript 39.10%, against Java's 16.11%. The two dynamically typed languages behave alike and Java is the outlier. This is a stronger and cleaner statement than either replication makes on its own, and it should be the headline of the Discussion. Python edges ahead of JavaScript, but the two are close enough that the ordering between them should not be emphasised.
- **Revisions per revised answer is remarkably stable across all three languages**: 2.68, 2.78, 2.82, median 2.0 in every case. The paper's per-answer editing behaviour replicates almost exactly. So the languages differ in *how many* answers get edited, not in *how much* an edited answer gets edited.
- **Both replication languages carry more code per answer than Java**, 1.39 and 1.42 against 1.05. Together with the higher revision rates this yields indexed corpora roughly six to seven times the size of the Java one (1,998,016 and 1,640,080 snippet revisions against 283,838).
- The most-revised JavaScript answer, post 9550412 with 68 revisions spread over eight years and eight months, contrasts with Python's 111 revisions in four days. The three maxima describe three quite different editing patterns, sustained maintenance (JavaScript), a burst (Python), and something in between (Java). One sentence at most, and check post 9550412 before characterising it.

---

## 3. Levenshtein distance, original versus latest code block

| Statistic | JavaScript | Python | Java (paper) |
|---|---|---|---|
| Pairs analysed | **793,362** | 637,923 | not reported |
| Min | 0 | 0 | 0 |
| Max | **20,690** | 28,500 | 21,158 |
| Mean | **48.66** | 49.66 | 88.87 |
| Median | **0** | 0 | not reported |
| Std | **228.44** | 268.53 | 359.44 |

Additional quantiles (computed for this report, not in the notebook):

| Percentile | JavaScript | Python |
|---|---|---|
| 25th | 0 | 0 |
| 50th | 0 | 0 |
| 75th | 8 | 7 |
| 90th | 115 | 103 |
| 95th | 253 | 244 |
| 99th | 798 | 866 |

**Zero-distance pairs: 537,142 of 793,362, i.e. 67.70%** (Python 68.68%). Restricted to the pairs that changed, mean is **150.68** and median is **48** (Python 158.57 and 43).

The two replication languages agree closely on every distance statistic, and both sit well below Java's mean of 88.87. The distributions are near-identical, which is a useful robustness point: the same editing signature appears in two unrelated ecosystems.

### Derived per-answer figures (computed for this report)

| | JavaScript | Python |
|---|---|---|
| Answers with at least one original/recent pair | 387,883 | 303,271 |
| Average code blocks per revised answer | 2.05 | 2.10 |
| Answers with at least one code block that changed | **207,945** | 163,360 |
| ... as a percentage of revised answers | **53.61%** | 53.87% |
| ... as a percentage of all accepted answers | **18.17%** | 19.44% |

The proportion of revised answers in which the code actually changed is essentially the same in both languages, 53.61% and 53.87%. Neither has a counterpart in the paper.

As with Python, report 39.10% as the figure directly comparable to Java's 16.11%, and 18.17% as the stricter code-change-only variant, without equating the latter to the Java headline.

---

## 4. Figures available

| Figure | File | Paper counterpart |
|---|---|---|
| Revisions distribution histogram | `analysis/javascript_post_revisions_histogram.pdf` | Fig 8 |
| Levenshtein boxplot, with outliers | `javascript_levenshtein_boxplot.pdf` and `.png` (repo root) | Fig 9 |
| Levenshtein boxplot, outliers hidden | `javascript_levenshtein_boxplot_no_outliers.pdf` and `.png` (repo root) | none |

Same caveats as Python: log-scaled y axis on the histogram unlike the paper's Fig 8, and the repo-root boxplots are the current ones. Regenerate all three languages on common axes in step 7.

---

## 5. Open items

1. **Resolved, both languages verified against the database on 7 August 2026.**

   | Tag | Unrestricted query | Answer-list file | Verdict |
   |---|---|---|---|
   | `python` (TagId 16) | **346,535** | 305,768 | list built with `--require-code-block` |
   | `javascript` (TagId 3) | **447,379** | 447,379 | list unrestricted, exact match |

   The suspicion was correct for Python and the JavaScript list is clean. Consequences:

   - Python's RQ1 headline is **41.25%**, not 36.40%, so **Python has the highest revision rate of the three languages**, ahead of JavaScript's 39.10%.
   - JavaScript's 39.10% needs no adjustment.
   - Both languages now have the same three-level breakdown available: edited at all, edited and code-bearing, edited with a code change.

   `python_rq1_stats.ipynb`, `javascript_rq1_stats.ipynb` and `python_rq1_stats.py` now select the filtered set from the database with the canonical predicate instead of reading the id file, and cross-check the file, so this class of drift cannot recur. Re-running the Python notebook will report 346,535 and warn that the file disagrees; the JavaScript notebook will report an exact match.

2. The three-language comparison table for the Results and Discussion sections can now be assembled in full from this file and `notes-results-python.md`. Java column comes from `notes-paper.md`.

3. RQ2 material for JavaScript lives in `analysis/so-gh_clones/search_results_js/`, handled in step 5, together with the project counts per popularity group from `javascript_repos_stars*.txt`.
