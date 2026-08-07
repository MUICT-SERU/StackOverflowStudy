# Technical Report: Replication Study of "An Empirical Study of Java Code Improvements Based on Stack Overflow Answer Edits" on Python and JavaScript.

## Aim
To show that the findings from the paper "An Empirical Study of Java Code Improvements Based on Stack Overflow Answer Edits" (https://arxiv.org/abs/2511.05813) is generalized to other languages.

## What Have Been Done
1. There are two studies that follow the same methodology as the arXiv paper but analyze the Python accepted answers and JavaScript accepted answers on Stack Overflow.
2. The GitHub projects are collected based on the popularity criteria from the Java projects as indicated in the arXiv paper.
3. The results should support the findings in RQ1 and RQ2 of the paper.

## What To Do
1. Write a technical report using LaTeX IEEE technical report format (see https://www.ieee.org/conferences/publishing/templates) based on the results in the analysis folder. Specifically, look at the the Jupyter notebooks (python_*.ipynb, and javascript_*.ipynb). Discuss the findings in the same style as the arXiv paper.
2. Write the findings from the clone search results using Matcha (i.e., Siamese+) as can be found in the `so-gh_clones` folders in the same way as RQ2. However, we will not do the manual classification. So, only show the number of Stack Overflow answer edits based on each group of GitHub projects (low-, medium-, and high-popularity).

## Structure of the Report
1. Abstract
2. Introduction -- Explain why we need to do this replication study. You can refer to the arXiv paper. Motivate that Python and JavaScript are among the most popular programming languages besides Java.
3. Methodology -- Explain the methodology in general, then separate some specific details for each language.
4. Results -- Separate the results in two sections: Python and JavaScript.
5. Discussion -- Compare and contrast the findings with the arXiv paper.
6. Threats to Validity.
7. Conclusion

## Caveats
1. Use British English when writing.
2. Do not use emdahses, use commas instead.

## Claude's Planning

Each step below is self-contained. Tell me a number and I will do that step only.

### Phase A: Gather the source material

1. **Read the revised paper, `technical-report/paper.pdf`. DONE** This is the current revision of the arXiv paper (2511.05813) and supersedes the arXiv version, so all numbers and findings come from here. It is 44 pages, so read it in page ranges. Take notes on its structure, the exact wording of RQ1 and RQ2, the metrics reported (number of posts, revisions, Levenshtein distance statistics, the popularity grouping thresholds), the tables and figures used, and the phrasing style of the findings. Save the notes to `technical-report/notes-paper.md` so later steps do not need to reread the PDF. This step defines the template that everything else has to match. Note for later steps: the technical report still cites the arXiv version (2511.05813), since the revision will be uploaded there in due course.

2. **Extract the Python results. DONE** Run through `analysis/python_revision_extraction.ipynb` and `analysis/python_rq1_stats.ipynb` (plus `analysis/python_rq1_stats.py` and `analysis/levenshtein_distances_python.csv`) and pull out every number the report needs: total accepted answers, answers with code, number of revisions, edit categories, Levenshtein distance descriptive statistics, and any statistical tests. Record them in `technical-report/notes-results-python.md`.

3. **Extract the JavaScript results. DONE** The same as step 2 but for `analysis/javascript_revision_extraction.ipynb`, `analysis/javascript_rq1_stats.ipynb` and `analysis/levenshtein_distances_javascript.csv`. Record them in `technical-report/notes-results-javascript.md`.

4. **Extract the Java baseline numbers. DONE** Take the Java figures solely from `technical-report/paper.pdf`, since that revision is authoritative. Do not use `analysis/java_rq1_stats.ipynb` or `analysis/levenshtein_distances.csv`, which may predate the revision. Recorded in `technical-report/notes-paper.md` as part of step 1, so this step is already complete.

5. **Aggregate the Matcha clone search results (RQ2). DONE** Work out the schema of the CSVs in `analysis/so-gh_clones/search_results_python_new/` and `analysis/so-gh_clones/search_results_js/`, map each repository to its popularity group using the four `*_repos_stars*.txt` lists (low: 10 to 25 stars, medium: 26 to 271, high: 272 and above), then count the distinct Stack Overflow answer edits matched per group per language. Write a small reusable script to `analysis/aggregate_so_gh_clones.py` and save the resulting counts to `technical-report/notes-rq2-clones.md`. No manual classification, counts only.

### Phase B: Build the report

6. **Set up the LaTeX skeleton. DONE** Create `technical-report/report.tex` using the IEEEtran conference class with one column format, with the bibliography file `technical-report/references.bib`, a `figures/` folder, and empty sections matching the agreed structure. Confirm it compiles with `pdflatex` and `bibtex`, and add a `Makefile` or short build note. Nothing but placeholder text at this stage.

7. **Produce the tables and figures. DONE** Generate the LaTeX tables for the descriptive statistics of both languages and the RQ2 popularity group counts, and copy or regenerate the boxplots (`python_levenshtein_boxplot*.pdf`, `javascript_levenshtein_boxplot*.pdf`, `java_levenshtein_boxplot.pdf`) and histograms into `technical-report/figures/`. Aim for a side by side Java, Python, JavaScript presentation wherever the paper reports a single Java number.

8. **Write Methodology. DONE** The shared pipeline first (SOTorrent based revision extraction, filtering of accepted answers with code blocks, Levenshtein distance computation, GitHub project selection criteria, Matcha/Siamese+ clone search configuration), then a short subsection per language covering the parser, the tags used, and any language specific deviation.

9. **Write Results, Python. DONE** RQ1 then RQ2 for Python, using the numbers from steps 2 and 5, phrased in the same style as the arXiv paper, with explicit finding boxes if the paper uses them.

10. **Write Results, JavaScript. DONE** The same as step 9 for JavaScript, using steps 3 and 5.

11. **Write Discussion. DONE** Compare and contrast Python and JavaScript against the Java results, state clearly which of the original findings replicate, which hold only partially, and which do not, and offer explanations grounded in language characteristics rather than speculation.

12. **Write Threats to Validity. DONE** Internal, external and construct validity, including the reliance on SOTorrent snapshots, the clone detector's false positive rate, and, as set out in section 8 point 4 of `notes-paper.md`, three threats specific to this replication: (a) Matcha was run on Python and JavaScript with the configuration tuned for Java in Phase 1 of the original study, against a 2013 Java ground truth, with no language-specific retuning, (b) the popularity thresholds were inherited from the Java project population rather than recomputed per language, and (c) there is no manual classification, so the RQ2 figures are candidate matches rather than validated applicable improvements.

13. **Write Introduction and Conclusion. DONE** Motivate the replication with the popularity of Python and JavaScript relative to Java, state the contributions, then close with the conclusions and possible future work. Written after the body so the claims match what was actually found.

14. **Write the Abstract. DONE** Written last so it reflects the finished report.

### Phase C: Finish

15. **Full pass and build.** Compile the final PDF, check that every table, figure and citation resolves, verify British English throughout, verify there are no em dashes, and check every number in the prose against the notes files from Phase A.
