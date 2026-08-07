# RQ2: Matcha clone search results by GitHub project popularity

Source: `analysis/so-gh_clones/`, aggregated by `analysis/aggregate_so_gh_clones.py` (written for this step, reusable).
Run with `.venv/bin/python3 analysis/aggregate_so_gh_clones.py --json out.json`. The statistical tests need `scipy`, which has been installed into `.venv`.

---

## 1. Data layout and how it was interpreted

Per language: three repository lists and one result CSV per project.

| File | Group | Projects |
|---|---|---|
| `{lang}_repos_stars10-25_forks0-14.txt` | low | 33 |
| `{lang}_repos_stars26-271_forks15-105.txt` | medium | 33 |
| `{lang}_repos_stars272plus_forks106plus.txt` | high | 34 |

These thresholds are exactly the Java quartile boundaries from the paper (stars Q1 [10, 25] and Q4 272+, forks Q1 [0, 14] and Q4 106+), so the grouping criterion is inherited unchanged. See threat (b) in `notes-paper.md`.

Result files are `search_results_python_new/{repo}_{timestamp}.csv` and `search_results_js/{repo}_{timestamp}.csv`, 100 of each. Every repository in the lists has exactly one result file and there are no name collisions, so the file-to-group mapping is unambiguous.

Each result line is headerless and comma separated:

```
/path/to/repo/file.py_<method>#<start>#<end>,<PostId>/<PostId>_<LocalId>_<rev>.py_<method>#<start>#<end>,...
```

Field 0 is the GitHub method that was used as the query. The remaining fields are the matched Stack Overflow snippets, where `<rev>` is a `PostHistoryId` or the literal `original` or `recent`. Because the Matcha index holds *every* revision of every code block, a single project method usually matches many revisions of the same block, so the revisions are folded together and the block `(PostId, LocalId)` is the unit of counting.

### Counting decisions, and why

The plan asks for "the number of Stack Overflow answer edits per group". Three quantities are reported, because they answer slightly different questions and the paper's own figures mix them:

- **Candidate pairs** = result lines with at least one match. This is the closest analogue of the paper's 793 "pairs of code snippets in GitHub projects that included the latest code answers".
- **Blocks matched** = distinct `(PostId, LocalId)` code blocks matched anywhere in the group.
- **Answer edits** = blocks matched whose content actually changed between the original and the latest revision, verified against `levenshtein_distances_{python,javascript}.csv` (distance > 0). **This is the headline number.** A matched block with distance 0 was never edited, so it carries no improvement to recommend, and counting it would overstate the supply. Recall from RQ1 that roughly 68% of all blocks have distance 0, so this filter is doing real work.

A small number of matched blocks (48 Python, 44 JavaScript) have no entry in the distance CSV and are excluded from the edit counts rather than guessed at.

**Note on de-duplication.** The group totals are set unions, so a block matched in three projects of the same group counts once. The per-project maxima and averages, and hence the statistical tests, use per-project counts, where that block counts once per project. This is why the Python high-popularity group shows 977 distinct edits but a per-project sum of 1,254. The paper's Table 7 reports totals and per-project max/avg side by side in the same way.

---

## 2. Results

### Python

| Group | Projects | Projects with matches | Candidate pairs | Blocks matched | **Answer edits** | Max per project | Avg per project |
|---|---|---|---|---|---|---|---|
| Low-popularity | 33 | 7 | 31 | 149 | **80** | 54 | 2.4242 |
| Medium-popularity | 33 | 16 | 111 | 304 | **156** | 64 | 5.6364 |
| High-popularity | 34 | 21 | 612 | 1,767 | **977** | 777 | 36.8824 |
| Total | 100 | 44 | 754 | 1,970 | **1,080** | | |

### JavaScript

| Group | Projects | Projects with matches | Candidate pairs | Blocks matched | **Answer edits** | Max per project | Avg per project |
|---|---|---|---|---|---|---|---|
| Low-popularity | 33 | 10 | 70 | 87 | **32** | 16 | 1.0303 |
| Medium-popularity | 33 | 10 | 62 | 164 | **71** | 28 | 2.1818 |
| High-popularity | 34 | 16 | 414 | 749 | **353** | 121 | 11.7941 |
| Total | 100 | 36 | 546 | 970 | **449** | | |

Totals are de-duplicated across groups, so they are smaller than the column sums.

### Java, for comparison (paper, Table 7)

| Group | Projects | Fixing Bug | Improving Code | Combined applicable |
|---|---|---|---|---|
| Low-popularity | 2,103 | 5 | 39 | 44 |
| Medium-popularity | 5,073 | 15 | 122 | 137 |
| High-popularity | 3,497 | 37 | 173 | 210 |
| Total | 10,673 | 57 | 334 | 391 (of 793 candidates) |

---

