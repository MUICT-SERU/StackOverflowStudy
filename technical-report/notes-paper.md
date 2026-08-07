# Notes on `paper.pdf` (revised version of arXiv:2511.05813)

Source: `technical-report/paper.pdf`, 44 pages, dated 7 August 2026.
Title: *An Empirical Study of Java Code Improvements Based on Stack Overflow Answer Edits*.
Authors: In-on Wiratsin, Chaiyong Ragkhitwetsagul (corresponding), Matheus Paixao, Denis De Sousa, Pongpop Lapvikai, Peter Haddawy.
Affiliations: Faculty of ICT, Mahidol University, Thailand, and State University of Ceara (UECE), Fortaleza, Brazil.

This revision supersedes the arXiv version. All numbers below come from this PDF. The technical report still cites the arXiv entry (2511.05813), since this revision will be uploaded there later.

Note on formatting: the PDF is typeset in a PLOS-style single-column journal template with numbered sections and line numbers, not IEEE two-column. The technical report will use the IEEE template, so the *style of argument* is what we mirror, not the physical layout.

---

## 1. Section structure of the paper

1. Introduction (1.1 Motivating Example, 1.2 Research Questions)
2. Related Work (2.1 Stack Overflow Answer Edits, 2.2 Generating Code Recommendations)
3. Methodology (3.1 Datasets, 3.2 Code Clone Search Tool, 3.3 Experimental Design with Phases 1 to 3)
4. Results (4.1 Study Setup, 4.2 RQ1, 4.3 RQ2, 4.4 RQ3, 4.5 Practical Application / Phase 3)
5. Discussion (5.1 implications for researchers, 5.2 for maintainers, 5.3 GenAI era, 5.4 limitations of leveraging SO answer revisions)
6. Threats to the Validity (construct, internal, conclusion, external)
7. Conclusion
8. Declarations (funding, ethics, consent, author contributions, data availability, conflict of interest)
References, then Appendices.

Our technical report structure (Abstract, Introduction, Methodology, Results split by language, Discussion, Threats to Validity, Conclusion) maps cleanly onto this, minus Related Work and minus Phase 3.

---

## 2. Research questions, exact wording

- **RQ1:** *To what extent are accepted Java answers on Stack Overflow edited?*
  Purpose: quantify prevalence of edits on SO Java accepted answers, extract the revision history to determine how many answers were edited after posting and how large those edits are. This establishes the supply of potential code improvements.

- **RQ2:** *What types of code improvements do Stack Overflow answer edits suggest for code found in open-source projects, and how are they distributed across projects of different popularity?*
  Purpose: use the supply from RQ1 to (1) understand the types of code improvements suggested and (2) determine how often they are applicable to open-source projects, classifying edits into categories and examining distribution across popularity groups.

- **RQ3:** *What are the differences in terms of code structure and readability introduced by Stack Overflow answer edits?*
  Objective static-analysis measurement (JavaParser, Checkstyle) complementing the manual classification in RQ2. **New in this revision.** Out of scope for our technical report.

Phase 3 (pull requests) is described as a practical validation of the pipeline, not a separately declared research question.

For our report: RQ1 replicates directly. RQ2 replicates only in its *distribution across popularity groups* half, since we do no manual classification. We should reword our RQ2 accordingly, for example "how are the Stack Overflow answer edits matched in open-source projects distributed across projects of different popularity?".

---

## 3. Methodology details to mirror

### 3.1 Datasets

