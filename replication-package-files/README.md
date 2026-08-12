# Replication Package — Do Stack Overflow Answer Edits Occur Beyond Java? A Replication on Python and JavaScript

Chaiyong Ragkhitwetsagul, In-on Wiratsin, Matheus Paixao, Denis De Sousa,
Pongpop Lapvikai, Peter Haddawy

Faculty of Information and Communication Technology, Mahidol University, Thailand ·
State University of Ceara (UECE), Brazil

DOI: [10.5281/zenodo.21900949](https://doi.org/10.5281/zenodo.21900949)

---

This package contains the data, code and intermediate results behind a replication of the
Java study of Wiratsin et al. (arXiv:[2511.05813](https://arxiv.org/abs/2511.05813)) on
Python and JavaScript.

The study asks two questions:

- **RQ1** — How often are accepted Stack Overflow answers edited, and how large are the
  edits to their code snippets?
- **RQ2** — Do the resulting code recommendations concentrate in popular GitHub projects?

Headline results, over 840,132 accepted Python answers and 1,144,185 accepted JavaScript
answers from the SOTorrent 2020-12-31 release: 41.25% and 39.10% respectively have been
edited at least once, against 16.11% for Java, while the mean number of revisions per
edited answer is near-identical across the three languages (2.78, 2.68, 2.82). Searching
100 GitHub projects per language, matched answer edits rise monotonically from low- to
medium- to high-popularity projects — 80 / 156 / 977 for Python and 32 / 71 / 353 for
JavaScript — significantly so for Python, not for JavaScript.

The technical report describing the study is distributed separately and is not included
here; this package holds the material needed to reproduce its results.

## What is in the package

```
README.md                     This file
CITATION.cff                  Citation metadata
LICENSE                       MIT, applies to the code
requirements.txt              Python dependencies
MANIFEST.sha256               SHA-256 of every file in the package

analysis/                     Analysis code and data
  extract_answer_list.py        Stage 1: select accepted, revised answers from SOTorrent
  python_revision_extraction.ipynb    Stage 2: extract code-block revisions to files
  javascript_revision_extraction.ipynb
  python_rq1_stats.ipynb        Stage 3: RQ1 statistics and Levenshtein distances
  javascript_rq1_stats.ipynb
  python_rq1_stats.py           Command-line equivalent of the Python RQ1 notebook
  levenshtein_stats.py          Stage 4: edit-size distribution, no database needed
  aggregate_so_gh_clones.py     Stage 5: RQ2 aggregation and statistical tests
  levenshtein_distances_python.csv       637,923 original/latest code-block pairs
  levenshtein_distances_javascript.csv   793,362 pairs
  python_post_revisions_histogram.pdf    Revision-count histograms written by stage 3
  javascript_post_revisions_histogram.pdf
  so-gh_clones/                 RQ2 clone-search output
    {python,javascript}_repos_stars*.txt      the 100 searched projects per language,
                                              split into the three popularity groups
    search_results_python_new/    one CSV of matched clone pairs per Python project
    search_results_js/            one CSV per JavaScript project

files/                        Answer id lists produced by stage 1
  acceptedWithVersionAnswer_python.txt        305,768 ids (see the caveat below)
  acceptedWithVersionAnswer_javascript.txt    447,379 ids, unrestricted

results/                      Derived results, regenerated when this package was built
  levenshtein_stats.{json,txt}  Stage 4 output
  rq2_summary.{json,txt}        Stage 5 output
```

## Reproducing the results

The directory layout matters — the scripts resolve their inputs relative to their own
location, so run them from within the unpacked package without moving files.

Stages 1 to 3 need a local SOTorrent database. **Stages 4 and 5 run from the CSVs shipped
here, so every number in the report can be reproduced without MySQL.**

### Prerequisites

For stages 4 and 5 only:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

For stages 1 to 3 additionally: MySQL with the SOTorrent 2020-12-31 release loaded into a
schema named `sotorrent`, reachable at `127.0.0.1` as user `root` with an empty password.
Change the connection settings in the configuration cell of each notebook if yours differ.
SOTorrent is available at <https://empirical-software.engineering/projects/sotorrent/>.

### 1. Select the accepted, revised answers (database, ~10 min per language)

```bash
.venv/bin/python3 analysis/extract_answer_list.py --tag python \
    --output files/acceptedWithVersionAnswer_python.txt
.venv/bin/python3 analysis/extract_answer_list.py --tag javascript \
    --output files/acceptedWithVersionAnswer_javascript.txt
```

An answer is selected when it is accepted, its parent question carries the tag, and it has
at least one `PostVersion` row with a non-null `PredPostHistoryId` — that is, it was edited
at least once. This is the predicate the Java study used.

> **Caveat.** Do **not** pass `--require-code-block`. The Python list shipped here was
> built with that flag, which is why it holds 305,768 ids while the unrestricted query
> returns 346,535. The report quotes 41.25% (unrestricted) as the RQ1 headline for Python,
> because that is the quantity the Java study reports, and 36.40% as the code-bearing
> subset. The JavaScript list is unrestricted and needs no such caveat.

### 2. Extract the code block revisions (database, ~8-11 min per language)

Open `analysis/python_revision_extraction.ipynb` and
`analysis/javascript_revision_extraction.ipynb`, set `RUN_FULL_EXTRACTION = True`, and run
all cells. Each writes one directory per answer to `../python_files/` and
`../javascript_files/`, one level above the package root, containing one file per code
block revision plus `_original` and `_recent` files per `(PostId, LocalId)` pair.

Extraction is resumable: an answer whose output directory already exists is skipped.
Expect roughly 2.9 million files for Python and 3.6 million for JavaScript. These extracted
files are not shipped here — they are ~10 GB per language and are fully derivable from
SOTorrent.

### 3. RQ1 statistics and edit distances (database, ~20 min per language)

Open `analysis/python_rq1_stats.ipynb` and `analysis/javascript_rq1_stats.ipynb` and run
all cells. Set `RUN_DISTANCE_COMPUTATION = True` in the Levenshtein cell to rebuild the
distance CSVs; leave it `False` to reuse the ones shipped here, which is much faster.

These notebooks produce the accepted-answer totals, code snippet counts, revision counts
and headline Levenshtein figures, and they write
`analysis/levenshtein_distances_{python,javascript}.csv` and the revision histograms.

The notebooks select the filtered answer set **from the database** rather than reading the
id file, and cross-check the id file against the query result. Running the Python notebook
against the shipped list will therefore report 346,535 answers and warn that the file holds
305,768. That warning is expected, and is the discrepancy described in stage 1.

`analysis/python_rq1_stats.py` is a command-line equivalent of the Python notebook:

```bash
.venv/bin/python3 analysis/python_rq1_stats.py --tag python
```

### 4. Edit-size distribution (no database, ~1 min)

```bash
.venv/bin/python3 analysis/levenshtein_stats.py --json results/levenshtein_stats.json
```

Derives the parts of the distribution the notebooks do not: the proportion of code blocks
byte-identical between their original and latest revisions, the distribution restricted to
blocks that did change, selected quantiles, and the per-answer aggregates. Uses only the
standard library.

### 5. RQ2, the clone search results (no database, ~1 min)

The clone search itself was run separately with Siamese+/Matcha; its output is included
under `analysis/so-gh_clones/` as one CSV per project plus the three project lists per
language. Re-running the search requires Matcha
(<https://github.com/cragkhit/Matcha>) and local clones of the 200 projects; the tuned
configuration is the one from the Java study, given in Section II-D of the report.

To aggregate the included results:

```bash
.venv/bin/python3 analysis/aggregate_so_gh_clones.py --json results/rq2_summary.json
```

This maps each project to its popularity group, counts candidate pairs, matched blocks and
matched answer edits per group, computes per-project maxima and averages, and runs the
Shapiro-Wilk and Kruskal-Wallis tests. `scipy` is needed for the tests; without it the
counts are still produced and the tests skipped.

## Where each number in the report comes from

| Report location | Numbers | Produced by |
|---|---|---|
| Table III, rows 1 to 9 | Accepted answers, snippets, revision counts, maxima | Stage 3 notebooks |
| Table III, Levenshtein rows | Mean, median, maximum, standard deviation | Stage 3 notebooks |
| Table III, unchanged code blocks | 68.68%, 67.70% | Stage 4 |
| Section III-A, III-B, quantiles and changed-only figures | p75, p90, p95, p99, changed-only mean and median | Stage 4 |
| Section III-A, III-B, per-answer aggregates | Answers with pairs, blocks per answer, answers with a changed block | Stage 4 |
| Tables I and II | All RQ2 counts, maxima and averages | Stage 5 |
| Section III-A, III-B, Kruskal-Wallis and Shapiro-Wilk | H, p, W | Stage 5 |
| Figures 1 and 2 | Revision histograms | Stage 3 |
| Figures 3 and 4 | Boxplots, RQ2 bar chart | Plotted from the stage 4 and 5 data |
| All Java figures | Everything in the Java column | The original manuscript, not recomputed |

## Data formats

`analysis/levenshtein_distances_{lang}.csv` — one row per code block, header
`First File,Second File,Levenshtein Distance`. The two path columns name the original and
latest revision of the same `(PostId, LocalId)` code block, as written by stage 2; the
answer id is the parent directory name and the `LocalId` is the middle field of the
filename. The third column is the character-level Levenshtein distance, `0` when the block
was never textually changed.

`analysis/so-gh_clones/search_results_*/{repo}_{timestamp}.csv` — one file per searched
GitHub project, holding the candidate clone pairs the search returned between that project
and the indexed Stack Overflow code-block revisions.

`files/acceptedWithVersionAnswer_{lang}.txt` — one Stack Overflow answer id per line,
ascending.

## Reproducibility caveats

These are stated in the report's threats to validity and repeated here because they affect
what a re-run will show.

- **The clone-search configuration is the one tuned for Java** in the original study,
  against a 2013 Java ground truth. No language-specific retuning was done, so match counts
  are comparable across the three languages but are not optimal for Python or JavaScript.
- **The popularity thresholds are inherited from the Java project population** rather than
  recomputed as quartiles of the Python or JavaScript populations.
- **100 projects per language were searched**, against the Java study's 10,673. Absolute
  counts are therefore not comparable with the published Java figures; only the
  within-study distribution across groups is.
- **No manual classification was performed.** The RQ2 figures are candidate matches, so
  they correspond to the Java study's 793 candidate pairs, not to its 391 manually
  validated applicable recommendations.
- **The SOTorrent release is 2020-12-31**, so the data predate the widespread adoption of
  generative AI coding assistants.
- **The Python answer id list was built with `--require-code-block`**, as described in
  stage 1.

## Licence

Code in this package is released under the MIT licence (`LICENSE`).

The derived data files are released under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), following the licence of
the Stack Overflow content they are derived from via SOTorrent. Stack Overflow content is
contributed by its users under CC BY-SA; SOTorrent itself is distributed under CC BY-SA 4.0.

## Citing

To cite this package:

> Chaiyong Ragkhitwetsagul, In-on Wiratsin, Matheus Paixao, Denis De Sousa, Pongpop
> Lapvikai, and Peter Haddawy. *Replication package: Do Stack Overflow Answer Edits Occur
> Beyond Java? A Replication on Python and JavaScript.* Zenodo, 2026.
> doi:[10.5281/zenodo.21900949](https://doi.org/10.5281/zenodo.21900949)

Machine-readable metadata is in `CITATION.cff`. The study being replicated is:

> In-on Wiratsin, Chaiyong Ragkhitwetsagul, Matheus Paixao, Denis De Sousa, Pongpop
> Lapvikai, and Peter Haddawy. *An Empirical Study of Java Code Improvements Based on Stack
> Overflow Answer Edits.* arXiv:2511.05813, 2025.

The underlying dataset is:

> Sebastian Baltes, Lorik Dumani, Christoph Treude, and Stephan Diehl. *SOTorrent:
> Reconstructing and Analyzing the Evolution of Stack Overflow Posts.* MSR 2018, 319-330.
> doi:10.1145/3196398.3196430