## 3. Statistical testing, following the paper's procedure

H0: there is no statistically significant difference in the number of matched Stack Overflow answer edits across the three project groups.

Shapiro-Wilk rejects normality in every group of both languages (all p < 1e-8), as it did for Java, so the non-parametric Kruskal-Wallis test is used on the per-project edit counts.

| Language | Kruskal-Wallis H | p | df | Decision at alpha = 0.05 |
|---|---|---|---|---|
| **Python** | 12.599128 | **0.001837** | 2 | **Reject H0**, significant difference |
| **JavaScript** | 3.051303 | 0.217479 | 2 | Retain H0, not significant |
| Java, Fixing Bug (paper) | 6.505224 | 0.038673 | 2 | Reject H0 |
| Java, Improving Code (paper) | 22.100237 | 0.000016 | 2 | Reject H0 |

Shapiro-Wilk detail:

| Language | Group | n | W | p |
|---|---|---|---|---|
| Python | low | 33 | 0.2735 | 1.208e-11 |
| Python | medium | 33 | 0.5076 | 2.187e-09 |
| Python | high | 34 | 0.2812 | 9.378e-12 |
| JavaScript | low | 33 | 0.3958 | 1.536e-10 |
| JavaScript | medium | 33 | 0.4161 | 2.425e-10 |
| JavaScript | high | 34 | 0.4705 | 6.056e-10 |

Exploratory pairwise Mann-Whitney U tests, uncorrected, reported for context only and not to be presented as confirmatory:

| Language | Comparison | U | p |
|---|---|---|---|
| Python | low vs medium | 417.5 | 0.049542 |
| Python | low vs high | 308.0 | 0.000404 |
| Python | medium vs high | 438.5 | 0.104750 |
| JavaScript | low vs medium | 543.5 | 0.993342 |
| JavaScript | low vs high | 461.0 | 0.134922 |
| JavaScript | medium vs high | 466.5 | 0.151670 |

---

## 4. What to claim, and what not to

**Replicated:** the paper's central RQ2 observation, that matched Stack Overflow answer edits increase from low- to medium- to high-popularity projects, holds in both languages and is monotonic on every measure, candidate pairs, blocks matched, answer edits, projects with matches, and per-project average. Python's per-project average rises 2.42 -> 5.64 -> 36.88 and JavaScript's 1.03 -> 2.18 -> 11.79. The high-popularity group also contains the projects with by far the largest single-project counts (777 for Python, 121 for JavaScript).

**Replicated with statistical support in Python only.** Kruskal-Wallis is significant for Python (p = 0.0018) as it was for Java in both categories, but **not** for JavaScript (p = 0.2175). The honest statement is that the trend is present in both languages but only reaches significance in Python. Do not describe the JavaScript trend as significant, and do not bury the negative result.

Most plausible explanation, to be offered in the Discussion without overclaiming: sample size and the extreme skew of the per-project counts. Each group holds only 33 or 34 projects, against the paper's 2,103 to 5,073, and the median project in five of the six groups matched zero edits, so the tests have very little power. The JavaScript counts are also roughly a third of the Python ones at every group. This is a limitation of the replication's scale, not evidence against the original finding.

**Do not** compare our edit counts against the Java study's 391 applicable recommendations. Ours are unvalidated candidate matches, so the comparable Java quantity is the 793 candidate pairs. There is no applicability rate in this replication because there is no manual classification.

---

## 5. Scale caveat, important for Methodology and Threats to Validity

The replication searched **100 projects per language**, 33 low, 33 medium, 34 high, against the Java study's **10,673**. The three groups are balanced by design here, whereas the Java groups were 2,103 / 5,073 / 3,497.

Consequences to state plainly in the report:

1. Absolute counts are not comparable with the Java study's. Only the within-study distribution across groups is.
2. Statistical power is low, which is the most likely reason the JavaScript test fails to reach significance.
3. The balanced design is arguably a fairer test of the popularity effect than the Java study's unbalanced one, since group size cannot drive the totals. Worth one sentence, since it partially offsets the scale limitation.
4. Add this to Threats to Validity as an external validity threat, alongside the three already recorded in `notes-paper.md` section 8 point 4.

---

## 6. Figures and tables to produce in step 7

- A grouped bar chart per language, answer edits by popularity group, the counterpart of the paper's Fig 10. Consider a single chart with two languages side by side, or a two-panel figure.
- One combined table in the style of Table 7, with a Python block and a JavaScript block, columns: group, projects, candidate pairs, answer edits, max per project, avg per project.
- A small table for the Kruskal-Wallis results across the two languages plus the two Java rows from the paper.

Note that the per-project counts are extremely skewed, median 0 in five of six groups, so a boxplot of per-project counts would be unreadable without a log axis. The bar chart of totals is the better choice, matching the paper.