- **SOTorrent** [ref 46, Baltes et al., MSR '18], local MySQL copy of the **2020-12-31** release. That release contains 51,296,931 SO posts with 81,536,422 post versions.
- Tags are attached to questions, not answers, so Java answers were identified through the parent question: join `Posts` to `PostTags` on the question and resolve the `java` tag to `Tags.Id`.
- An answer enters the set when it is both **accepted** (`Id` equals the parent question's `AcceptedAnswerId`) and **revised** (has at least one `PostVersion` row whose `PredPostHistoryId` is not null).
- Code blocks come from `PostBlockVersion` where `PostBlockTypeId = 2`.
- Answers with more than one code block are **not** merged or reduced to a single snippet. Each block is tracked separately by its `LocalId`, so an answer with two code blocks contributes two independent edit histories.
- For every `(PostId, LocalId)` pair, every revision is written out as its own file, plus two distinguished versions: **latest** (`MostRecentVersion = 1`) and **original** (the root of the block's edit chain given by `RootPostBlockVersionId`). The original is taken from the root of the chain rather than the answer's first revision, because an edit chain can break and restart when a block is removed and later re-added.

### 3.2 GitHub project collection

- Tool: **GHS (GitHub Search)** [ref 50, Dabic et al., MSR '21], 735,669 repositories in 10 languages, 25 characteristics per project usable as filters.
- Filters used: `Language: Java`, `Exclude Forks`, `Has Open Issues`, `Has Open Pull Requests`. Forks excluded to avoid redundancy, open issues and open PRs used as an aliveness proxy.
- Data collection performed in **March 2023**.
- Result: **20,976** GitHub Java projects before popularity filtering.

### 3.3 Popularity grouping, the criterion we must reuse

Three GHS metrics: **Number of Stars, Number of Watchers, Number of Forks**. Each metric's distribution is split into quartiles.

- **Low-popularity:** all three metric values in the first quartile.
- **High-popularity:** all three metric values in the fourth quartile.
- **Medium-popularity:** all three metric values between the first and third quartiles.
- Projects landing in different quartiles for different metrics are **excluded**.

Quartile boundaries reported for the Java set (Table 4 and Section 4.1.2):

| Metric | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| Stars | [10, 25] | (25, 70] | (70, 272] | (272, 145397] |
| Forks | [0, 14] | (14, 34] | (34, 106] | (106, 50497] |
| Watchers | [0, 6] | (6, 13] | (13, 31] | (31, 5442] |

Table 4 summary statistics: Stars mean 558.80, std 2,609.89, min 10, 25% 25, median 70, 75% 272, max 145,397. Forks mean 185.72, std 957.41, min 0, 25% 14, median 34, 75% 106, max 50,497. Watchers mean 38.93, std 126.28, min 0, 25% 6, median 13, 75% 31, max 5,442.

**This matches the filenames in `analysis/so-gh_clones/`**: `*_repos_stars10-25_forks0-14.txt` (low), `*_repos_stars26-271_forks15-105.txt` (medium), `*_repos_stars272plus_forks106plus.txt` (high). So the Python and JavaScript sets reuse the Java thresholds directly, which is what the plan assumed. Worth stating explicitly in the report's methodology and again in Threats to Validity, since language ecosystems have different star distributions.

### 3.4 Clone search tool

- Base tool: **Siamese** [ref 11, Ragkhitwetsagul and Krinke, EMSE 2019], scalable incremental clone search via multiple code representations, accurate for Type-1 to Type-3, scales to 365 million lines, results in about 8 seconds.
- Phase 1 tuned Siamese by **Grid Search** maximising **MRR**, using a ground truth of clone pairs between SO and the **Qualitas corpus** (111 Java projects, release 20130901r, 166,709 files, 19,614,083 lines) from ref 56. The 2,302 original pairs were reduced to **553** by keeping only the three reuse-relevant patterns (QS, EX, UD).
- Grid Search evaluated **3,073 configurations** in **54 hours**, average 63 seconds per configuration, over 72,365 Java code snippets. Best **MRR = 0.782**. Correct clone was ranked first in about 80% of queries, and Siamese never returned an empty result set.
- Optimised configuration (Table 3): clone size 6 lines; n-gram size 1 for representation r0 and 4 for r1, r2, r3; QR thresholds 9, 6, 5, 9; similarity thresholds 50%, 60%, 70%, 80%.
- **Siamese+** is Siamese augmented with three modules: (1) **boiler-plate code filter** (getters, setters, `equals()`, `compareTo()`, `toString()`, encoded as regular expressions from ref 55, applied as a query filter), (2) **multiple code revision search** (index containing every revision, snippets named `PostID_LocalID_HistoryID`, with the first and last marked `original` and `latest`, e.g. `8394534_0_original.java` and `8394534_0_latest.java`), (3) **latest code revision retrieval** (if the matched snippet is not the latest, Siamese+ returns the latest version as the recommendation). Output is CSV with file name, method name, start line, end line, and the `PostID`.
- Siamese+ is public at https://github.com/cragkhit/Matcha. **This is the tool our technical report calls Matcha.** Useful point: the report should note that Matcha is the same tool as Siamese+ in the paper, extended to Python and JavaScript.

### 3.5 Manual classification (RQ2, Java only, we skip this)

- Code book in Fig 4: clones? -> meaningful revision (not formatting-only)? -> applicable to GitHub code? -> improvement if applied? -> classify into Fixing Bug or Improving Code plus a subcategory.
- Applicability criteria (three, all must hold): (i) GitHub code and SO code implement the same functionality, (ii) same or compatible APIs or libraries, (iii) improvement applicable without changing the intended behaviour of the original code.
- Base categorisation adopted from Baltes et al. [ref 38] (Table 2: actions performed, target of the edit, meta-level), then extended by open coding.
- Two independent validators (first and fifth authors), Cohen's kappa **0.8333**, disagreements resolved by a third researcher with more than 20 years of Java experience.

---

## 4. Key results

### 4.1 Study setup

- 20,976 projects from GHS, filtered to **10,673** projects containing **4,571,660 Java files**.
- Group sizes (Table 5): low 2,103 (avg 18,453.85 lines, std 154,149.35), medium 5,073 (avg 45,675.51, std 254,021.39), high 3,497 (avg 112,896.53, std 749,139.46). Medium is the largest group, then high, then low. Code size grows with popularity.

### 4.2 RQ1 (Java)

- **2,832,800** Java answers on SO, of which **874,438 are accepted**.
- The accepted answers contain **917,389 Java code snippets**, an average of **1.05** snippets per accepted answer, std **1.22**.
- **140,840** accepted answers had at least one revision, i.e. **16.11%** of the 874,438 accepted answers.
- Average revisions per answer **2.82**, median **2.0**. Maximum **53** revisions (post 62805030, Apache Lang3 `StopWatch`, first revision 8 July 2020, last 24 January 2021, spanning 6 months 17 days).
- Total code snippets across all revisions of accepted answers: **283,838**. These were indexed in Siamese+.
- Levenshtein distance between original and latest code answer: min **0**, max **21,158**, mean **88.87**, std **359.44**. Largest-revision example post 24407816 (`JideScrollPane`).
- Narrative point: most edits are small, no more than 100 characters, with a long tail of large edits.

> **Answer to RQ1:** 16.11% of Stack Overflow Java accepted answers have more than one revision, with the average number of revisions per answer being 2.82. The average code edit size between the original and the latest SO revisions is 88.87 characters.

Figures: Fig 8 (histogram of revision counts, annotated with Total Answers 140,840 / Mean 2.82 / Median 2.0), Fig 9 (boxplot of Levenshtein distance). Our `python_levenshtein_boxplot.pdf` and `javascript_levenshtein_boxplot.pdf` are the counterparts of Fig 9, and `post_revisions_histogram.pdf` / `javascript_post_revisions_histogram.pdf` of Fig 8.

### 4.3 RQ2 (Java)

- Siamese+ run over 283,838 indexed revisions against 10,673 projects, execution time **16 days, 5 hours, 21 minutes**.
- **793** pairs of code snippets found in GitHub projects that included the latest code answers.
- Manual validation: 298 agreed applicable, 408 agreed non-applicable, 87 disagreements, kappa 0.8333. Final: **391 applicable**, **402 non-applicable**, i.e. **49.30%** applicable.
- Category split of the 391 (Table 6): **Fixing Bug 57**, **Improving Code 334**. Improving Code subcategories: Application/Framework-Specific 56, Code Clarity and Maintainability 57, Compatibility 7, Data and File Handling 52, Data Structures and Algorithms 14, Error Handling and Robustness 45, Functional Enhancement 21, Miscellaneous/Others 21, Resource and Process Management 14, Security and Cryptography 2, Usability 33, UI and Interaction 12.

**Table 7, the direct template for our RQ2 table** (Number of SO latest code answers grouped by GitHub project groups):

| Group | Fixing Bug Total | Max | Avg | Improving Code Total | Max | Avg |
|---|---|---|---|---|---|---|
| Low-popularity | 5 | 1 | 0.0024 | 39 | 10 | 0.0185 |
| Medium-popularity | 15 | 1 | 0.0030 | 122 | 9 | 0.0240 |
| High-popularity | 37 | 12 | 0.0106 | 173 | 9 | 0.0495 |

Max and Avg are per project. Fig 10 is the grouped bar chart of the Total columns.

Since we do no manual classification, our equivalent table has one count column per language rather than the Fixing Bug / Improving Code split, i.e. total SO answer edits matched per popularity group, plus max and average per project so the comparison with Table 7 stays meaningful. We should also report the number of projects per group as a denominator, since group sizes differ.

- Statistical testing: Shapiro-Wilk [ref 64] indicated non-normality, so **Kruskal-Wallis** [ref 65] was used.
  - Fixing Bug across the three groups: p = **0.038673**, H = **6.505224**, df = 2, alpha = 0.05, null rejected.
  - Improving Code across the three groups: p = **0.000016**, H = **22.100237**, df = 2, null rejected.
- Table 8 gives the 12 Improving Code subcategories as percentages within each group (N = 39 low, 122 medium, 173 high). Largest per group: low = Application/Framework-Specific 28.21%, medium = Code Clarity and Maintainability 21.31%, high = Error Handling and Robustness 19.08%.

> **Answer to RQ2:** 49.30% (391 out of the 793) of SO's latest code answers are considered applicable to the GitHub projects. The number of recommendations for both the Fixing Bugs and Improving Code categories is the highest in high-popularity GitHub projects.

Key claim we need to test for Python and JavaScript: **matched edits increase monotonically from low- to medium- to high-popularity projects**, and the difference is statistically significant by Kruskal-Wallis. We can run the same Shapiro-Wilk plus Kruskal-Wallis on our per-project counts even without manual classification.

### 4.4 RQ3 (Java, out of scope for us, summarised for the Discussion)

- 793 pairs reduce to **205 unique original-recent** SO pairs. Tools: JavaParser 3.28.1 (18 structural metrics plus non-comment code lines), Checkstyle 13.9.0 (8 readability and style checks).
- Parsing coverage (Table 9): JavaParser analysed 128 of 205, excluded 77, exclusion rate 37.6%. Checkstyle analysed 129, excluded 76, 37.1%.
- Paired Wilcoxon signed-rank with Holm correction across 19 metrics: **no metric significant after correction**. Code lines closest (raw p = 0.004, p_Holm = 0.070, increased in 63 pairs vs decreased in 34). Every rank-biserial correlation non-negative, i.e. revisions skew toward increasing structural counts.
- Checkstyle (n = 129): raw findings 25 improved / 84 unchanged / 20 worsened, r_rb = -0.141, p = 0.414. Density per 100 lines 39 improved / 68 unchanged / 22 worsened, r_rb = -0.228, p = 0.122. Neither significant.

> **Answer to RQ3:** The majority of the SO's latest code answers do not change the code structure or readability of the original code snippets. However, the revisions tend to add defensive and error-handling logic, which increases structural counts while slightly improving readability.

### 4.5 Phase 3, pull requests (out of scope, summarised)

Funnel (Table 12): 107 selected (57 Fixing Bug, 50 Improving Code), 27 excluded before submission, **80 submitted**, 57 pull requests opened (24 Fixing Bug, 33 Improving Code), 10 pull requests accepted, **17 recommendations accepted**. Acceptance rate **21.25%** of the 80 submitted (23.40% Fixing Bug, 18.18% Improving Code), 15.89% if measured against all 107 selected, 17.5% at the level of pull requests (10/57). 39 of 57 still pending review at time of writing, 5 closed without adoption.

---

## 5. Style conventions to reproduce

- **British English** throughout (analyse, categorise, optimise, behaviour, labelling).
- Em dashes are not used in the running text of this paper, commas and parentheses instead. Matches our caveat.
- Each RQ section closes with a boxed **"Answer to RQx:"** statement, one to three sentences, leading with the headline percentage. We should reproduce these boxes (`tcolorbox` or a framed `minipage` in IEEEtran).
- Numbers are given with thousands separators and two decimal places for means and standard deviations, four decimal places for the small per-project averages in Table 7, and six decimal places for p-values.
- Percentages are stated with the raw fraction in parentheses, e.g. "49.30% (391 out of the 793)".
- Every RQ answer is stated as a claim first, then the supporting distributional detail.
- Figures are referenced as "Fig 1", tables as "Table 1".
- Tools are named in small caps or bold on first mention (Siamese, Siamese+, JavaParser, Checkstyle).

---

## 6. References we will need in `references.bib`

Numbering below is the paper's.

- [11] Ragkhitwetsagul C, Krinke J. Siamese: scalable and incremental code clone search via multiple code representations. EMSE. 2019;24:2236-84.
- [38] Baltes S, Wagner M. An annotated dataset of stack overflow post edits. GECCO '20 Companion. 2020. p. 1923-5. (edit categories)
- [46] Baltes S, Dumani L, Treude C, Diehl S. SOTorrent: Reconstructing and Analyzing the Evolution of Stack Overflow Posts. MSR '18. 2018. p. 319-30.
- [50] Dabic O, Aghajani E, Bavota G. Sampling Projects in GitHub for MSR Studies. MSR '21. 2021. p. 560-4. (GHS)
- [51] Cass S. The Top Programming Languages 2024. IEEE Spectrum. https://spectrum.ieee.org/top-programming-languages-2024 (**use this for the Python and JavaScript popularity motivation in our Introduction**)
- [54] Ragkhitwetsagul C, Krinke J, Clark D. A comparison of code similarity analysers. EMSE. 2018;23(4):2464-519.
- [55] / [56] Ragkhitwetsagul C, Krinke J, Paixao M, Bianco G, Oliveto R. Toxic Code Snippets on Stack Overflow. TSE. 2021;47(3):560-81. (boilerplate patterns and the clone ground truth)
- [57] Tempero E, et al. The Qualitas corpus. APSEC 2010. p. 336-45.
- [58] Wang T, Harman M, Jia Y, Krinke J. Searching for better configurations. FSE '13. p. 455-65.
- [59] Ragkhitwetsagul C, et al. Searching for configurations in clone evaluation, a replication study. SSBSE '16. p. 250-6.
- [64] Shapiro SS, Wilk MB. An analysis of variance test for normality. Biometrika. 1965;52(3-4):591-611.
- [65] Kruskal WH, Wallis WA. Use of ranks in one-criterion variance analysis. JASA. 1952;47(260):583-621.
- [26] Tang H, Nadi S. On using Stack Overflow comment-edit pairs to recommend code maintenance changes. EMSE. 2021;26(4):68. (**applies to five languages including Python and JavaScript, directly relevant to our motivation**)
- [28] Mondal S, Roy CK. Does Editing Improve Answer Quality on Stack Overflow? ICSME '25. (**analyses 94,994 Python answers, the closest existing Python work, must be cited in our Introduction and Discussion**)
- [39] Zhang H, et al. A Study of C/C++ Code Weaknesses on Stack Overflow. TSE. 2022;48(7):2359-75. (other-language precedent)
- [29] Zuo S, et al. How Security Coding Knowledge Impact Software Quality, C# SO security issues. QRS 2025. (other-language precedent)
- Plus the arXiv entry for the Java study itself: arXiv:2511.05813.

Full reference list is on pages 36 to 41 of the PDF if more are needed.

---

## 7. Open issues spotted in the PDF

Two margin notes addressed to "Chaiyong" flag the same problem, on page 8 (Section 3.3) and page 36 (Section 8.5 Data Availability): the replication package DOI is given as **zenodo.17220746** in Section 3 but **zenodo.17220745** in the Data Availability statement. Both need to be corrected to the final DOI. Not our deliverable, but relevant if the technical report links to the same replication package.

---

## 8. Implications for the technical report

1. Our Methodology can be considerably shorter than the paper's, since Phase 1 (tuning) was done once for Java and the tuned configuration is reused. **Confirmed by the authors: Matcha for Python and JavaScript reuses the Java-tuned configuration of Table 3 unchanged (clone size 6 lines, n-gram 1 for r0 and 4 for r1 to r3, QR thresholds 9, 6, 5, 9, similarity thresholds 50%, 60%, 70%, 80%, MRR 0.782).** No language-specific retuning was performed, so Phase 1 is not repeated in the replication. State this in the Methodology and carry it into Threats to Validity, see point 4 below.
2. RQ1 gives us five comparable quantities per language: total accepted answers, percentage with more than one revision, mean and median revisions per answer, maximum revisions, and Levenshtein distance mean, median, max. Build one side-by-side Java / Python / JavaScript table from these.
3. RQ2 gives us three comparable quantities per language: total matched pairs, counts per popularity group, and the Kruskal-Wallis result across groups. The Java applicability rate of 49.30% has no counterpart in our study, so the Discussion must be careful not to compare raw match counts against Java's 391 applicable recommendations, only against the 793 candidate pairs.
4. Threats to Validity should inherit the paper's construct threat (a textual clone match is not proof of reuse direction) and internal threat (Siamese configuration tuned on a 2013 Java corpus), and add three of our own:

   a. **Clone search configuration transferred across languages (internal validity).** Matcha was run on Python and JavaScript with the configuration tuned in Phase 1 of the Java study, which was optimised by Grid Search against a Java ground truth built from the Qualitas corpus, a collection of Java projects dating from 2013. The parameters were therefore never tuned for, or validated against, Python or JavaScript code. Values such as the minimum clone size of 6 lines and the n-gram sizes interact directly with a language's syntax and typical method length: Python is markedly more concise than Java and has no braces, so a 6-line threshold covers a larger unit of behaviour and may filter out valid matches, whereas JavaScript's callback and closure idioms produce shape distributions unlike those of Java methods. Reusing the configuration keeps the replication faithful to the original methodology and makes the three languages directly comparable, which is why it was done, but it may under- or over-report matches for either language, so the per-language match counts should be read as conservative and comparable rather than as optimal for each language. Retuning Matcha per language, following the Phase 1 Grid Search over a language-specific ground truth, is left as future work.

   b. **Popularity thresholds inherited from Java (external validity).** The quartile boundaries for stars, forks and watchers were derived from the Java project population and applied unchanged to the Python and JavaScript project sets, even though star and fork distributions differ across language ecosystems. This keeps the three-way comparison meaningful but means the low, medium and high groups are not necessarily quartiles of the Python or JavaScript populations themselves.

   c. **No manual validation of the matched pairs (construct validity).** Unlike the Java study, we perform no manual classification, so our figures are counts of candidate matches, not confirmed applicable improvements. They are comparable to the Java study's 793 candidate pairs and must not be compared against its 391 manually validated applicable recommendations.
