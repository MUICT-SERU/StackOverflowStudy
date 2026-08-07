# Replicating the results in the technical report

This directory holds the technical report *Do Stack Overflow Answer Edits Improve Code
Beyond Java? A Replication on Python and JavaScript*, and this file explains how to
reproduce every number in it.

The report replicates the Java study of Wiratsin et al. (arXiv:2511.05813) on Python and
JavaScript. The revised manuscript of that study is `paper.pdf`, and all Java figures
quoted in the report are taken from it rather than recomputed.

## Contents

| File | What it is |
|---|---|
| `report.tex`, `references.bib` | The report source |
| `report.pdf` | The built report |
| `Makefile` | Build targets |
| `make_figures.py` | Regenerates the figures from the analysis data |
| `figures/` | Generated figures |
| `paper.pdf` | The revised Java manuscript being replicated |
| `plan.md` | The working plan used to produce the report |
| `notes-paper.md` | Notes on the Java manuscript, including all its figures |
| `notes-results-python.md`, `notes-results-javascript.md` | RQ1 results per language |
| `notes-rq2-clones.md` | RQ2 clone-search results |

The notes files are the authority for every number in the report. If a figure in the
report and a figure in a notes file ever disagree, the notes file was written from the
tool output and should be trusted.

## Prerequisites

1. **A local SOTorrent database.** MySQL with the SOTorrent 2020-12-31 release loaded into
   a schema named `sotorrent`, reachable at `127.0.0.1` as user `root` with an empty
   password. Change the connection settings in the configuration cell of each notebook if
   yours differ. On macOS with Homebrew, start it for one session with
   `brew services run mysql` and stop it afterwards with `brew services stop mysql`.
2. **The Python environment.** A virtualenv at the repository root:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install mysql-connector-python matplotlib python-Levenshtein scipy
   ```

3. **LaTeX**, with the `IEEEtran` class, for building the report. TeX Live 2025 has it.

Only stages 1 to 3 below need the database. Stages 4 onwards run from the CSVs already in
the repository, so the report can be rebuilt without MySQL.

## Pipeline

Run from the repository root unless stated otherwise. Approximate runtimes are for a
local SSD-backed MySQL instance.

### 1. Select the accepted, revised answers (needs the database, ~10 min per language)

```bash
.venv/bin/python3 analysis/extract_answer_list.py --tag python \
    --output files/acceptedWithVersionAnswer_python.txt
.venv/bin/python3 analysis/extract_answer_list.py --tag javascript \
    --output files/acceptedWithVersionAnswer_javascript.txt
```

An answer is selected when it is accepted, its parent question carries the tag, and it has
at least one `PostVersion` row with a non-null `PredPostHistoryId`, that is it was edited
at least once. This is the same predicate the Java study used.

> **Important.** Do **not** pass `--require-code-block`. The Python list shipped in this
> repository was built with that flag, which is why it holds 305,768 ids while the
> unrestricted query returns 346,535. The report quotes 41.25% (the unrestricted figure)
> as the RQ1 headline for Python, because that is the quantity the Java study reports, and
> 36.40% as the code-bearing subset. The JavaScript list is unrestricted and needs no such
> caveat. See `notes-results-python.md` section 5.

### 2. Extract the code block revisions (needs the database, ~8 to 11 min per language)

Open `analysis/python_revision_extraction.ipynb` and
`analysis/javascript_revision_extraction.ipynb`, set `RUN_FULL_EXTRACTION = True`, and run
all cells. Each writes one directory per answer to `../python_files/` and
`../javascript_files/`, one level above the repository root, containing one file per code
block revision plus `_original` and `_recent` files per `(PostId, LocalId)` pair.

The extraction is resumable: an answer whose output directory already exists is skipped.

Expect roughly 2.9 million files for Python and 3.6 million for JavaScript.

### 3. RQ1 statistics and edit distances (needs the database, ~20 min per language)

Open `analysis/python_rq1_stats.ipynb` and `analysis/javascript_rq1_stats.ipynb` and run
all cells. Set `RUN_DISTANCE_COMPUTATION = True` in the Levenshtein cell to rebuild the
distance CSVs; leave it `False` to reuse the ones in the repository, which is much faster.

These notebooks produce the accepted-answer totals, the code snippet counts, the revision
counts and the headline Levenshtein figures, and they write
`analysis/levenshtein_distances_{python,javascript}.csv` and the revision histograms.

The notebooks select the filtered answer set **from the database**, using the same
predicate as `extract_answer_list.py`, rather than reading the id file. They cross-check
the id file against the query result and print a warning listing the set differences if
the two disagree. Running the Python notebook against the shipped list will therefore
report 346,535 answers and warn that the file holds 305,768; that warning is expected and
is the discrepancy described in stage 1.

`analysis/python_rq1_stats.py` is a command-line equivalent of the Python notebook:

```bash
.venv/bin/python3 analysis/python_rq1_stats.py --tag python
```

### 4. Edit-size distribution (no database, ~1 min)

```bash
python3 analysis/levenshtein_stats.py --json levenshtein_stats.json
```

Derives the parts of the distribution that the notebooks do not: the proportion of code
blocks that are byte-identical between their original and latest revisions, the
distribution restricted to blocks that did change, selected quantiles, and the per-answer
aggregates. Uses only the standard library, so the system Python is fine.

### 5. RQ2, the clone search results (no database, ~1 min)

The Matcha search itself was run separately and its output is committed under
`analysis/so-gh_clones/`, as one CSV per project plus the three project lists per
language. Re-running it requires Matcha (<https://github.com/cragkhit/Matcha>) and local
clones of the 200 projects; the tuned configuration is the one from the Java study, given
in Section II-D of the report.

To aggregate the committed results:

```bash
.venv/bin/python3 analysis/aggregate_so_gh_clones.py --json technical-report/rq2_summary.json
```

This maps each project to its popularity group, counts candidate pairs, matched blocks and
matched answer edits per group, computes the per-project maxima and averages, and runs the
Shapiro-Wilk and Kruskal-Wallis tests. `scipy` is needed for the tests; without it the
counts are still produced and the tests are skipped.

### 6. Figures (no database, ~1 min)

```bash
.venv/bin/python3 technical-report/make_figures.py
```

Writes the Levenshtein boxplots and the RQ2 bar chart into `technical-report/figures/`,
invoking the stage 5 aggregation for the latter. The two revision histograms are copied
from `analysis/` rather than regenerated, because the per-answer revision counts exist only
in the database.

### 7. Build the report

```bash
cd technical-report && make
```

Runs `pdflatex`, `bibtex`, then `pdflatex` twice more. `make figures` reruns stage 6 and
`make clean` removes the build artefacts. A clean build produces a 12-page PDF with no
undefined references and no bibtex warnings.

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
| Figures 1 and 2 | Revision histograms | Stage 3, copied by stage 6 |
| Figures 3 and 4 | Boxplots, RQ2 bar chart | Stage 6 |
| All Java figures | Everything in the Java column | `paper.pdf`, not recomputed |

## Reproducibility caveats

These are stated in the report's threats to validity and repeated here because they affect
what a re-run will show.

- **The Matcha configuration is the one tuned for Java** in the original study, against a
  2013 Java ground truth. No language-specific retuning was done, so the match counts are
  comparable across the three languages but are not optimal for Python or JavaScript.
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
